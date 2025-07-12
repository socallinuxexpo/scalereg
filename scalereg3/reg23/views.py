from django.shortcuts import redirect
from django.shortcuts import render

from . import models

STEPS_TOTAL = 7


def index_redirect(request):
    return redirect('/reg23/')


def index(request):
    avail_tickets = models.Ticket.objects.filter(
        public=True).order_by('description')

    request.session.set_test_cookie()

    return render(
        request, 'reg23/index.html', {
            'title': 'Registration',
            'tickets': avail_tickets,
            'step': 1,
            'steps_total': STEPS_TOTAL,
        })
