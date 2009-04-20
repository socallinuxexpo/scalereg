# Create your views here.

from django import forms
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response
import models
import random
import string

STEPS_TOTAL = 6

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


def GenerateOrderID(bad_nums):
  valid_chars = string.ascii_uppercase + string.digits
  id = ''.join([random.choice(valid_chars) for x in xrange(10)])
  if not bad_nums:
    return id
  while id in bad_nums:
    id = ''.join([random.choice(valid_chars) for x in xrange(10)])
  return id


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

  request.session.set_test_cookie()
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
  if 'HTTP_REFERER' not in request.META or \
    '/reg6/' not in request.META['HTTP_REFERER']:
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
  if 'HTTP_REFERER' in request.META:
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
      if not request.session.test_cookie_worked():
        return render_to_response('reg6/reg_error.html',
          {'title': 'Registration Problem',
           'error_message': 'Please do not register multiple attendees at the same time. Please make sure you have cookies enabled.',
          })
      request.session.delete_test_cookie()
      manipulator.do_html2python(new_data)
      new_place = manipulator.save(new_data)
      request.session['attendee'] = new_place.id
      return HttpResponseRedirect('/reg6/registered_attendee/')

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


def RegisteredAttendee(request):
  if request.method != 'GET':
    return HttpResponseRedirect('/reg6/')
  if 'HTTP_REFERER' not in request.META  or \
    '/reg6/add_attendee/' not in request.META['HTTP_REFERER']:
    return HttpResponseRedirect('/reg6/')

  required_cookies = ['attendee']
  r = CheckVars(request, [], required_cookies)
  if r:
    return r

  attendee = models.Attendee.objects.get(id=request.session['attendee'])

  return render_to_response('reg6/reg_finish.html',
    {'title': 'Attendee Registered',
     'attendee': attendee,
     'step': 4,
     'steps_total': STEPS_TOTAL,
    })


def StartPayment(request):
  PAYMENT_STEP = 5

  if 'payment' not in request.session:
    request.session['payment'] = []

  new_attendee = None
  all_attendees = request.session['payment']
  bad_attendee = None
  paid_attendee = None
  removed_attendee = None
  total = 0

  if 'remove' in request.POST:
    try:
      remove_id = int(request.POST['remove'])
      if remove_id in all_attendees:
        all_attendees.remove(remove_id)
    except ValueError:
      pass
  elif 'id' in request.POST and 'email' in request.POST:
    try:
      id = int(request.POST['id'])
      new_attendee = models.Attendee.objects.get(id=id)
    except ValueError:
      pass
    except models.Attendee.DoesNotExist:
      pass

    if id in all_attendees:
      new_attendee = None
    elif new_attendee and new_attendee.email == request.POST['email']:
      if not new_attendee.valid:
        if new_attendee not in all_attendees:
          all_attendees.append(id)
      else:
        paid_attendee = new_attendee
        new_attendee = None
    else:
      bad_attendee = [request.POST['id'], request.POST['email']]
      new_attendee = None

  # sanity check
  checksum = 0
  for f in [new_attendee, bad_attendee, paid_attendee, removed_attendee]:
    if f:
      checksum += 1
  assert checksum <= 1

  all_attendees_data = []
  for id in all_attendees:
    try:
      attendee = models.Attendee.objects.get(id=id)
      if not attendee.valid:
        all_attendees_data.append(attendee)
    except models.Attendee.DoesNotExist:
      pass

  all_attendees = [attendee.id for attendee in all_attendees_data]

  request.session['payment'] = all_attendees
  for person in all_attendees_data:
    total += person.ticket_cost()

  return render_to_response('reg6/reg_start_payment.html',
    {'title': 'Start Payment',
     'bad_attendee': bad_attendee,
     'new_attendee': new_attendee,
     'paid_attendee': paid_attendee,
     'removed_attendee': removed_attendee,
     'attendees': all_attendees_data,
     'step': PAYMENT_STEP,
     'steps_total': STEPS_TOTAL,
     'total': total,
    })


def Payment(request):
  PAYMENT_STEP = 6

  if request.method != 'POST':
    return HttpResponseRedirect('/reg6/')
  if 'HTTP_REFERER' not in request.META  or \
    '/reg6/start_payment/' not in request.META['HTTP_REFERER']:
    return HttpResponseRedirect('/reg6/')

  required_cookies = ['payment']
  r = CheckVars(request, [], required_cookies)
  if r:
    return r

  total = 0

  all_attendees = request.session['payment']
  all_attendees_data = []
  for id in all_attendees:
    try:
      attendee = models.Attendee.objects.get(id=id)
      if not attendee.valid:
        all_attendees_data.append(attendee)
    except models.Attendee.DoesNotExist:
      pass

  all_attendees = [attendee.id for attendee in all_attendees_data]
  request.session['payment'] = all_attendees

  for person in all_attendees_data:
    total += person.ticket_cost()

  csv = ','.join([str(x) for x in all_attendees])

  order_tries = 0
  order_saved = False
  while not order_saved:
    try:
      bad_order_nums = [ x.order_num for x in models.TempOrder.objects.all() ]
      order_num = GenerateOrderID(bad_order_nums)
      temp_order = models.TempOrder(order_num=order_num, attendees=csv)
      temp_order.save()
      order_saved = True
    except: # FIXME catch the specific db exceptions
      order_tries += 1
      if order_tries > 10:
        return render_to_response('reg6/reg_error.html',
          {'title': 'Registration Problem',
           'error_message': 'We cannot generate an order ID for you.',
          })

  return render_to_response('reg6/reg_payment.html',
    {'title': 'Registration Payment',
     'attendees': all_attendees_data,
     'order': order_num,
     'step': PAYMENT_STEP,
     'steps_total': STEPS_TOTAL,
     'total': total,
    })


def Sale(request):
  if request.method != 'POST':
    return HttpResponseServerError('not POST')
  if 'HTTP_REFERER' in request.META:
    print request.META['HTTP_REFERER']
#  if 'HTTP_REFERER' not in request.META  or \
#    '/reg6/start_payment/' not in request.META['HTTP_REFERER']:
#    return HttpResponseRedirect('/reg6/')

  required_vars = [
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
    'RESULT',
    'RESPMSG',
    'USER1',
  ]

  r = CheckVars(request, required_vars, [])
  if r:
    return HttpResponseServerError('required vars missing')

  try:
    temp_order = models.TempOrder.objects.get(order_num=request.POST['USER1'])
  except models.Attendee.DoesNotExist:
    return HttpResponseServerError('cannot get temp order')

  order_exists = True
  try:
    order = models.Order.objects.get(order_num=request.POST['USER1'])
  except models.Order.DoesNotExist:
    order_exists = False
  if order_exists:
    return HttpResponseServerError('order already exists')

  all_attendees_data = []
  for id in temp_order.attendees_list():
    try:
      attendee = models.Attendee.objects.get(id=id)
      if not attendee.valid:
        all_attendees_data.append(attendee)
    except models.Attendee.DoesNotExist:
      return HttpResponseServerError('cannot find an attendee')

  total = 0
  for person in all_attendees_data:
    total += person.ticket_cost()
  assert total == float(request.POST['AMOUNT'])

  try:
    order = models.Order(order_num=request.POST['USER1'],
      valid=True,
      name=request.POST['NAME'],
      address=request.POST['ADDRESS'],
      city=request.POST['CITY'],
      state=request.POST['STATE'],
      zip=int(request.POST['ZIP']),
      country=request.POST['COUNTRY'],
      email=request.POST['EMAIL'],
      phone=request.POST['PHONE'],
      amount=float(request.POST['AMOUNT']),
      payment_type='verisign',
      auth_code=request.POST['AUTHCODE'],
      resp_msg=request.POST['RESPMSG'],
      result=request.POST['RESULT'],
    )
    order.save()
  except: # FIXME catch the specific db exceptions
    return HttpResponseServerError('cannot save order')

  for person in all_attendees_data:
    person.valid = True
    person.order = order
    person.save()

  return HttpResponse('success')
