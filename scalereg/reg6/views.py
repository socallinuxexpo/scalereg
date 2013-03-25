# Create your views here.

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response
from scalereg.common import utils
from scalereg.reg6 import forms
from scalereg.reg6 import models
import datetime
import re
import sys

STEPS_TOTAL = 7

REGISTRATION_PAYMENT_COOKIE = 'payment'

def ScaleDebug(msg):
  if not settings.SCALEREG_DEBUG_LOGGING_ENABLED:
    return

  frame = sys._getframe(1)

  name = frame.f_code.co_name
  line_number = frame.f_lineno
  filename = frame.f_code.co_filename

  line = 'File "%s", line %d, in %s: %s' % (filename, line_number, name, msg)
  handle = open(settings.SCALEREG_DEBUG_LOGGING_PATH, 'a')
  handle.write('%s: %s\n' % (datetime.datetime.now(), line))
  handle.close()


def PrintAttendee(attendee, reprint_ids):
  badge = []
  badge.append(attendee.salutation)
  badge.append(attendee.first_name)
  badge.append(attendee.last_name)
  badge.append(attendee.title)
  badge.append(attendee.org)
  badge.append(attendee.email)
  badge.append(attendee.phone)
  badge.append(attendee.zip)
  badge.append(str(attendee.id))
  if attendee.id in reprint_ids:
    reprint = models.Reprint.objects.get(attendee=attendee)
    badge.append(str(reprint.count))
  else:
    badge.append('0')
  badge.append(attendee.badge_type.type)
  if not attendee.order:
    return ''
  if attendee.order.payment_type in ('verisign', 'google', 'cash'):
    badge.append('%2.2f' % attendee.ticket_cost())
  else:
    badge.append('0.00')

  try:
    tshirt = attendee.answers.filter(question='What is your shirt size?')
    if tshirt:
      badge.append(tshirt[0].text)
    else:
      badge.append('???')
  except:
    badge.append('???')
    pass

  for i in attendee.ordered_items.all():
    badge.append(i.name)

  return '~' + '~'.join([x.replace('~', '') for x in badge]) + '~'


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


def ApplyPromoToPostedItems(ticket, promo, post):
  avail_items = GetTicketItems(ticket)
  selected_items = []
  for i in xrange(len(avail_items)):
    item_number = 'item%d' % i
    if item_number in post:
      try:
        item = models.Item.objects.get(name=post[item_number])
      except:
        continue
      if item in avail_items:
        selected_items.append(item)
  ApplyPromoToItems(promo, selected_items)
  return selected_items


def FindRelevantQuestions(type, ticket, selected_items):
  questions = []
  all_active_questions = type.objects.filter(active=True)
  for q in all_active_questions:
    if q.applies_to_all or ticket in q.applies_to_tickets.all():
      questions.append(q)
    else:
      relevant_items = q.applies_to_items.all()
      for item in selected_items:
        if item in relevant_items:
          questions.append(q)
          break
  return questions


def ItemNameCompare(x, y):
  if x.name == y.name:
    return 0
  if x.name < y.name:
    return -1
  return 1


def GetTicketItems(ticket):
  set1 = ticket.item_set.all()
  set2 = models.Item.objects.filter(applies_to_all=True)
  combined_set = [ s for s in set1 if s.active ]
  for s in set2:
    if not s.active:
      continue
    if s not in combined_set:
      combined_set.append(s)
  combined_set.sort(cmp=ItemNameCompare)
  return combined_set


def IsTicketAvailable(ticket, num_to_buy):
  if ticket.limit == 0:
    return True
  attendees = models.Attendee.objects.filter(badge_type=ticket, valid=True)
  return (attendees.count() + num_to_buy) <= ticket.limit


def CalculateTicketCost(ticket, items):
  total = ticket.price
  offset_item = None
  for item in items:
    total += item.price
    if offset_item:
      continue
    if item.ticket_offset:
      offset_item = item
  if offset_item:
    total -= ticket.price
  return (total, offset_item)


def IsUpgradeUnchanged(attendee, ticket, selected_items):
  if attendee.badge_type != ticket:
    return False
  attendee_items = attendee.ordered_items.all()
  if len(selected_items) != len(attendee_items):
    return False
  for item in selected_items:
    if item not in attendee_items:
      return False
  return True


def FindUpgradeAttendee(attendee_id, attendee_email):
  not_eligible = None
  not_found = False
  not_paid = False

  try:
    attendee_id = int(attendee_id)
    attendee = models.Attendee.objects.get(id=attendee_id)
  except (ValueError, models.Attendee.DoesNotExist):
    attendee = None

  if attendee and attendee.email != attendee_email:
    attendee = None

  if not attendee:
    not_found = True
  else:
    if not attendee.valid:
      not_paid = True
    elif not attendee.badge_type.upgradable:
      not_eligible = attendee
  return (attendee, not_eligible, not_found, not_paid)


def HandleBadUpgrade(request, not_found, not_paid, not_eligible):
  if not_found:
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'Invalid upgrade: Attendee not found'
      })
  if not_paid:
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'Invalid upgrade: Unpaid attendee'
      })
  if not_eligible:
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'Invalid upgrade: Ineligible attendee'
      })
  return None


def CreateUpgrade(attendee, new_ticket, new_items):
  upgrade = models.Upgrade()
  upgrade.attendee = attendee
  upgrade.old_badge_type = attendee.badge_type
  upgrade.old_order = attendee.order
  upgrade.new_badge_type = new_ticket
  upgrade.save()
  for s in attendee.ordered_items.all():
    upgrade.old_ordered_items.add(s)
  for s in new_items:
    upgrade.new_ordered_items.add(s)
  return upgrade


def UpgradeAttendee(upgrade, new_order):
  upgrade.new_order = new_order
  upgrade.valid = True
  upgrade.save()

  person = upgrade.attendee
  person.badge_type = upgrade.new_badge_type
  person.order = new_order
  person.save()
  person.ordered_items.clear()
  for s in upgrade.new_ordered_items.all():
    person.ordered_items.add(s)


def CheckPaymentAmount(request, expected_cost):
  r = CheckVars(request, ['AMOUNT'], [])
  if r:
    return r
  actual = int(float(request.POST['AMOUNT']))
  expected = int(expected_cost)
  if actual == expected:
    return None
  reason = 'incorrect payment amount, expected %d, got %d' % (expected, actual)
  ScaleDebug(reason)
  return HttpResponseServerError(reason)


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


def CheckReferrer(meta, path):
  if 'HTTP_REFERER' in meta and path in meta['HTTP_REFERER']:
    return None
  return HttpResponseRedirect('/reg6/')


def GenerateOrderID(bad_nums):
  return utils.GenerateUniqueID(10, bad_nums)


def scale_render_to_response(request, template, vars):
  if 'kiosk' in request.session:
    vars['kiosk'] = True
  return render_to_response(template, vars)


def index(request):
  avail_tickets = [ticket for ticket in
                   models.Ticket.public_objects.order_by('description')
                   if IsTicketAvailable(ticket, 1)]
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


def kiosk_index(request):
  response = HttpResponse()
  response.write("""<html><head></head>
  <body>
  <div align="center">
  <h1>Welcome to SCALE 6X</h1>
  <h1>February 8 - 10, 2008</h1>

  <hr noshade width="60%">

  <h1>Please make a selection below:</h1>

  <table border="0" cellpadding="4">
  <tr>
  <td valign="top">
  <form method="get" action="../checkin/">
  <input type="submit" value="&nbsp;&nbsp;Check In&nbsp;&nbsp;">
  <input type="hidden" name="kiosk" value="1">
  </form>
  </td>
  <td valign="top">
  If you already registered with SCALE<br />
  and would like to pick up your badge.
  </td>
  </tr>
  <tr>
  <td valign="top">
  <form method="get" action="../">
  <input type="submit" value="Registration">
  <input type="hidden" name="kiosk" value="1">
  </form>
  </td>
  <td valign="top">If you have not registered with SCALE.</td>
  </tr>
  </table>

  <p>If you are a speaker, exhibitor, or a member of the press, please go to
  the registration desk.</p>
  </div></body></html>""")
  return response


def AddItems(request):
  if request.method != 'POST':
    return HttpResponseRedirect('/reg6/')
  r = CheckReferrer(request.META, '/reg6/')
  if r:
    return r

  required_vars = ['promo', 'ticket']
  r = CheckVars(request, required_vars, [])
  if r:
    return r

  ticket = models.Ticket.public_objects.filter(name=request.POST['ticket'])
  active_promocode_set = models.PromoCode.active_objects
  avail_promocodes = active_promocode_set.names()

  promo = request.POST['promo'].upper()
  promo_in_use = None
  if promo in avail_promocodes:
    promo_in_use = active_promocode_set.get(name=promo)

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

  try:
    ticket = models.Ticket.public_objects.get(name=request.POST['ticket'])
  except models.Ticket.DoesNotExist:
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'You have selected an invalid ticket type.',
      })
  if not IsTicketAvailable(ticket, 1):
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'The ticket you selected is sold out.',
      })
  active_promocode_set = models.PromoCode.active_objects
  avail_promocodes = active_promocode_set.names()

  promo_in_use = None
  if request.POST['promo'] in avail_promocodes:
    promo_in_use = active_promocode_set.get(name=request.POST['promo'])

  promo_name = ApplyPromoToTickets(promo_in_use, [ticket])
  selected_items = ApplyPromoToPostedItems(ticket, promo_in_use, request.POST)
  (total, offset_item) = CalculateTicketCost(ticket, selected_items)

  list_questions = FindRelevantQuestions(models.ListQuestion, ticket,
      selected_items)
  text_questions = FindRelevantQuestions(models.TextQuestion, ticket,
      selected_items)

  if action == 'add':
    request.session['attendee'] = ''
    form = forms.AttendeeForm()
  else:
    if 'attendee' in request.session and request.session['attendee']:
      return scale_render_to_response(request, 'reg6/reg_error.html',
        {'title': 'Registration Problem',
         'error_message': 'You already added this attendee.',
        })
    form = forms.AttendeeForm(request.POST)
    if form.is_valid():
      if not request.session.test_cookie_worked():
        return scale_render_to_response(request, 'reg6/reg_error.html',
          {'title': 'Registration Problem',
           'error_message': 'Please do not register multiple attendees at the same time. Please make sure you have cookies enabled.',
          })

      # create attendee
      new_attendee = form.save(commit=False)

      # add badge type
      new_attendee.badge_type = ticket
      # add promo
      new_attendee.promo = promo_in_use

      # save attendee
      new_attendee.save()
      form.save_m2m()

      # add ordered items
      for s in selected_items:
        new_attendee.ordered_items.add(s)
      # add survey answers
      for i in xrange(len(list_questions)):
        i = 'lq%d' % i
        if i in request.POST and request.POST[i]:
          try:
            ans = models.Answer.objects.get(id=request.POST[i])
            new_attendee.answers.add(ans)
          except models.Answer.DoesNotExist:
            continue
      for q in text_questions:
        i = 'tq%d' % q.id
        if i in request.POST and request.POST[i]:
          answer = models.TextAnswer()
          answer.question = q
          answer.text = request.POST[i][:q.max_length]
          answer.save()
          new_attendee.answers.add(answer)

      request.session['attendee'] = new_attendee.id

      # add attendee to order
      if REGISTRATION_PAYMENT_COOKIE not in request.session:
        request.session[REGISTRATION_PAYMENT_COOKIE] = [new_attendee.id]
      else:
        request.session[REGISTRATION_PAYMENT_COOKIE].append(new_attendee.id)

      return HttpResponseRedirect('/reg6/registered_attendee/')

  return scale_render_to_response(request, 'reg6/reg_attendee.html',
    {'title': 'Register Attendee',
     'ticket': ticket,
     'promo': promo_name,
     'items': selected_items,
     'offset_item': offset_item,
     'total': total,
     'list_questions': list_questions,
     'text_questions': text_questions,
     'form': form,
     'step': 3,
     'steps_total': STEPS_TOTAL,
    })


def RegisteredAttendee(request):
  if request.method != 'GET':
    return HttpResponseRedirect('/reg6/')
  r = CheckReferrer(request.META, '/reg6/add_attendee/')
  if r:
    return r

  required_cookies = ['attendee']
  r = CheckVars(request, [], required_cookies)
  if r:
    return r

  attendee = models.Attendee.objects.get(id=request.session['attendee'])

  return scale_render_to_response(request, 'reg6/reg_finish.html',
    {'title': 'Attendee Registered (Payment still required)',
     'attendee': attendee,
     'step': 4,
     'steps_total': STEPS_TOTAL,
    })


def StartPayment(request):
  PAYMENT_STEP = 5

  if REGISTRATION_PAYMENT_COOKIE not in request.session:
    request.session[REGISTRATION_PAYMENT_COOKIE] = []

  all_attendees = []
  new_attendee = None
  bad_attendee = None
  paid_attendee = None
  removed_attendee = None

  # sanitize session data first
  for attendee_id in request.session[REGISTRATION_PAYMENT_COOKIE]:
    try:
      person = models.Attendee.objects.get(id=attendee_id)
    except models.Attendee.DoesNotExist:
      continue
    if not person.valid:
      all_attendees.append(attendee_id)

  if request.method == 'POST':
    if 'remove' in request.POST:
      try:
        remove_id = int(request.POST['remove'])
        if remove_id in all_attendees:
          all_attendees.remove(remove_id)
      except ValueError:
        pass
    elif 'id' in request.POST and 'email' in request.POST:
      try:
        attendee_id = int(request.POST['id'])
        new_attendee = models.Attendee.objects.get(id=attendee_id)
      except (ValueError, models.Attendee.DoesNotExist):
        attendee_id = None

      if attendee_id in all_attendees:
        new_attendee = None
      elif new_attendee and new_attendee.email == request.POST['email']:
        if not new_attendee.valid:
          if new_attendee not in all_attendees:
            all_attendees.append(attendee_id)
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
  for attendee_id in all_attendees:
    try:
      attendee = models.Attendee.objects.get(id=attendee_id)
      if not attendee.valid:
        all_attendees_data.append(attendee)
    except models.Attendee.DoesNotExist:
      pass

  request.session[REGISTRATION_PAYMENT_COOKIE] = [
    attendee.id for attendee in all_attendees_data
  ]

  total = 0
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
  r = CheckReferrer(request.META, '/reg6/start_payment/')
  if r:
    return r

  required_cookies = [REGISTRATION_PAYMENT_COOKIE]
  r = CheckVars(request, [], required_cookies)
  if r:
    return r

  total = 0

  all_attendees = request.session[REGISTRATION_PAYMENT_COOKIE]
  all_attendees_data = []
  for attendee_id in all_attendees:
    try:
      attendee = models.Attendee.objects.get(id=attendee_id)
      if not attendee.valid:
        all_attendees_data.append(attendee)
    except models.Attendee.DoesNotExist:
      pass

  all_attendees = [attendee.id for attendee in all_attendees_data]
  request.session[REGISTRATION_PAYMENT_COOKIE] = all_attendees

  attendees_by_ticket = {}
  for person in all_attendees_data:
    if person.badge_type in attendees_by_ticket:
      attendees_by_ticket[person.badge_type] += 1
    else:
      attendees_by_ticket[person.badge_type] = 1
  tickets_soldout = []
  for ticket,num_to_buy in attendees_by_ticket.iteritems():
    if not IsTicketAvailable(ticket, num_to_buy):
      tickets_soldout.append(ticket.description)
  if tickets_soldout:
    return scale_render_to_response(request, 'reg6/reg_payment.html',
      {'title': 'Registration Payment',
       'step': PAYMENT_STEP,
       'steps_total': STEPS_TOTAL,
       'tickets_soldout': tickets_soldout,
    })

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
     'payflow_partner': settings.SCALEREG_PAYFLOW_PARTNER,
     'payflow_login': settings.SCALEREG_PAYFLOW_LOGIN,
     'step': PAYMENT_STEP,
     'steps_total': STEPS_TOTAL,
     'total': total,
    })


def Sale(request):
  if request.method != 'POST':
    ScaleDebug('not POST')
    return HttpResponse('Method not allowed: %s' % request.method, status=405)
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
    'PNREF',
    'RESULT',
    'RESPMSG',
    'USER1',
    'USER2',
  ]

  r = CheckVars(request, required_vars, [])
  if r:
    ScaleDebug('required vars missing')
    return HttpResponseServerError('required vars missing')
  if request.POST['RESULT'] != '0':
    ScaleDebug('transaction did not succeed')
    return HttpResponse('transaction did not succeed')
  if request.POST['RESPMSG'] != 'Approved':
    ScaleDebug('transaction declined')
    return HttpResponse('transaction declined')

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
  already_paid_attendees_data = []
  upgrade = temp_order.upgrade
  if upgrade:
    r = CheckPaymentAmount(request, upgrade.upgrade_cost())
    if r:
      return r
    person = upgrade.attendee
    items = [item.name for item in person.ordered_items.all()]
    items = set(items)
    orig_items = [item.name for item in upgrade.old_ordered_items.all()]
    orig_items = set(orig_items)
    if (upgrade.valid or
        person.badge_type != upgrade.old_badge_type or
        person.order != upgrade.old_order or
        items != orig_items):
      ScaleDebug('bad upgrade')
      return HttpResponseServerError('bad upgrade')

  else:
    for attendee_id in temp_order.attendees_list():
      try:
        attendee = models.Attendee.objects.get(id=attendee_id)
        if attendee.valid:
          already_paid_attendees_data.append(attendee)
        else:
          all_attendees_data.append(attendee)
      except models.Attendee.DoesNotExist:
        ScaleDebug('cannot find an attendee')
        return HttpResponseServerError('cannot find an attendee')

    total = 0
    for person in all_attendees_data:
      total += person.ticket_cost()
    for person in already_paid_attendees_data:
      total += person.ticket_cost()
    r = CheckPaymentAmount(request, total)
    if r:
      return r

  try:
    order = models.Order(order_num=request.POST['USER1'],
      valid=True,
      name=request.POST['NAME'],
      address=request.POST['ADDRESS'],
      city=request.POST['CITY'],
      state=request.POST['STATE'],
      zip=request.POST['ZIP'],
      country=request.POST['COUNTRY'],
      email=request.POST['EMAIL'],
      phone=request.POST['PHONE'],
      amount=request.POST['AMOUNT'],
      payment_type='verisign',
      auth_code=request.POST['AUTHCODE'],
      pnref=request.POST['PNREF'],
      resp_msg=request.POST['RESPMSG'],
      result=request.POST['RESULT'],
    )
    order.save()
    for attendee in already_paid_attendees_data:
      order.already_paid_attendees.add(attendee)
  except Exception, inst: # FIXME catch the specific db exceptions
    ScaleDebug('cannot save order')
    print inst
    ScaleDebug(inst.args)
    ScaleDebug(inst)
    return HttpResponseServerError('cannot save order')

  if upgrade:
    UpgradeAttendee(upgrade, order)
  else:
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
    temp_order = models.TempOrder.objects.get(order_num=request.POST['USER1'])
    order = models.Order.objects.get(order_num=request.POST['USER1'])
  except models.Order.DoesNotExist:
    ScaleDebug('Your order cannot be found')
    return HttpResponseServerError('Your order cannot be found')

  if temp_order.upgrade:
    return scale_render_to_response(request, 'reg6/reg_receipt_upgrade.html',
      {'title': 'Registration Payment Receipt',
       'name': request.POST['NAME'],
       'email': request.POST['EMAIL'],
       'order': request.POST['USER1'],
       'total': request.POST['AMOUNT'],
       'upgrade': temp_order.upgrade
      })

  all_attendees_data = models.Attendee.objects.filter(order=order.order_num)
  already_paid_attendees_data = order.already_paid_attendees

  return scale_render_to_response(request, 'reg6/reg_receipt.html',
    {'title': 'Registration Payment Receipt',
     'name': request.POST['NAME'],
     'email': request.POST['EMAIL'],
     'attendees': all_attendees_data,
     'already_paid_attendees': already_paid_attendees_data.all(),
     'order': request.POST['USER1'],
     'step': PAYMENT_STEP,
     'steps_total': STEPS_TOTAL,
     'total': request.POST['AMOUNT'],
    })


def StartUpgrade(request):
  if request.method != 'POST':
    return scale_render_to_response(request, 'reg6/reg_start_upgrade.html',
      {'title': 'Registration Upgrade',
      })

  # POST, look for attendee first.
  if not 'id' in request.POST or not 'email' in request.POST:
    return scale_render_to_response(request, 'reg6/reg_start_upgrade.html',
      {'title': 'Registration Upgrade',
      })

  (attendee, not_eligible, not_found, not_paid) = \
    FindUpgradeAttendee(request.POST['id'], request.POST['email'])

  if not_found or not_paid or not_eligible:
    return scale_render_to_response(request, 'reg6/reg_start_upgrade.html',
      {'title': 'Registration Upgrade',
       'email': request.POST['email'],
       'id': request.POST['id'],
       'not_eligible': not_eligible,
       'not_found': not_found,
       'not_paid': not_paid,
      })

  # Valid attendee found.

  # Show final upgrade confirmation if items have been selected.
  if 'has_selected_items' in request.POST and 'ticket' in request.POST:
    tickets = models.Ticket.objects.filter(name=request.POST['ticket'])
    if len(tickets) != 1:
      return scale_render_to_response(request, 'reg6/reg_error.html',
        {'title': 'Registration Problem',
         'error_message': 'You have selected an invalid ticket type.',
        })
    ApplyPromoToTickets(attendee.promo, tickets)
    selected_ticket = tickets[0]
    selected_items = ApplyPromoToPostedItems(selected_ticket, attendee.promo,
                                             request.POST)
    (total, offset_item) = CalculateTicketCost(selected_ticket, selected_items)
    upgrade_cost = total - attendee.ticket_cost()
    unchanged = IsUpgradeUnchanged(attendee, selected_ticket, selected_items)

    return scale_render_to_response(request, 'reg6/reg_start_upgrade.html',
      {'title': 'Registration Upgrade',
       'attendee': attendee,
       'has_selected_items': True,
       'selected_items': selected_items,
       'selected_ticket': selected_ticket,
       'total': total,
       'unchanged': unchanged,
       'upgrade_cost': upgrade_cost,
      })

  # Show available items if there is a ticket selected.
  if 'ticket' in request.POST:
    tickets = models.Ticket.objects.filter(name=request.POST['ticket'])
    if len(tickets) != 1:
      return scale_render_to_response(request, 'reg6/reg_error.html',
        {'title': 'Registration Problem',
         'error_message': 'You have selected an invalid ticket type.',
        })
    ApplyPromoToTickets(attendee.promo, tickets)
    selected_ticket = tickets[0]
    items = GetTicketItems(selected_ticket)
    ApplyPromoToItems(attendee.promo, items)
    return scale_render_to_response(request, 'reg6/reg_start_upgrade.html',
      {'title': 'Registration Upgrade',
       'attendee': attendee,
       'items': items,
       'selected_ticket': selected_ticket,
      })

  # Show available tickets.
  avail_tickets = [ticket for ticket in
                   models.Ticket.public_objects.order_by('description')
                   if (IsTicketAvailable(ticket, 1) and
                       ticket != attendee.badge_type)]
  ApplyPromoToTickets(attendee.promo, avail_tickets)
  return scale_render_to_response(request, 'reg6/reg_start_upgrade.html',
    {'title': 'Registration Upgrade',
     'attendee': attendee,
     'tickets': avail_tickets,
    })


def NonFreeUpgrade(request):
  if request.method != 'POST':
    return HttpResponseRedirect('/reg6/')
  r = CheckReferrer(request.META, '/reg6/start_upgrade/')
  if r:
    return r

  required_vars = [
    'email',
    'id',
    'ticket'
  ]
  r = CheckVars(request, required_vars, [])
  if r:
    return r

  (attendee, not_eligible, not_found, not_paid) = \
    FindUpgradeAttendee(request.POST['id'], request.POST['email'])
  r = HandleBadUpgrade(request, not_found, not_paid, not_eligible)
  if r:
    return r

  # Valid attendee found.
  tickets = models.Ticket.objects.filter(name=request.POST['ticket'])
  if len(tickets) != 1:
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'Invalid upgrade: Invalid ticket type.',
      })
  ApplyPromoToTickets(attendee.promo, tickets)
  selected_ticket = tickets[0]
  selected_items = ApplyPromoToPostedItems(selected_ticket, attendee.promo,
                                           request.POST)
  (total, offset_item) = CalculateTicketCost(selected_ticket, selected_items)
  upgrade_cost = total - attendee.ticket_cost()

  # Check for unchanged registration
  unchanged = IsUpgradeUnchanged(attendee, selected_ticket, selected_items)
  if unchanged:
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'Invalid upgrade: Unchanged attendee.',
      })

  try:
    upgrade = CreateUpgrade(attendee, selected_ticket, selected_items)
  except: # FIXME catch the specific db exceptions
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'Cannot save upgrade',
      })

  order_tries = 0
  order_saved = False
  while not order_saved:
    try:
      bad_order_nums = [ x.order_num for x in models.TempOrder.objects.all() ]
      bad_order_nums += [ x.order_num for x in models.Order.objects.all() ]
      order_num = GenerateOrderID(bad_order_nums)
      temp_order = models.TempOrder(order_num=order_num, upgrade=upgrade)
      temp_order.save()
      order_saved = True
    except: # FIXME catch the specific db exceptions
      order_tries += 1
      if order_tries > 10:
        return scale_render_to_response(request, 'reg6/reg_error.html',
          {'title': 'Registration Problem',
           'error_message': 'We cannot generate an order ID for you.',
          })

  return scale_render_to_response(request, 'reg6/reg_non_free_upgrade.html',
    {'title': 'Registration Upgrade',
     'attendee': attendee,
     'order': order_num,
     'payflow_partner': settings.SCALEREG_PAYFLOW_PARTNER,
     'payflow_login': settings.SCALEREG_PAYFLOW_LOGIN,
     'upgrade': upgrade,
    })


def FreeUpgrade(request):
  if request.method != 'POST':
    ScaleDebug('not POST')
    return HttpResponse('Method not allowed: %s' % request.method, status=405)
  required_vars = [
    'id',
    'email',
    'ticket',
  ]
  r = CheckVars(request, required_vars, [])
  if r:
    return r

  (attendee, not_eligible, not_found, not_paid) = \
    FindUpgradeAttendee(request.POST['id'], request.POST['email'])
  r = HandleBadUpgrade(request, not_found, not_paid, not_eligible)
  if r:
    return r

  # Valid attendee found.
  tickets = models.Ticket.objects.filter(name=request.POST['ticket'])
  if len(tickets) != 1:
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'Invalid upgrade: Invalid ticket type.',
      })
  ApplyPromoToTickets(attendee.promo, tickets)
  selected_ticket = tickets[0]
  selected_items = ApplyPromoToPostedItems(selected_ticket, attendee.promo,
                                           request.POST)
  (total, offset_item) = CalculateTicketCost(selected_ticket, selected_items)
  upgrade_cost = total - attendee.ticket_cost()
  if upgrade_cost > 0:
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'Invalid upgrade: Not Free.',
      })

  try:
    upgrade = CreateUpgrade(attendee, selected_ticket, selected_items)
  except: # FIXME catch the specific db exceptions
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'Cannot save upgrade',
      })

  order_tries = 0
  order_saved = False
  while not order_saved:
    try:
      bad_order_nums = [ x.order_num for x in models.TempOrder.objects.all() ]
      bad_order_nums += [ x.order_num for x in models.Order.objects.all() ]
      order_num = GenerateOrderID(bad_order_nums)
      order = models.Order(order_num=order_num,
        valid=True,
        name='Free Upgrade',
        address='N/A',
        city='N/A',
        state='N/A',
        zip='N/A',
        email=attendee.email,
        amount=0,
        payment_type='freeup',
      )
      order.save()
      order_saved = True
    except: # FIXME catch the specific db exceptions
      order_tries += 1
      if order_tries > 10:
        return scale_render_to_response(request, 'reg6/reg_error.html',
          {'title': 'Registration Problem',
           'error_message': 'We cannot generate an order ID for you.',
          })

  UpgradeAttendee(upgrade, order)
  return scale_render_to_response(request, 'reg6/reg_receipt_upgrade.html',
    {'title': 'Registration Payment Receipt',
     'name': attendee.full_name(),
     'email': attendee.email,
     'order': order,
     'total': 0,
     'upgrade': upgrade,
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


def CheckIn(request):
  kiosk_mode = False
  if request.method == 'GET':
    if 'kiosk' in request.GET:
      request.session['kiosk'] = True
      return render_to_response('reg6/reg_kiosk.html')

    return scale_render_to_response(request, 'reg6/reg_checkin.html',
      {'title': 'Check In',
      })

  attendees = []
  attendees_email = []
  attendees_zip = []
  if request.POST['zip'] and request.POST['email']:
    attendees = models.Attendee.objects.filter(valid=True, checked_in=False,
      zip=request.POST['zip'],
      email=request.POST['email'])
  if not attendees:
    if request.POST['first'] and request.POST['last']:
      attendees = models.Attendee.objects.filter(valid=True, checked_in=False,
        first_name=request.POST['first'],
        last_name=request.POST['last'])
    if attendees:
      if request.POST['email']:
        attendees_email = attendees.filter(email=request.POST['email'])
      if request.POST['zip']:
        attendees_zip = attendees.filter(zip=request.POST['zip'])
      if attendees_email:
        attendees = attendees_email
      elif attendees_zip:
        attendees = attendees_zip

  return scale_render_to_response(request, 'reg6/reg_checkin.html',
    {'title': 'Check In',
     'attendees': attendees,
     'first': request.POST['first'],
     'last': request.POST['last'],
     'email': request.POST['email'],
     'zip': request.POST['zip'],
     'search': 1,
    })


def FinishCheckIn(request):
  if request.method != 'POST':
    return HttpResponseRedirect('/reg6/')

  required_vars = [
    'id',
  ]

  r = CheckVars(request, required_vars, [])
  if r:
    return r

  try:
    attendee = models.Attendee.objects.get(id=request.POST['id'])
  except models.Attendee.DoesNotExist:
    return HttpResponseServerError('We could not find your registration')

  try:
    attendee.checked_in = True
    attendee.save()
  except:
    return HttpResponseServerError('We encountered a problem with your checkin')

  return scale_render_to_response(request, 'reg6/reg_finish_checkin.html',
    {'title': 'Checked In',
     'attendee': attendee,
    })

def RedeemCoupon(request):
  PAYMENT_STEP = 7

  if request.method != 'POST':
    return HttpResponseRedirect('/reg6/')
  r = CheckReferrer(request.META, '/reg6/payment/')
  if r:
    return r

  required_vars = [
    'code',
    'order',
  ]

  r = CheckVars(request, required_vars, [])
  if r:
    return r

  try:
    coupon = models.Coupon.objects.get(code=request.POST['code'])
  except models.Coupon.DoesNotExist:
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'Invalid coupon'
      })

  if not coupon.is_valid():
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'This coupon has expired'
      })

  try:
    temp_order = models.TempOrder.objects.get(order_num=request.POST['order'])
  except models.TempOrder.DoesNotExist:
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'cannot get temp order'
      })

  num_attendees = len(temp_order.attendees_list())
  if num_attendees > coupon.max_attendees:
    return scale_render_to_response(request, 'reg6/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'coupon not valid for the number of attendees'
      })

  all_attendees_data = []
  for attendee_id in temp_order.attendees_list():
    try:
      attendee = models.Attendee.objects.get(id=attendee_id)
      if not attendee.valid:
        all_attendees_data.append(attendee)
    except models.Attendee.DoesNotExist:
      return HttpResponseServerError('cannot find an attendee')

  for person in all_attendees_data:
    # remove non-free addon items
    for item in person.ordered_items.all():
      if item.price > 0:
        person.ordered_items.remove(item)
    person.valid = True
    person.order = coupon.order
    person.badge_type = coupon.badge_type
    person.promo = None
    person.save()

  coupon.max_attendees = coupon.max_attendees - num_attendees
  if coupon.max_attendees == 0:
    coupon.used = True
  coupon.save()

  return scale_render_to_response(request, 'reg6/reg_receipt.html',
    {'title': 'Registration Payment Receipt',
     'attendees': all_attendees_data,
     'coupon_code': request.POST['code'],
     'step': PAYMENT_STEP,
     'steps_total': STEPS_TOTAL,
    })


@login_required
def AddCoupon(request):
  can_access = False
  if request.user.is_superuser:
    can_access = True
  else:
    perms = request.user.get_all_permissions()
    if 'reg6.add_order' in perms and 'reg6.add_coupon' in perms:
      can_access = True

  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  # FIXME Add this to the Ticket model?
  ticket_types = {
    'expo': 'invitee',
    'full': 'invitee',
    'press': 'press',
    'speaker': 'speaker',
    'exhibitor': 'exhibitor',
    'friday': 'invitee',
  }

  if request.method == 'GET':
    tickets = []
    for ticket_type in ticket_types.keys():
      temp_tickets = models.Ticket.objects.filter(type=ticket_type)
      for t in temp_tickets:
        tickets.append(t)
    form = forms.AddCouponForm()
    return scale_render_to_response(request, 'reg6/add_coupon.html',
      {'title': 'Add Coupon',
       'form': form,
       'tickets': tickets,
      })

  required_vars = [
    'TICKET',
    'MAX_ATTENDEES',
  ]

  r = CheckVars(request, required_vars, [])
  if r:
    return HttpResponseServerError('required vars missing')

  try:
    ticket = models.Ticket.objects.get(name=request.POST['TICKET'])
  except:
    return HttpResponseServerError('cannot find ticket %s' % request.POST['TICKET'])

  form = forms.AddCouponForm(request.POST)
  if not form.is_valid():
    return HttpResponseServerError('parts of the form is not filled out, please try again')

  order = form.save(commit=False)
  bad_order_nums = [ x.order_num for x in models.Order.objects.all() ]
  order.order_num = GenerateOrderID(bad_order_nums)
  order.valid = False
  order.amount = '0'
  order.payment_type=ticket_types[ticket.type]

  order.save()
  form.save_m2m()

  coupon = models.Coupon(code=order.order_num,
    badge_type = ticket,
    order = order,
    used = False,
    max_attendees = request.POST['MAX_ATTENDEES'],
  )
  try:
    coupon.save()
  except: # FIXME catch the specific db exceptions
    order.delete()
    return HttpResponseServerError('error saving the coupon')

  try:
    order.valid = True
    order.save()
  except: # FIXME catch the specific db exceptions
    order.delete()
    coupon.delete()
    return HttpResponseServerError('error saving the order')

  return HttpResponse('Success! Your coupon code is: %s' % order.order_num)


@login_required
def CheckedIn(request):
  if not request.user.is_superuser:
    return HttpResponse('')

  attendees = models.Attendee.objects.filter(valid=True)
  if request.method == 'GET':
    attendees = attendees.filter(checked_in=True)
    if 'idsonly' in request.GET:
      return HttpResponse('\n'.join([str(f.id) for f in attendees]),
                          mimetype='text/plain')

  reprint_ids = [reprint.attendee.id
                 for reprint in models.Reprint.objects.all()]
  return HttpResponse(
      '\n'.join([PrintAttendee(f, reprint_ids) for f in attendees]),
          mimetype='text/plain')


@login_required
def MassAddAttendee(request):
  if not request.user.is_superuser:
    return HttpResponse('')
  if request.method == 'GET':
    response = HttpResponse()
    response.write('<html><head></head><body><form method="post">')
    response.write('<p>first_name,last_name,title,org,zip,email,phone,order_number,ticket_code</p>')
    response.write('<textarea name="data" rows="25" cols="80"></textarea>')
    response.write('<br /><input type="submit" /></form>')
    response.write('</body></html>')
    return response

  if 'data' not in request.POST:
    return HttpResponse('No Data')

  response = HttpResponse()
  response.write('<html><head></head><body>')

  data = request.POST['data'].split('\n')
  for entry in data:
    entry = entry.strip()
    if not entry:
      continue
    entry_split = entry.split(',')
    if len(entry_split) != 9:
      response.write('bad data: %s<br />\n' % entry)
      continue

    try:
      order = models.Order.objects.get(order_num=entry_split[7])
    except models.Order.DoesNotExist:
      response.write('bad order number: %s<br />\n' % entry_split[7])
      continue

    try:
      ticket = models.Ticket.objects.get(name=entry_split[8])
    except models.Ticket.DoesNotExist:
      response.write('bad ticket type: %s<br />\n' % entry_split[8])
      continue

    entry_dict = {
      'first_name': entry_split[0],
      'last_name': entry_split[1],
      'title': entry_split[2],
      'org': entry_split[3],
      'zip': entry_split[4],
      'email': entry_split[5],
      'phone': entry_split[6],
      'badge_type': ticket,
    }
    form = forms.MassAddAttendeeForm(entry_dict)
    if not form.is_valid():
      response.write('bad entry: %s, reason: %s<br />\n' % (entry, form.errors))
      continue
    attendee = form.save(commit=False)
    attendee.valid = True
    attendee.checked_in = False
    attendee.can_email = True
    attendee.order = order
    attendee.badge_type = ticket
    attendee.save()
    form.save_m2m()
    response.write('Added %s<br />\n' % entry)

  response.write('</body></html>')
  return response


@login_required
def MassAddPromo(request):
  if not request.user.is_superuser:
    return HttpResponse('')
  if request.method == 'GET':
    response = HttpResponse()
    response.write('<html><head></head><body><form method="post">')
    response.write('<p>code,modifier,description</p>')
    response.write('<textarea name="data" rows="25" cols="80"></textarea>')
    response.write('<br /><input type="submit" /></form>')
    response.write('</body></html>')
    return response

  if 'data' not in request.POST:
    return HttpResponse('No Data')

  response = HttpResponse()
  response.write('<html><head></head><body>')

  # apply only to full tickets by default
  full_tickets = models.Ticket.public_objects.filter(type='full')
  data = request.POST['data'].split('\n')

  for entry in data:
    entry = entry.strip()
    if not entry:
      continue
    entry_split = entry.split(',', 2)
    if len(entry_split) != 3:
      response.write('bad data: %s<br />\n' % entry)
      continue

    entry_dict = {
      'name': entry_split[0],
      'price_modifier': float(entry_split[1]),
      'description': entry_split[2],
    }
    form = forms.MassAddPromoForm(entry_dict)
    if not form.is_valid():
      response.write('bad entry: %s<br />\n' % entry)
      continue
    promo = form.save(commit=False)
    promo.active = True
    promo.save()
    form.save_m2m()

    for ticket in full_tickets:
      promo.applies_to.add(ticket)
    response.write('Added %s<br />\n' % entry)

  response.write('</body></html>')
  return response


@login_required
def ClearBadOrder(request):
  if not request.user.is_superuser:
    return HttpResponse('')

  try:
    order = models.Order.objects.get(order_num='')
    order.delete()
  except models.Order.DoesNotExist:
    return HttpResponse('Not Found')

  return HttpResponse('Done')
