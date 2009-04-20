# Create your views here.

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
import models

STEPS_TOTAL = 5

def index(request):
  avail_tickets = models.Ticket.public_objects.order_by('description')
  active_promocode_set = models.PromoCode.active_objects
  avail_promocodes = active_promocode_set.names()

  promo_in_use = None
  if request.method == 'GET':
    if 'promo' in request.GET and request.GET['promo'] in avail_promocodes:
      promo_in_use = active_promocode_set.get(name=request.GET['promo'])
  elif request.method == 'POST':
    if 'promo' in request.POST and request.POST['promo'] in avail_promocodes:
      promo_in_use = active_promocode_set.get(name=request.POST['promo'])

  if promo_in_use:
    promo_name = promo_in_use.name
    promo_applies_to = promo_in_use.applies_to.all()
    for t in avail_tickets:
      if t in promo_applies_to:
        t.price *= promo_in_use.price_modifier
  else:
    promo_name = None

  return render_to_response('reg6/reg_index.html',
    {'title': 'Registration',
     'tickets': avail_tickets,
     'promo': promo_name,
     'step': 1,
     'steps_total': STEPS_TOTAL,
    })


def AddItems(request):
  if request.method != 'POST':
    return HttpResponseRedirect('/reg6/')

  required_vars = ['ticket', 'promo']
  for var in required_vars:
    if var not in request.POST:
      return render_to_response('reg6/reg_error.html',
        {'title': 'Registration Problem',
         'error_message': 'No %s information.' % var,
        })

  return render_to_response('reg6/reg_items.html',
    {'title': 'Add Items',
     'step': 2,
     'steps_total': STEPS_TOTAL,
    })


def AddAttendee(request):
  return render_to_response('reg6/index.html',
    {'title': 'Blar'})
