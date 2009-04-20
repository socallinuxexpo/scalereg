# Create your views here.

from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
import models

STEPS_TOTAL = 5

def ApplyPromoToTickets(promo, tickets):
  if not promo:
    return None
  promo_applies_to = promo.applies_to.all()
  for t in tickets:
    if t in promo_applies_to:
      t.price *= promo.price_modifier
  return promo.name


def ApplyPromoToItems(promo, items):
  if not promo:
    return None
  for item in items:
    if item.promo:
      item.price *= promo.price_modifier
  return promo.name


def CheckVars(request, post, cookies):
  for var in post:
    if var not in request.POST:
      return render_to_response('reg6/reg_error.html',
        {'title': 'Registration Problem',
         'error_message': 'No %s information.' % var,
        })
  for var in cookies:
    if var not in request.session:
      return render_to_response('reg6/reg_error.html',
        {'title': 'Registration Problem',
         'error_message': 'No %s information.' % var,
        })
  return None


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

  required_vars = ['promo', 'ticket']
  r = CheckVars(request, required_vars, [])
  if r:
    return r

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
  if request.method != 'POST':
    return HttpResponseRedirect('/reg6/')

  action = None
  if '/reg6/add_items/' in request.META['HTTP_REFERER']:
    action = 'add'
  elif '/reg6/add_attendee/' in request.META['HTTP_REFERER']:
    action = 'check'

  if not action:
    return HttpResponseRedirect('/reg6/')

  required_vars = ['ticket', 'promo']
  r = CheckVars(request, required_vars, [])
  if r:
    return r

  ticket = models.Ticket.public_objects.filter(name=request.POST['ticket'])
  active_promocode_set = models.PromoCode.active_objects
  avail_promocodes = active_promocode_set.names()
  
  promo_in_use = None
  if request.POST['promo'] in avail_promocodes:
    promo_in_use = active_promocode_set.get(name=request.POST['promo'])

  promo_name = ApplyPromoToTickets(promo_in_use, ticket)
  avail_items = ticket[0].item_set.all().order_by('description')

  selected_items = []
  for i in xrange(len(avail_items)):
    item_number = 'item%d' % i
    if item_number in request.POST:
      item = models.Item.objects.get(name=request.POST[item_number])
      if item in avail_items:
        selected_items.append(item)
  ApplyPromoToItems(promo_in_use, selected_items)

  total = ticket[0].price
  for item in selected_items:
    total += item.price

  manipulator = models.Attendee.AddManipulator()

  if action == 'add':
    errors = new_data = {}
  else:
    new_data = request.POST.copy()

    # add badge type
    new_data['badge_type'] = new_data['ticket']
    # add ordered items
    for s in selected_items:
      new_data.appendlist('ordered_items', str(s.id))
    # add promo
    if new_data['promo'] == 'None':
      new_data['promo'] = ''
    # add other fields
    new_data['obtained_items'] = new_data['survey_answers'] = ''

    errors = manipulator.get_validation_errors(new_data)
    if not errors:
      manipulator.do_html2python(new_data)
      new_place = manipulator.save(new_data)
      return HttpResponseRedirect('/reg6/finish_registration/')

  form = forms.FormWrapper(manipulator, new_data, errors)
  return render_to_response('reg6/reg_attendee.html',
    {'title': 'Register Attendee',
     'ticket': ticket[0],
     'promo': promo_name,
     'items': selected_items,
     'total': total,
     'form': form,
     'step': 3,
     'steps_total': STEPS_TOTAL,
    })
