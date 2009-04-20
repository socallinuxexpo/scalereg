# Create your views here.

from django.shortcuts import render_to_response
import models

def index(request):
  available_tickets = []
  available_promocodes = {}
  promo = False

  tickets = models.Ticket.objects.filter(public=True).order_by('description')
  for t in tickets:
    if t.is_public():
      available_tickets.append(t)
  promocodes = models.PromoCode.objects.filter(active=True)
  for p in promocodes:
    if p.is_active():
      available_promocodes[p.name] = p

  if 'promo' in request.GET and request.GET['promo'] in available_promocodes:
    promo_in_use = available_promocodes[request.GET['promo']]
    promo = promo_in_use.name
    promo_applies_to = promo_in_use.applies_to.all()
    for t in available_tickets:
      if t in promo_applies_to:
        t.price *= promo_in_use.price_modifier

  return render_to_response('reg6/index.html',
    {'title': 'Registration', 'tickets': available_tickets,
     'promo': promo})

def AddItems(request):
  return render_to_response('reg6/index.html',
    {'title': 'Blar'})

def AddAttendee(request):
  return render_to_response('reg6/index.html',
    {'title': 'Blar'})
