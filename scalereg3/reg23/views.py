from django.shortcuts import redirect
from django.shortcuts import render

from . import models

STEPS_TOTAL = 7


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
