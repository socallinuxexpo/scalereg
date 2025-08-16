from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render

from . import forms
from . import models

STEPS_TOTAL = 7

ATTENDEE_COOKIE = 'attendee'
PAYMENT_COOKIE = 'payment'


def render_error(request, error_message):
    return render(request, 'reg23/reg_error.html', {
        'title': 'Registration Problem',
        'error_message': error_message,
    })


def check_vars(request, required_post_vars):
    if request.method != 'POST':
        return redirect('/reg23/')

    for var in required_post_vars:
        if var not in request.POST:
            return render_error(request, f'No {var} information.')
    return None


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
        request, 'reg23/index.html', {
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
            request, 'reg23/reg_error.html', {
                'title': 'Registration Problem',
                'error_message': f'Ticket {ticket_name} not found.',
            })

    (promo_name, promo_in_use) = get_promo_in_use(request.POST)
    ticket.apply_promo(promo_in_use)
    items = ticket.get_items()
    for item in items:
        item.apply_promo(promo_in_use)

    return render(
        request, 'reg23/reg_items.html', {
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
        request, 'reg23/reg_attendee.html', {
            'title': 'Register Attendee',
            'ticket': ticket,
            'promo': promo_name,
            'items': items,
            'offset_item': offset_item,
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

    try:
        attendee = models.Attendee.objects.get(id=attendee_id)
    except models.Attendee.DoesNotExist:
        attendee = None

    return render(
        request, 'reg23/reg_finish.html', {
            'title': 'Attendee Registered (Payment still required)',
            'attendee': attendee,
            'step': 4,
            'steps_total': STEPS_TOTAL,
        })
