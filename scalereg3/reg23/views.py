import csv
from enum import Enum

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db import transaction
from django.http import HttpResponse
from django.http import HttpResponseServerError
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from common import utils
from sponsorship import views as sponsorship_views

from . import forms
from . import models

STEPS_TOTAL = 7

ATTENDEE_COOKIE = 'attendee'
PAYMENT_COOKIE = 'payment'


class UpgradeError(Enum):
    do_not_call_in_templates = True
    ATTENDEE_NOT_FOUND = 0
    ATTENDEE_NOT_PAID = 1
    ATTENDEE_NOT_ELIGIBLE = 2


class UpgradeState:

    def __init__(self, attendee, post):
        self._ticket = None
        self._items = []
        self._selected_items = []
        self._changed = False
        self._total = 0
        self._upgrade_cost = 0

        try:
            self._ticket = models.Ticket.objects.get(name=post['ticket'])
        except models.Ticket.DoesNotExist:
            return

        self._ticket.apply_promo(attendee.promo)
        self._items = self._ticket.get_items()
        for item in self._items:
            item.apply_promo(attendee.promo)
        self._selected_items = get_posted_items(post, self._items)
        for item in self._selected_items:
            item.apply_promo(attendee.promo)
        self._changed = attendee.is_badge_type_or_items_different(
            self._ticket, self._selected_items)
        if self._changed:
            self._total = self._ticket.ticket_cost(self._selected_items, None)
            self._upgrade_cost = self._total - attendee.ticket_cost()

    def get_error(self, is_free):
        if not self._ticket:
            return 'Invalid upgrade: Invalid ticket type.'
        if not self._changed:
            return 'Invalid upgrade: Nothing changed.'
        if is_free and self.upgrade_cost > 0:
            return 'Invalid upgrade: Not Free.'
        return None

    @property
    def ticket(self):
        return self._ticket

    @property
    def items(self):
        return self._items

    @property
    def selected_items(self):
        return self._selected_items

    @property
    def changed(self):
        return self._changed

    @property
    def total(self):
        return self._total

    @property
    def upgrade_cost(self):
        return self._upgrade_cost


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


def generate_order_id(existing_ids):
    return utils.generate_unique_id(10, existing_ids)


def generate_payflow_order(post):
    return models.Order(
        order_num=post['USER1'],
        valid=True,
        name=post['NAME'],
        address=post['ADDRESS'],
        city=post['CITY'],
        state=post['STATE'],
        zip_code=post['ZIP'],
        country=post['COUNTRY'],
        email=post['EMAIL'],
        phone=post['PHONE'],
        amount=post['AMOUNT'],
        payment_type='payflow',
        payflow_auth_code=post['AUTHCODE'],
        payflow_pnref=post['PNREF'],
        payflow_resp_msg=post['RESPMSG'],
        payflow_result=post['RESULT'],
    )


def get_attendee_for_id(attendee_id):
    try:
        return models.Attendee.objects.get(id=attendee_id)
    except (models.Attendee.DoesNotExist, ValueError):
        return None


def get_existing_order_ids():
    return [x.order_num for x in models.PendingOrder.objects.all()
            ] + [x.order_num for x in models.Order.objects.all()]


def get_payment_code(code):
    try:
        payment_code = models.PaymentCode.objects.get(code=code.strip())
    except models.PaymentCode.DoesNotExist:
        return None

    return payment_code if payment_code.order.valid else None


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


def should_redirect_post_to_sponsorship(request):
    if request.method != 'POST':
        return False
    return 'USER3' in request.POST and request.POST['USER3'] == 'SPONSORSHIP'


def start_payment_search_for_attendee(id_str, email_str):
    try:
        attendee_id = int(id_str)
    except ValueError:
        return None

    attendee = get_attendee_for_id(attendee_id)
    if not attendee or attendee.email != email_str:
        return None

    return attendee


def get_upgrade_attendee(id_str, email_str):
    attendee = start_payment_search_for_attendee(id_str, email_str)
    if not attendee:
        return UpgradeError.ATTENDEE_NOT_FOUND
    if not attendee.valid:
        return UpgradeError.ATTENDEE_NOT_PAID
    if not attendee.badge_type.upgradable:
        return UpgradeError.ATTENDEE_NOT_ELIGIBLE
    return attendee


def create_upgrade(attendee, new_ticket, new_items):
    with transaction.atomic():
        upgrade = models.Upgrade()
        upgrade.attendee = attendee
        upgrade.old_badge_type = attendee.badge_type
        upgrade.old_order = attendee.order
        upgrade.new_badge_type = new_ticket
        upgrade.save()
        upgrade.old_items.add(*attendee.ordered_items.all())
        upgrade.new_items.add(*new_items)
    return upgrade


def upgrade_attendee(upgrade, new_order):
    upgrade.new_order = new_order
    upgrade.valid = True
    upgrade.save()

    attendee = upgrade.attendee
    attendee.badge_type = upgrade.new_badge_type
    attendee.order = new_order
    attendee.save()
    attendee.ordered_items.clear()
    for item in upgrade.new_items.all():
        attendee.ordered_items.add(item)
    notify_attendee(attendee)


def generate_mass_add_get_response(content):
    response = HttpResponse('<html><body>')
    response.write(content)
    response.write('</body></html>')
    return response


def generate_notify_attendee_body(attendee):
    return f'''Thank you for registering for SCALE.
The details of your registration are included below.

Please note the Express Check-In Code below, which will allow you to
speed up your check-in and badge pickup on-site.

First Name: {attendee.first_name}
Last Name: {attendee.last_name}
Email: {attendee.email}
Zip Code: {attendee.zip_code}

Badge Type: {attendee.badge_type.description}
Express Check-In Code: {attendee.checkin_code()}
'''


def notify_attendee(attendee):
    if not settings.SCALEREG_SEND_MAIL:
        return

    if (not attendee.email or attendee.email.endswith('@example.com')
            or attendee.email.endswith('@none.com')
            or '@' not in attendee.email):
        return

    subject = 'SCALE Registration'
    send_mail(subject,
              generate_notify_attendee_body(attendee),
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
        return render_error(request, f'Ticket {ticket_name} not found.')

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
            'display_url_column': any(item.url for item in items),
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
    total = ticket.ticket_cost(items, None)

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
        csv_data = ','.join([str(x) for x in request.session[PAYMENT_COOKIE]])
        order_tries = 0
        while True:
            order_num = generate_order_id(get_existing_order_ids())
            pending_order = models.PendingOrder(order_num=order_num,
                                                attendees=csv_data)
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
    if should_redirect_post_to_sponsorship(request):
        return sponsorship_views.sale(request)

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

    if maybe_pending_order.upgrade:
        return sale_upgrade(request, maybe_pending_order.upgrade)
    return sale_registration(request, maybe_pending_order)


@csrf_exempt
def sale_registration(request, pending_order):
    maybe_attendee_data = get_pending_order_attendees(pending_order)
    if isinstance(maybe_attendee_data, HttpResponseServerError):
        return maybe_attendee_data

    all_attendees, already_paid_attendees = maybe_attendee_data
    total = sum(attendee.ticket_cost() for attendee in all_attendees)
    total += sum(attendee.ticket_cost() for attendee in already_paid_attendees)
    r = check_payment_amount(request.POST['AMOUNT'], total)
    if r:
        return r

    try:
        order = generate_payflow_order(request.POST)
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
def sale_upgrade(request, upgrade):
    r = check_payment_amount(request.POST['AMOUNT'], upgrade.upgrade_cost())
    if r:
        return r

    attendee = upgrade.attendee
    items = {item.name for item in attendee.ordered_items.all()}
    orig_items = {item.name for item in upgrade.old_items.all()}
    if (upgrade.valid or attendee.badge_type != upgrade.old_badge_type
            or attendee.order != upgrade.old_order or items != orig_items):
        return HttpResponseServerError('bad upgrade')

    try:
        order = generate_payflow_order(request.POST)
        order.save()
    except IntegrityError:
        return HttpResponseServerError('cannot save order')

    upgrade_attendee(upgrade, order)
    return HttpResponse('success')


@csrf_exempt
def failed_payment(request):
    if should_redirect_post_to_sponsorship(request):
        return sponsorship_views.failed_payment(request)

    return render(request, 'reg_failed.html', {
        'title': 'Registration Payment Failed',
    })


@csrf_exempt
def finish_payment(request):
    if should_redirect_post_to_sponsorship(request):
        return sponsorship_views.finish_payment(request)

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


def redeem_payment_code(request):
    required_vars = ['code', 'order']
    r = check_vars(request, required_vars)
    if r:
        return r

    payment_code = get_payment_code(request.POST['code'])
    if not payment_code:
        return render_error(request, 'Payment code is invalid')

    maybe_pending_order = get_pending_order(request.POST['order'])
    if isinstance(maybe_pending_order, HttpResponseServerError):
        return maybe_pending_order

    maybe_attendee_data = get_pending_order_attendees(maybe_pending_order)
    if isinstance(maybe_attendee_data, HttpResponseServerError):
        return maybe_attendee_data

    all_attendees, already_paid_attendees = maybe_attendee_data
    if len(all_attendees) > payment_code.max_attendees:
        return render_error(
            request, 'Payment code invalid for the number of attendees')

    for attendee in all_attendees:
        # Remove non-free addon items.
        for item in attendee.ordered_items.all():
            if item.price > 0:
                attendee.ordered_items.remove(item)
        attendee.badge_type = payment_code.badge_type
        attendee.order = payment_code.order
        attendee.valid = True
        attendee.promo = None
        attendee.save()
        notify_attendee(attendee)

    payment_code.max_attendees = payment_code.max_attendees - len(
        all_attendees)
    payment_code.save()

    return render(
        request, 'reg_receipt.html', {
            'title': 'Registration Payment Code Receipt',
            'attendees': all_attendees,
            'already_paid_attendees': already_paid_attendees,
            'payment_code': payment_code.code,
            'step': 7,
            'steps_total': STEPS_TOTAL,
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


def start_upgrade(request):
    title = 'Registration Upgrade'

    required_vars = [
        'id',
        'email',
    ]
    if check_vars(request, required_vars):
        return render(request, 'reg_start_upgrade.html', {
            'title': title,
        })

    maybe_attendee = get_upgrade_attendee(request.POST['id'],
                                          request.POST['email'])
    if isinstance(maybe_attendee, UpgradeError):
        return render(
            request, 'reg_start_upgrade.html', {
                'title': title,
                'email': request.POST['email'],
                'id': request.POST['id'],
                'upgrade_error': maybe_attendee.value,
                'UpgradeError': UpgradeError,
            })

    attendee = maybe_attendee
    if 'ticket' not in request.POST:
        # Show available tickets.
        avail_tickets = [
            ticket
            for ticket in models.Ticket.public_objects.order_by('description')
            if ticket != attendee.badge_type
        ]
        for ticket in avail_tickets:
            ticket.apply_promo(attendee.promo)
        return render(request, 'reg_start_upgrade.html', {
            'title': title,
            'attendee': attendee,
            'tickets': avail_tickets,
        })

    upgrade_state = UpgradeState(attendee, request.POST)
    if not upgrade_state.ticket:
        return render_error(request,
                            'You have selected an invalid ticket type.')

    if 'has_selected_items' not in request.POST:
        # Show available items if there is a ticket selected.
        return render(
            request, 'reg_start_upgrade.html', {
                'title': title,
                'attendee': attendee,
                'display_url_column': any(item.url
                                          for item in upgrade_state.items),
                'items': upgrade_state.items,
                'selected_ticket': upgrade_state.ticket,
            })

    # Show final upgrade confirmation if items have been selected.
    return render(
        request, 'reg_start_upgrade.html', {
            'title': title,
            'attendee': attendee,
            'changed': upgrade_state.changed,
            'has_selected_items': True,
            'selected_items': upgrade_state.selected_items,
            'selected_ticket': upgrade_state.ticket,
            'total': upgrade_state.total,
            'upgrade_cost': upgrade_state.upgrade_cost,
        })


def free_upgrade(request):
    required_vars = [
        'id',
        'email',
        'ticket',
    ]
    r = check_vars(request, required_vars)
    if r:
        return r

    maybe_attendee = get_upgrade_attendee(request.POST['id'],
                                          request.POST['email'])
    if isinstance(maybe_attendee, UpgradeError):
        return render_error(request, 'Bad upgrade.')

    attendee = maybe_attendee
    upgrade_state = UpgradeState(attendee, request.POST)
    upgrade_error = upgrade_state.get_error(True)
    if upgrade_error:
        return render_error(request, upgrade_error)

    try:
        upgrade = create_upgrade(attendee, upgrade_state.ticket,
                                 upgrade_state.selected_items)
    except IntegrityError:
        return render_error(request, 'Cannot save upgrade.')

    order_tries = 0
    while True:
        order_num = generate_order_id(get_existing_order_ids())
        order = models.Order(
            order_num=order_num,
            valid=True,
            name='Free Upgrade',
            address='N/A',
            city='N/A',
            state='N/A',
            zip_code='N/A',
            email=attendee.email,
            amount=0,
            payment_type='freeup',
        )
        try:
            order.save()
            break
        except IntegrityError:
            order_tries += 1
            if order_tries > 10:
                return render_error(request, 'Cannot generate order ID.')

    upgrade_attendee(upgrade, order)
    return render(
        request, 'reg_receipt_upgrade.html', {
            'title': 'Registration Payment Receipt',
            'name': attendee.full_name(),
            'email': attendee.email,
            'order': order,
            'total': 0,
            'upgrade': upgrade,
        })


def non_free_upgrade(request):
    required_vars = [
        'email',
        'id',
        'ticket',
    ]
    r = check_vars(request, required_vars)
    if r:
        return r

    maybe_attendee = get_upgrade_attendee(request.POST['id'],
                                          request.POST['email'])
    if isinstance(maybe_attendee, UpgradeError):
        return render_error(request, 'Bad upgrade.')

    attendee = maybe_attendee
    upgrade_state = UpgradeState(attendee, request.POST)
    upgrade_error = upgrade_state.get_error(False)
    if upgrade_error:
        return render_error(request, upgrade_error)

    try:
        upgrade = create_upgrade(attendee, upgrade_state.ticket,
                                 upgrade_state.selected_items)
    except IntegrityError:
        return render_error(request, 'Cannot save upgrade.')

    order_tries = 0
    while True:
        order_num = generate_order_id(get_existing_order_ids())
        pending_order = models.PendingOrder(order_num=order_num,
                                            upgrade=upgrade)
        try:
            pending_order.save()
            break
        except IntegrityError:
            order_tries += 1
            if order_tries > 10:
                return render_error(request, 'Cannot generate order ID.')

    return render(
        request, 'reg_non_free_upgrade.html', {
            'title': 'Registration Upgrade',
            'attendee': attendee,
            'order': order_num,
            'payflow_url': settings.SCALEREG_PAYFLOW_URL,
            'payflow_partner': settings.SCALEREG_PAYFLOW_PARTNER,
            'payflow_login': settings.SCALEREG_PAYFLOW_LOGIN,
            'upgrade': upgrade,
        })


@staff_member_required
def mass_add_attendees(request):
    csrf_token_value = get_token(request)
    input_form_html = f'''<form method="post">
<p>first_name,last_name,title,org,email,zip,phone,order_number,ticket_code</p>
<textarea name="data" rows="25" cols="80"></textarea><br />
<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token_value}">
<input type="submit" />
</form>'''

    if request.method == 'GET':
        return generate_mass_add_get_response(input_form_html)

    required_vars = ['data']
    r = check_vars(request, required_vars)
    if r:
        return r

    response = HttpResponse('<html><body>')
    attendees_added_count = 0
    csv_reader = csv.reader(request.POST['data'].split('\n'))
    for entry in csv_reader:
        if not entry:
            continue

        if len(entry) != 9:
            response.write(f'Bad data: {entry}<br />\n')
            continue

        try:
            order = models.Order.objects.get(order_num=entry[7].strip())
        except models.Order.DoesNotExist:
            response.write(f'Bad order number: {entry[7]}<br />\n')
            continue

        try:
            ticket = models.Ticket.objects.get(name=entry[8].strip())
        except models.Ticket.DoesNotExist:
            response.write(f'Bad ticket type: {entry[8]}<br />\n')
            continue

        entry_dict = {
            'first_name': entry[0].strip(),
            'last_name': entry[1].strip(),
            'title': entry[2].strip(),
            'org': entry[3].strip(),
            'email': entry[4].strip(),
            'zip_code': entry[5].strip(),
            'phone': entry[6].strip(),
            'badge_type': ticket,
        }
        form = forms.MassAddAttendeesForm(entry_dict)
        if not form.is_valid():
            response.write(
                f'Bad entry: {entry}, reason: {form.errors}<br />\n')
            continue

        attendee = form.save(commit=False)
        attendee.valid = True
        attendee.checked_in = False
        attendee.can_email = models.Attendee.EmailChoices.LOGISTICS_ONLY
        attendee.order = order
        attendee.badge_type = ticket
        attendee.save()
        form.save_m2m()
        notify_attendee(attendee)
        response.write(f'Added: {entry} as {attendee.id}<br />\n')
        attendees_added_count += 1

    response.write(f'Total added attendees: {attendees_added_count}\n')
    response.write(input_form_html)
    response.write('</body></html>')
    return response


@staff_member_required
def mass_add_payment_codes(request):
    csrf_token_value = get_token(request)
    input_form_html = f'''<form method="post">
<p>name,addr,city,state,zip,email,phone,type,max_att</p>
<textarea name="data" rows="25" cols="80"></textarea><br />
<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token_value}">
<input type="submit" />
</form>'''

    if request.method == 'GET':
        return generate_mass_add_get_response(input_form_html)

    required_vars = ['data']
    r = check_vars(request, required_vars)
    if r:
        return r

    response = HttpResponse('<html><body>')
    payment_codes_added_count = 0
    csv_reader = csv.reader(request.POST['data'].split('\n'))
    for entry in csv_reader:
        if not entry:
            continue

        if len(entry) != 9:
            response.write(f'Bad data: {entry}<br />\n')
            continue

        try:
            ticket = models.Ticket.objects.get(name=entry[7].strip())
        except models.Ticket.DoesNotExist:
            response.write(f'Bad ticket type: {entry[7]}<br />\n')
            continue

        order_num = generate_order_id(get_existing_order_ids())
        entry_dict = {
            'order_num': order_num,
            'name': entry[0].strip(),
            'address': entry[1].strip(),
            'city': entry[2].strip(),
            'state': entry[3].strip(),
            'zip_code': entry[4].strip(),
            'email': entry[5].strip(),
            'phone': entry[6].strip(),
            'payment_type': models.TICKET_TO_PAYMENT_MAP[ticket.ticket_type],
        }
        form = forms.MassAddOrderForm(entry_dict)
        if not form.is_valid():
            response.write(
                f'Bad entry: {entry}, reason: {form.errors}<br />\n')
            continue

        order = form.save(commit=False)
        order.amount = 0

        try:
            order.save()
        except IntegrityError:
            response.write(f'Error while saving order for: {entry[0]}\n')
            break

        form.save_m2m()

        payment_code = models.PaymentCode(
            code=order.order_num,
            badge_type=ticket,
            order=order,
            max_attendees=entry[8].strip(),
        )
        try:
            payment_code.save()
        except IntegrityError:
            order.delete()
            response.write(
                f'Error while saving payment code for: {entry[0]}\n')
            break

        order.valid = True
        order.save()
        response.write(f'Added: {entry} as {payment_code.code}<br />\n')
        payment_codes_added_count += 1

    response.write(f'Total added payment codes: {payment_codes_added_count}\n')
    response.write(input_form_html)
    response.write('</body></html>')
    return response


@staff_member_required
def mass_add_promos(request):
    csrf_token_value = get_token(request)
    input_form_html = f'''<form method="post">
<p>code,modifier,description</p>
<textarea name="data" rows="25" cols="80"></textarea><br />
<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token_value}">
<input type="submit" />
</form>'''

    if request.method == 'GET':
        return generate_mass_add_get_response(input_form_html)

    required_vars = ['data']
    r = check_vars(request, required_vars)
    if r:
        return r

    # Apply only to full tickets by default
    full_tickets = models.Ticket.public_objects.filter(ticket_type='full')

    response = HttpResponse('<html><body>')
    promos_added_count = 0
    csv_reader = csv.reader(request.POST['data'].split('\n'))
    for entry in csv_reader:
        if not entry:
            continue

        if len(entry) != 3:
            response.write(f'Bad data: {entry}<br />\n')
            continue

        try:
            price_modifier = float(entry[1].strip())
        except ValueError:
            response.write(f'Bad price modifier: {entry[1]}<br />\n')
            continue

        entry_dict = {
            'name': entry[0].strip(),
            'description': entry[2].strip(),
            'price_modifier': price_modifier,
        }
        form = forms.MassAddPromoForm(entry_dict)
        if not form.is_valid():
            response.write(
                f'Bad entry: {entry}, reason: {form.errors}<br />\n')
            continue

        promo = form.save(commit=False)
        promo.active = True
        promo.save()
        form.save_m2m()
        for ticket in full_tickets:
            promo.applies_to.add(ticket)
        response.write(f'Added: {entry}<br />\n')
        promos_added_count += 1

    response.write(f'Total added promos: {promos_added_count}\n')
    response.write(input_form_html)
    response.write('</body></html>')
    return response
