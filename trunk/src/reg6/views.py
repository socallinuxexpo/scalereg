# Create your views here.

from django import forms
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response
import datetime
import models
import random
import string
import sys

DEBUG_LOGGING = False
STEPS_TOTAL = 7

def ScaleDebug(msg):
  if not DEBUG_LOGGING:
    return

  frame = sys._getframe(1)

  name = frame.f_code.co_name
  line_number = frame.f_lineno
  filename = frame.f_code.co_filename

  line = 'File "%s", line %d, in %s: %s' % (filename, line_number, name, msg)
  handle = open('/tmp/scale_reg.log', 'a')
  handle.write("%s: %s\n" % (datetime.datetime.now(), line))
  handle.close()


def ApplyPromoToTickets(promo, tickets):
  if not promo:
    return None
  for t in tickets:
    if promo.is_applicable_to(t):
      t.price *= promo.price_modifier
  return promo.name


def ApplyPromoToItems(promo, items):
  if not promo:
    return None
  for item in items:
    if item.promo:
      item.price *= promo.price_modifier
  return promo.name


def GetTicketItems(ticket):
  set1 = ticket.item_set.all()
  set2 = models.Item.objects.filter(applies_to_all=True)
  combined_set = [ s for s in set1 ]
  for s in set2:
    if s not in combined_set:
      combined_set.append(s)
  combined_set.sort()
  return combined_set


def CheckVars(request, post, cookies):
  for var in post:
    if var not in request.POST:
      return scale_render_to_response(request, 'reg6/reg_error.html',
        {'title': 'Registration Problem',
         'error_message': 'No %s information.' % var,
        })
  for var in cookies:
    if var not in request.session:
      return scale_render_to_response(request, 'reg6/reg_error.html',
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


def scale_render_to_response(request, template, vars):
  if 'kiosk' in request.session:
    vars['kiosk'] = True
  return render_to_response(template, vars)


def index(request):
  avail_tickets = models.Ticket.public_objects.order_by('description')
  active_promocode_set = models.PromoCode.active_objects
  avail_promocodes = active_promocode_set.names()

  kiosk_mode = False
  promo_in_use = None
  if request.method == 'GET':
    if 'promo' in request.GET and request.GET['promo'] in avail_promocodes:
      promo_in_use = active_promocode_set.get(name=request.GET['promo'])
    if 'kiosk' in request.GET:
      kiosk_mode = True
  elif request.method == 'POST':
    if 'promo' in request.POST and request.POST['promo'] in avail_promocodes:
      promo_in_use = active_promocode_set.get(name=request.POST['promo'])
    if 'kiosk' in request.POST:
      kiosk_mode = True

  promo_name = ApplyPromoToTickets(promo_in_use, avail_tickets)

  request.session.set_test_cookie()

  if kiosk_mode:
    request.session['kiosk'] = True
    return render_to_response('reg6/reg_kiosk.html')

  return scale_render_to_response(request, 'reg6/reg_index.html',
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
  items = GetTicketItems(ticket[0])
  ApplyPromoToItems(promo_in_use, items)

  return scale_render_to_response(request, 'reg6/reg_items.html',
    {'title': 'Registration - Add Items',
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
  avail_items = GetTicketItems(ticket[0])

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

  questions = []
  all_active_questions = models.Question.objects.filter(active=True)
  for q in all_active_questions:
    if q.applies_to_all or ticket[0] in q.applies_to_tickets.all():
      questions.append(q)
    else:
      for item in selected_items:
        if item in q.applies_to_items.all():
          questions.append(q)
          break

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
    # add survey answers

    for i in xrange(len(questions)):
      i = 'q%d' % i
      if i in request.POST:
        try:
          ans = models.Answer.objects.get(id=request.POST[i])
        except models.Answer.DoesNotExist:
          continue
        new_data.appendlist('answers', request.POST[i])

    try:
      errors = manipulator.get_validation_errors(new_data)
    except: # FIXME sometimes we get an exception, not sure how to reproduce
      return scale_render_to_response(request, 'reg6/reg_error.html',
        {'title': 'Registration Problem',
         'error_message': 'An unexpected error occurred, please try again.'
        })
    if not errors:
      if not request.session.test_cookie_worked():
        return scale_render_to_response(request, 'reg6/reg_error.html',
          {'title': 'Registration Problem',
           'error_message': 'Please do not register multiple attendees at the same time. Please make sure you have cookies enabled.',
          })
      request.session.delete_test_cookie()
      manipulator.do_html2python(new_data)
      new_place = manipulator.save(new_data)
      request.session['attendee'] = new_place.id

      # add attendee to order
      if 'payment' not in request.session:
        request.session['payment'] = [new_place.id]
      else:
        request.session['payment'].append(new_place.id)

      return HttpResponseRedirect('/reg6/registered_attendee/')

  form = forms.FormWrapper(manipulator, new_data, errors)
  return scale_render_to_response(request, 'reg6/reg_attendee.html',
    {'title': 'Register Attendee',
     'ticket': ticket[0],
     'promo': promo_name,
     'items': selected_items,
     'total': total,
     'questions': questions,
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

  return scale_render_to_response(request, 'reg6/reg_finish.html',
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
  all_attendees = []
  bad_attendee = None
  paid_attendee = None
  removed_attendee = None
  total = 0

  # sanitize session data first
  for id in request.session['payment']:
    try:
      person = models.Attendee.objects.get(id=id)
    except models.Attendee.DoesNotExist:
      continue
    if not person.valid:
      all_attendees.append(id)

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
    except (ValueError, models.Attendee.DoesNotExist):
      id = None

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

  return scale_render_to_response(request, 'reg6/reg_start_payment.html',
    {'title': 'Place Your Order',
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
      bad_order_nums += [ x.order_num for x in models.Order.objects.all() ]
      order_num = GenerateOrderID(bad_order_nums)
      temp_order = models.TempOrder(order_num=order_num, attendees=csv)
      temp_order.save()
      order_saved = True
    except: # FIXME catch the specific db exceptions
      order_tries += 1
      if order_tries > 10:
        return scale_render_to_response(request, 'reg6/reg_error.html',
          {'title': 'Registration Problem',
           'error_message': 'We cannot generate an order ID for you.',
          })

  return scale_render_to_response(request, 'reg6/reg_payment.html',
    {'title': 'Registration Payment',
     'attendees': all_attendees_data,
     'order': order_num,
     'step': PAYMENT_STEP,
     'steps_total': STEPS_TOTAL,
     'total': total,
    })


def Sale(request):
  if request.method != 'POST':
    ScaleDebug('not POST')
    return HttpResponseServerError('not POST')
#  if 'HTTP_REFERER' in request.META:
#    print request.META['HTTP_REFERER']
#  if 'HTTP_REFERER' not in request.META  or \
#    '/reg6/start_payment/' not in request.META['HTTP_REFERER']:
#    return HttpResponseRedirect('/reg6/')

  ScaleDebug(request.META)
  ScaleDebug(request.POST)

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
    'USER2',
  ]

  r = CheckVars(request, required_vars, [])
  if r:
    ScaleDebug('required vars missing')
    return HttpResponseServerError('required vars missing')
  if request.POST['RESULT'] != "0":
    ScaleDebug('transaction did not succeed')
    return HttpResponseServerError('transaction did not succeed')
  if request.POST['RESPMSG'] != "Approved":
    ScaleDebug('transaction declined')
    return HttpResponseServerError('transaction declined')

  try:
    temp_order = models.TempOrder.objects.get(order_num=request.POST['USER1'])
  except models.TempOrder.DoesNotExist:
    ScaleDebug('cannot get temp order')
    return HttpResponseServerError('cannot get temp order')

  order_exists = True
  try:
    order = models.Order.objects.get(order_num=request.POST['USER1'])
  except models.Order.DoesNotExist:
    order_exists = False
  if order_exists:
    ScaleDebug('order already exists')
    return HttpResponseServerError('order already exists')

  all_attendees_data = []
  for id in temp_order.attendees_list():
    try:
      attendee = models.Attendee.objects.get(id=id)
      if not attendee.valid:
        all_attendees_data.append(attendee)
    except models.Attendee.DoesNotExist:
      ScaleDebug('cannot find an attendee')
      return HttpResponseServerError('cannot find an attendee')

  total = 0
  for person in all_attendees_data:
    total += person.ticket_cost()
  assert int(total) == int(float(request.POST['AMOUNT']))

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
  except Exception, inst: # FIXME catch the specific db exceptions
    ScaleDebug('cannot save order')
    ScaleDebug(inst.args)
    ScaleDebug(inst)
    return HttpResponseServerError('cannot save order')

  for person in all_attendees_data:
    person.valid = True
    person.order = order
    if request.POST['USER2'] == 'Y':
      person.checked_in = True
    person.save()

  return HttpResponse('success')


def FailedPayment(request):
  return scale_render_to_response(request, 'reg6/reg_failed.html',
    {'title': 'Registration Payment Failed',
    })


def FinishPayment(request):
  PAYMENT_STEP = 7

  if request.method != 'POST':
    return HttpResponseRedirect('/reg6/')
#  if 'HTTP_REFERER' not in request.META  or \
#    '/reg6/start_payment/' not in request.META['HTTP_REFERER']:
#    return HttpResponseRedirect('/reg6/')

  required_vars = [
    'NAME',
    'EMAIL',
    'AMOUNT',
    'USER1',
  ]

  r = CheckVars(request, required_vars, [])
  if r:
    return r

  try:
    order = models.Order.objects.get(order_num=request.POST['USER1'])
  except models.Order.DoesNotExist:
    ScaleDebug('Your order cannot be found')
    return HttpResponseServerError('Your order cannot be found')

  all_attendees_data = models.Attendee.objects.filter(order=order.order_num)

  return scale_render_to_response(request, 'reg6/reg_receipt.html',
    {'title': 'Registration Payment Receipt',
     'name': request.POST['NAME'],
     'email': request.POST['EMAIL'],
     'attendees': all_attendees_data,
     'order': request.POST['USER1'],
     'step': PAYMENT_STEP,
     'steps_total': STEPS_TOTAL,
     'total': request.POST['AMOUNT'],
    })


def RegLookup(request):
  if request.method != 'POST':
    return scale_render_to_response(request, 'reg6/reg_lookup.html',
      {'title': 'Registration Lookup',
      })

  required_vars = [
    'email',
    'zip',
  ]

  r = CheckVars(request, required_vars, [])
  if r:
    return r

  attendees = []
  if request.POST['zip'] and request.POST['email']:
    attendees = models.Attendee.objects.filter(zip=request.POST['zip'],
      email=request.POST['email'])

  return scale_render_to_response(request, 'reg6/reg_lookup.html',
    {'title': 'Registration Lookup',
     'attendees': attendees,
     'email': request.POST['email'],
     'zip': request.POST['zip'],
     'search': 1,
    })
