# Create your views here.

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
import models

STEPS_TOTAL = 5

def ApplyPromoToTickets(promo, tickets):
  if not promo:
    return None
  promo_name = promo.name
  promo_applies_to = promo.applies_to.all()
  for t in tickets:
    if t in promo_applies_to:
      t.price *= promo.price_modifier
  return promo.name


def ApplyPromoToItems(promo, items):
  if not promo:
    return None
  promo_name = promo.name
  for item in items:
    if item.promo:
      item.price *= promo.price_modifier
  return promo.name


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

  promo_name = ApplyPromoToTickets(promo_in_use, avail_tickets)

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
  if '/reg6/' not in request.META['HTTP_REFERER']:
    return HttpResponseRedirect('/reg6/')

  required_vars = ['ticket', 'promo']
  for var in required_vars:
    if var not in request.POST:
      return render_to_response('reg6/reg_error.html',
        {'title': 'Registration Problem',
         'error_message': 'No %s information.' % var,
        })

  ticket = models.Ticket.public_objects.filter(name=request.POST['ticket'])
  active_promocode_set = models.PromoCode.active_objects
  avail_promocodes = active_promocode_set.names()
  
  promo_in_use = None
  if request.POST['promo'] in avail_promocodes:
    promo_in_use = active_promocode_set.get(name=request.POST['promo'])

  promo_name = ApplyPromoToTickets(promo_in_use, ticket)
  items = ticket[0].item_set.all().order_by('description')
  ApplyPromoToItems(promo_in_use, items)

  return render_to_response('reg6/reg_items.html',
    {'title': 'Add Items',
     'ticket': ticket[0],
     'promo': promo_name,
     'items': items,
     'step': 2,
     'steps_total': STEPS_TOTAL,
    })


def AddAttendee(request):
  return render_to_response('reg6/index.html',
    {'title': 'Blar'})
