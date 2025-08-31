from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import HttpResponse
from django.http import HttpResponseServerError
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from common import utils

from . import forms
from . import models

STEPS_TOTAL = 7

ATTENDEE_COOKIE = 'attendee'
PAYMENT_COOKIE = 'payment'


def render_error(request, error_message):
    return render(request, 'reg_error.html', {
        'title': 'Registration Problem',
        'error_message': error_message,
    })


def check_payment_amount(amount_str, expected_cost):
    actual = int(float(amount_str))
    expected = int(float(expected_cost))
    if actual == 0:
        return HttpResponseServerError(
            f'incorrect payment amount: got {actual}')
    if expected == 0:
        return HttpResponseServerError(
            'incorrect payment amount: should not expect 0')
    if actual == expected:
        return None
    return HttpResponseServerError(
        f'incorrect payment amount: expected {expected}, got {actual}')


def check_sales_request(request, required_vars):
    if request.method != 'POST':
        return HttpResponse(f'Method not allowed: {request.method}',
                            status=405)

    for var in required_vars:
        if var not in request.POST:
            return HttpResponseServerError('required vars missing')
    if request.POST['RESULT'] != '0':
        return HttpResponseServerError('transaction did not succeed')
    if request.POST['RESPMSG'] != 'Approved':
        return HttpResponseServerError('transaction declined')
    return None


def check_vars(request, required_post_vars):
    if request.method != 'POST':
        return redirect('/reg23/')

    for var in required_post_vars:
        if var not in request.POST:
            return render_error(request, f'No {var} information.')
    return None


def get_attendee_for_id(attendee_id):
    try:
        return models.Attendee.objects.get(id=attendee_id)
    except (models.Attendee.DoesNotExist, ValueError):
        return None


def generate_order_id(existing_ids):
    return utils.generate_unique_id(10, existing_ids)


def get_pending_order_attendees(pending_order):
    all_attendees = []
    already_paid_attendees = []
    for attendee_id in pending_order.attendees_list():
        attendee = get_attendee_for_id(attendee_id)
        if not attendee:
            return HttpResponseServerError('cannot find an attendee')

        if attendee.valid:
            already_paid_attendees.append(attendee)
        else:
            all_attendees.append(attendee)
    return (all_attendees, already_paid_attendees)


def get_pending_order(order_num):
    if models.Order.objects.filter(order_num=order_num):
        return HttpResponseServerError('order already exists')

    try:
        return models.PendingOrder.objects.get(order_num=order_num)
    except models.PendingOrder.DoesNotExist:
        return HttpResponseServerError('cannot get pending order')


def get_posted_items(post, avail_items):
    selected_items = set()
    for i in range(len(avail_items)):
        key = f'item{i}'
        if key in post:
            try:
                item = models.Item.objects.get(name=post[key])
            except models.Item.DoesNotExist:
                continue

            if item in avail_items:
                selected_items.add(item)
    return selected_items


def get_promo_from_request(request_data, avail_promocodes):
    if 'promo' not in request_data:
        return None
    promo = request_data['promo'].upper()
    return promo if promo in avail_promocodes else None


def get_promo_in_use(request_data):
    active_promo_set = models.PromoCode.active_objects
    promo_name = get_promo_from_request(request_data, active_promo_set.names())
    if not promo_name:
        return (None, None)
    return (promo_name, active_promo_set.get(name=promo_name))


def get_relevant_questions(ticket, items):
    results = []
    for question in models.Question.objects.filter(active=True):
        if question.is_applicable_to_ticket(ticket) or any(
                question.is_applicable_to_item(item) for item in items):
            results.append(question)
    return results


def get_unpaid_attendees_from_payment_cookie(cookie_data):
    unpaid_attendees = []
    for attendee_id in cookie_data:
        attendee = get_attendee_for_id(attendee_id)
        if not attendee:
            continue
        if attendee.valid:
            continue  # Ignore paid attendees
        unpaid_attendees.append(attendee)
    return unpaid_attendees


def start_payment_search_for_attendee(id_str, email_str):
    try:
        attendee_id = int(id_str)
    except ValueError:
        return None

    attendee = get_attendee_for_id(attendee_id)
    if not attendee or attendee.email != email_str:
        return None

    return attendee


def notify_attendee(attendee):
    if not settings.SCALEREG_SEND_MAIL:
        return

    if (not attendee.email or attendee.email.endswith('@example.com')
            or attendee.email.endswith('@none.com')
            or '@' not in attendee.email):
        return

    subject = 'SCALE Registration'
    body = f'''Thank you for registering for SCALE.
The details of your registration are included below.

First Name: {attendee.first_name}
Last Name: {attendee.last_name}
Email: {attendee.email}
Zip Code: {attendee.zip_code}

Badge Type: {attendee.badge_type.description}
'''

    send_mail(subject,
              body,
              settings.SCALEREG_EMAIL, [attendee.email],
              fail_silently=True)


def validate_save_attendee(request, ticket, items, promo_in_use):
    if ATTENDEE_COOKIE in request.session and request.session[ATTENDEE_COOKIE]:
        return render_error(request, 'Already added attendee.')

    form = forms.AttendeeForm(request.POST)
    if not form.is_valid():
        return form

    if not request.session.test_cookie_worked():
        return render_error(
            request,
            ('Please do not register multiple attendees at the same time. ',
             'Please make sure you have cookies enabled.'))

    # create attendee
    new_attendee = form.save(commit=False)
    new_attendee.badge_type = ticket
    new_attendee.promo = promo_in_use

    # save attendee
    new_attendee.save()
    form.save_m2m()

    # add ordered items
    for item in items:
        new_attendee.ordered_items.add(item)

    # add survey answers
    for question in get_relevant_questions(ticket, items):
        key = f'question{question.id}'
        value = request.POST.get(key, None)
        if not value:
            continue
        if question.is_text_question:
            answer = models.Answer()
            answer.question = question
            answer.text = value[:question.max_length]
            answer.save()
            new_attendee.answers.add(answer)
        else:
            try:
                new_attendee.answers.add(models.Answer.objects.get(id=value))
            except (models.Answer.DoesNotExist, ValueError):
                pass

    request.session[ATTENDEE_COOKIE] = new_attendee.id

    # add attendee to order
    request.session.setdefault(PAYMENT_COOKIE, [])
    request.session[PAYMENT_COOKIE].append(new_attendee.id)

    return redirect('/reg23/registered_attendee/')


def index_redirect(request):
    return redirect('/reg23/')


def index(request):
    avail_tickets = models.Ticket.public_objects.order_by('description')

    request_data = {}
    if request.method == 'GET':
        request_data = request.GET
    elif request.method == 'POST':
        request_data = request.POST
    (promo_name, promo_in_use) = get_promo_in_use(request_data)
    for ticket in avail_tickets:
        ticket.apply_promo(promo_in_use)

    request.session.set_test_cookie()

    return render(
        request, 'reg_index.html', {
            'title': 'Registration',
            'tickets': avail_tickets,
            'promo': promo_name,
            'step': 1,
            'steps_total': STEPS_TOTAL,
        })


def add_items(request):
    required_vars = ['ticket', 'promo']
    r = check_vars(request, required_vars)
    if r:
        return r

    ticket_name = request.POST['ticket']
    try:
        ticket = models.Ticket.public_objects.get(name=ticket_name)
    except models.Ticket.DoesNotExist:
        return render(
            request, 'reg_error.html', {
                'title': 'Registration Problem',
                'error_message': f'Ticket {ticket_name} not found.',
            })

    (promo_name, promo_in_use) = get_promo_in_use(request.POST)
    ticket.apply_promo(promo_in_use)
    items = ticket.get_items()
    for item in items:
        item.apply_promo(promo_in_use)

    return render(
        request, 'reg_items.html', {
            'title': 'Registration - Add Items',
            'ticket': ticket,
            'items': items,
            'promo': promo_name,
            'step': 2,
            'steps_total': STEPS_TOTAL,
        })


def add_attendee(request):
    required_vars = ['ticket', 'promo']
    r = check_vars(request, required_vars)
    if r:
        return r

    action = None
    if 'HTTP_REFERER' in request.META:
        if '/reg23/add_items/' in request.META['HTTP_REFERER']:
            action = 'add_new'
        elif '/reg23/add_attendee/' in request.META['HTTP_REFERER']:
            action = 'validate'
    if not action:
        return render_error(request, 'Invalid referrer.')

    ticket_name = request.POST['ticket']
    try:
        ticket = models.Ticket.public_objects.get(name=ticket_name)
    except models.Ticket.DoesNotExist:
        return render_error(request, f'Ticket {ticket_name} not found.')

    (promo_name, promo_in_use) = get_promo_in_use(request.POST)
    ticket.apply_promo(promo_in_use)
    items = get_posted_items(request.POST, ticket.get_items())
    for item in items:
        item.apply_promo(promo_in_use)

    offset_items = [item for item in items if item.ticket_offset]
    offset_item = offset_items[0] if offset_items else None
    total = ticket.ticket_cost(items)

    if action == 'add_new':
        request.session[ATTENDEE_COOKIE] = ''
        form = forms.AttendeeForm()
    else:
        assert action == 'validate'
        result = validate_save_attendee(request, ticket, items, promo_in_use)
        if isinstance(result, HttpResponse):
            return result

        assert isinstance(result, forms.AttendeeForm)
        form = result

    return render(
        request, 'reg_attendee.html', {
            'title': 'Register Attendee',
            'ticket': ticket,
            'promo': promo_name,
            'items': items,
            'offset_item': offset_item,
            'questions': get_relevant_questions(ticket, items),
            'total': total,
            'form': form,
            'step': 3,
            'steps_total': STEPS_TOTAL,
        })


def registered_attendee(request):
    if request.method != 'GET':
        return redirect('/reg23/')

    attendee_id = request.session.get(ATTENDEE_COOKIE, None)
    if not isinstance(attendee_id, int):
        return redirect('/reg23/')

    attendee = get_attendee_for_id(attendee_id)
    return render(
        request, 'reg_finish.html', {
            'title': 'Attendee Registered (Payment still required)',
            'attendee': attendee,
            'step': 4,
            'steps_total': STEPS_TOTAL,
        })


def start_payment(request):
    if PAYMENT_COOKIE not in request.session:
        request.session[PAYMENT_COOKIE] = []

    try:
        unpaid_attendees = get_unpaid_attendees_from_payment_cookie(
            request.session[PAYMENT_COOKIE])
    except TypeError:
        return redirect('/reg23/')

    new_attendee = None
    bad_attendee_id_email = None
    paid_attendee = None
    removed_attendee = None

    if request.method == 'POST':
        if 'remove' in request.POST:
            removed_attendee = get_attendee_for_id(request.POST['remove'])
            if removed_attendee in unpaid_attendees:
                unpaid_attendees.remove(removed_attendee)
            else:
                removed_attendee = None
        elif 'id' in request.POST and 'email' in request.POST:
            id_str = request.POST['id']
            email_str = request.POST['email'].strip()
            searched_attendee = start_payment_search_for_attendee(
                id_str, email_str)
            if not searched_attendee:
                bad_attendee_id_email = [id_str, email_str]
            elif searched_attendee.valid:
                paid_attendee = searched_attendee
            elif searched_attendee not in unpaid_attendees:
                new_attendee = searched_attendee
                unpaid_attendees.append(searched_attendee)

    request.session[PAYMENT_COOKIE] = [
        attendee.id for attendee in unpaid_attendees
    ]

    total = sum(attendee.ticket_cost() for attendee in unpaid_attendees)

    return render(
        request, 'reg_start_payment.html', {
            'title': 'Place Your Order',
            'bad_attendee_id_email': bad_attendee_id_email,
            'new_attendee': new_attendee,
            'paid_attendee': paid_attendee,
            'removed_attendee': removed_attendee,
            'attendees': unpaid_attendees,
            'step': 5,
            'steps_total': STEPS_TOTAL,
            'total': total,
        })


def payment(request):
    if request.method != 'POST':
        return redirect('/reg23/')

    if PAYMENT_COOKIE not in request.session:
        return redirect('/reg23/')

    try:
        unpaid_attendees = get_unpaid_attendees_from_payment_cookie(
            request.session[PAYMENT_COOKIE])
    except TypeError:
        return redirect('/reg23/')

    request.session[PAYMENT_COOKIE] = [
        attendee.id for attendee in unpaid_attendees
    ]

    order_num = None
    if unpaid_attendees:
        csv = ','.join([str(x) for x in request.session[PAYMENT_COOKIE]])
        order_tries = 0
        while True:
            existing_order_ids = [
                x.order_num for x in models.PendingOrder.objects.all()
            ]
            existing_order_ids += [
                x.order_num for x in models.Order.objects.all()
            ]
            order_num = generate_order_id(existing_order_ids)
            pending_order = models.PendingOrder(order_num=order_num,
                                                attendees=csv)
            try:
                pending_order.save()
                break
            except IntegrityError:
                order_tries += 1
                if order_tries > 10:
                    return render_error(request, 'cannot generate order ID')

    total = sum(attendee.ticket_cost() for attendee in unpaid_attendees)

    return render(
        request, 'reg_payment.html', {
            'title': 'Registration Payment',
            'attendees': unpaid_attendees,
            'order': order_num,
            'payflow_url': settings.SCALEREG_PAYFLOW_URL,
            'payflow_partner': settings.SCALEREG_PAYFLOW_PARTNER,
            'payflow_login': settings.SCALEREG_PAYFLOW_LOGIN,
            'step': 6,
            'steps_total': STEPS_TOTAL,
            'total': total,
        })


@csrf_exempt
def sale(request):
    required_vars = (
        'NAME',
        'ADDRESS',
        'CITY',
        'STATE',
        'ZIP',
        'COUNTRY',
        'PHONE',
        'EMAIL',
        'AMOUNT',
        'AUTHCODE',
        'PNREF',
        'RESULT',
        'RESPMSG',
        'USER1',
    )
    r = check_sales_request(request, required_vars)
    if r:
        return r

    maybe_pending_order = get_pending_order(request.POST['USER1'])
    if isinstance(maybe_pending_order, HttpResponseServerError):
        return maybe_pending_order

    maybe_attendee_data = get_pending_order_attendees(maybe_pending_order)
    if isinstance(maybe_attendee_data, HttpResponseServerError):
        return maybe_attendee_data

    all_attendees, already_paid_attendees = maybe_attendee_data
    total = sum(attendee.ticket_cost() for attendee in all_attendees)
    total += sum(attendee.ticket_cost() for attendee in already_paid_attendees)
    r = check_payment_amount(request.POST['AMOUNT'], total)
    if r:
        return r

    try:
        order = models.Order(
            order_num=request.POST['USER1'],
            valid=True,
            name=request.POST['NAME'],
            address=request.POST['ADDRESS'],
            city=request.POST['CITY'],
            state=request.POST['STATE'],
            zip_code=request.POST['ZIP'],
            country=request.POST['COUNTRY'],
            email=request.POST['EMAIL'],
            phone=request.POST['PHONE'],
            amount=request.POST['AMOUNT'],
            payment_type='payflow',
            payflow_auth_code=request.POST['AUTHCODE'],
            payflow_pnref=request.POST['PNREF'],
            payflow_resp_msg=request.POST['RESPMSG'],
            payflow_result=request.POST['RESULT'],
        )
        order.save()
        for attendee in already_paid_attendees:
            order.already_paid_attendees.add(attendee)
    except IntegrityError:
        return HttpResponseServerError('cannot save order')

    for attendee in all_attendees:
        attendee.valid = True
        attendee.order = order
        attendee.save()
        notify_attendee(attendee)

    return HttpResponse('success')


@csrf_exempt
def failed_payment(request):
    return render(request, 'reg_failed.html', {
        'title': 'Registration Payment Failed',
    })


@csrf_exempt
def finish_payment(request):
    required_vars = (
        'NAME',
        'EMAIL',
        'AMOUNT',
        'USER1',
    )
    r = check_vars(request, required_vars)
    if r:
        return r

    try:
        order = models.Order.objects.get(order_num=request.POST['USER1'])
    except models.Order.DoesNotExist:
        return render_error(request, 'Your registration order cannot be found')

    all_attendees = models.Attendee.objects.filter(order=order.order_num)
    already_paid_attendees = order.already_paid_attendees

    return render(
        request, 'reg_receipt.html', {
            'title': 'Registration Payment Receipt',
            'name': request.POST['NAME'],
            'email': request.POST['EMAIL'],
            'attendees': all_attendees,
            'already_paid_attendees': already_paid_attendees.all(),
            'order': request.POST['USER1'],
            'step': 7,
            'steps_total': STEPS_TOTAL,
            'total': request.POST['AMOUNT'],
        })


def reg_lookup(request):
    if request.method != 'POST':
        return render(request, 'reg_lookup.html', {
            'title': 'Registration Lookup',
            'form': forms.AttendeeLookupForm()
        })

    attendees = []
    form = forms.AttendeeLookupForm(request.POST)
    if form.is_valid():
        attendees = models.Attendee.objects.filter(
            email=form.cleaned_data['email'],
            zip_code=form.cleaned_data['zip_code'])

    return render(
        request, 'reg_lookup.html', {
            'title': 'Registration Lookup',
            'attendees': attendees,
            'form': form,
            'search': 1,
        })
