# Create your views here.

from django.shortcuts import render_to_response
import models

def index(request):
  avail_tickets = []
  avail_promocodes = {}

  tickets = models.Ticket.objects.filter(public=True).order_by('description')
  for t in tickets:
    if t.is_public():
      avail_tickets.append(t)
  promocodes = models.PromoCode.objects.filter(active=True)
  for p in promocodes:
    if p.is_active():
      avail_promocodes[p.name] = p

  promo_in_use = None
  if request.method == 'GET':
    if 'promo' in request.GET and request.GET['promo'] in avail_promocodes:
      promo_in_use = avail_promocodes[request.GET['promo']]
  elif request.method == 'POST':
    if 'promo' in request.POST and request.POST['promo'] in avail_promocodes:
      promo_in_use = avail_promocodes[request.POST['promo']]

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
    })


def AddItems(request):
  return render_to_response('reg6/reg_items.html',
    {'title': 'Blar',
    })


def AddAttendee(request):
  return render_to_response('reg6/index.html',
    {'title': 'Blar'})
