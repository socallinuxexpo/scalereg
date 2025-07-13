from django.shortcuts import redirect
from django.shortcuts import render

from . import models

STEPS_TOTAL = 7


def check_vars(request, post):
    if request.method != 'POST':
        return redirect('/reg23/')

    for var in post:
        if var not in request.POST:
            return render(
                request, 'reg23/reg_error.html', {
                    'title': 'Registration Problem',
                    'error_message': f'No {var} information.',
                })
    return None


def index_redirect(request):
    return redirect('/reg23/')


def index(request):
    avail_tickets = models.Ticket.public_objects.order_by('description')

    request.session.set_test_cookie()

    return render(
        request, 'reg23/index.html', {
            'title': 'Registration',
            'tickets': avail_tickets,
            'step': 1,
            'steps_total': STEPS_TOTAL,
        })


def add_items(request):
    required_vars = ['ticket']
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

    return render(
        request, 'reg23/reg_items.html', {
            'title': 'Registration - Add Items',
            'ticket': ticket,
            'items': ticket.get_items(),
            'step': 2,
            'steps_total': STEPS_TOTAL,
        })
