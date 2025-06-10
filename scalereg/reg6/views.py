# Create your views here.

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.shortcuts import render
from scalereg.common import utils
from scalereg.reg6 import forms
from scalereg.reg6 import models
from scalereg.reg6 import validators
from scalereg.sponsorship import views as sponsorship_views
import datetime
import re
import sys
import urllib

STEPS_TOTAL = 7

REGISTRATION_PAYMENT_COOKIE = 'payment'

PGP_KEY_QUESTION_INDEX_OFFSET = 3

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


def ShouldRedirectPostToSponsorship(post):
  return 'USER3' in post and post['USER3'] == 'SPONSORSHIP'


def IsPGPEnabled():
  return (settings.SCALEREG_PGP_QUESTION_ID_START >= 0 and
          settings.SCALEREG_PGP_MAX_KEYS > 0)


def GetPGPTotalQuestions():
  return settings.SCALEREG_PGP_MAX_KEYS * PGP_KEY_QUESTION_INDEX_OFFSET


def GetPGPKeyQuestionOffset(question_number):
  assert IsPGPEnabled()
  assert question_number > 0
  assert question_number <= settings.SCALEREG_PGP_MAX_KEYS
  return (question_number - 1) * PGP_KEY_QUESTION_INDEX_OFFSET


def GetPGPKeyQuestionIndex(question_number):
  offset = GetPGPKeyQuestionOffset(question_number)
  return settings.SCALEREG_PGP_QUESTION_ID_START + offset


def GetPGPText(attendee, qpgp, question_number):
  q_index = GetPGPKeyQuestionOffset(question_number)
  pgp_keys = attendee.answers.filter(question=qpgp[q_index])
  if not pgp_keys:
    return ''
  pgp_sizes = attendee.answers.filter(question=qpgp[q_index + 1])
  pgp_types = attendee.answers.filter(question=qpgp[q_index + 2])
  if not pgp_sizes or not pgp_types:
    return ''
  return '%s,%s%s' % (pgp_keys[0].text, pgp_sizes[0].text, pgp_types[0].text[0])


def ShouldIgnoreKSPItem(item, post_data):
  return (IsPGPEnabled() and
          item.name == settings.SCALEREG_PGP_KSP_ITEM_NAME and
          'no_pgp' in post_data)


def PrintAttendee(attendee, reprint_ids, ksp_ids, qpgp):
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
  parity = 0
  for f in validators.hashAttendee(attendee):
    parity += int(f, 16)
  badge.append(str(parity % 10))
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

  if IsPGPEnabled():
    ksp = attendee.id in ksp_ids
    has_pgp_text = 'NO PGP'
    all_pgp_text = []
    for i in xrange(0, settings.SCALEREG_PGP_MAX_KEYS):
      all_pgp_text.append('NO PGP KEY %d' % (i + 1))
    if ksp:
      has_pgp_text = 'PGP'
      for i in xrange(0, settings.SCALEREG_PGP_MAX_KEYS):
        pgp_text = GetPGPText(attendee, qpgp, i + 1)
        if pgp_text:
          all_pgp_text[i] = pgp_text
    badge.append(has_pgp_text)
    badge.extend(all_pgp_text)

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
      is_item_available = item in avail_items;
      if ShouldIgnoreKSPItem(item, post):
        is_item_available = False
      if is_item_available:
        selected_items.append(item)
  ApplyPromoToItems(promo, selected_items)
  return selected_items


def FindRelevantQuestions(model_type, ticket, selected_items):
  if model_type == models.ListQuestion:
    type_value = 'list'
  elif model_type == models.TextQuestion:
    type_value = 'text'
  else:
    raise ValueError

  questions = []
  all_active_questions = model_type.objects.filter(active=True)
  for q in all_active_questions:
    q.type_value = type_value
    if q.applies_to_all or ticket in q.applies_to_tickets.all():
      questions.append(q)
    else:
      relevant_items = q.applies_to_items.all()
      for item in selected_items:
        if item in relevant_items:
          questions.append(q)
          break
  return questions


def IdCompare(x, y):
  if x.id == y.id:
    return 0
  if x.id < y.id:
    return -1
  return 1


def FindAllRelevantQuestions(ticket, selected_items):
  list_questions = FindRelevantQuestions(models.ListQuestion, ticket,
                                         selected_items)
  text_questions = FindRelevantQuestions(models.TextQuestion, ticket,
                                         selected_items)
  questions = list_questions + text_questions
  questions.sort(cmp=IdCompare)
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

  if attendee and attendee.email != attendee_email.strip():
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


def UpgradeAttendee(upgrade, new_order, at_kiosk):
  upgrade.new_order = new_order
  upgrade.valid = True
  upgrade.save()

  person = upgrade.attendee
  person.badge_type = upgrade.new_badge_type
  person.order = new_order
  if at_kiosk:
    person.checked_in = True
  person.save()
  person.ordered_items.clear()
  for s in upgrade.new_ordered_items.all():
    person.ordered_items.add(s)
  if at_kiosk:
    try:
      reprint = models.Reprint.objects.get(attendee=person)
    except:
      reprint = models.Reprint()
      reprint.attendee = person
      reprint.count = 0
    reprint.count += 1
    reprint.save()
  else:
    NotifyAttendee(person)


def NotifyAttendee(person):
  if not settings.SCALEREG_SEND_MAIL:
    return

  if (not person.email or person.email.endswith('@example.com') or
      person.email.endswith('@none.com') or '@' not in person.email):
    return

  try:
    send_mail('SCALE Registration',
              '''Thank you for registering for SCALE.
The details of your registration are included below.

Please note the Express Check-In Code below, which will allow you to
speed up your check in and badge pick up on site.

First Name: %s
Last Name: %s
Email: %s
Zip Code: %s

Badge Type: %s
Express Check-In Code: %s
''' % \
              (person.first_name, person.last_name, person.email, person.zip,
               person.badge_type.description, person.checkin_code()),
              settings.SCALEREG_EMAIL,
              [person.email])
  except:
    pass


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


def GetUserAgentFromRequest(request):
  if 'HTTP_USER_AGENT' not in request.META:
    return ''
  return request.META['HTTP_USER_AGENT']


def RecordAttendeeAgent(attendee, user_agent):
  if settings.SCALEREG_KIOSK_AGENT_SECRET not in user_agent:
    return

  try:
    kiosk_idx = user_agent.find(settings.SCALEREG_KIOSK_AGENT_SECRET) + \
        len(settings.SCALEREG_KIOSK_AGENT_SECRET)
    truncated_user_agent = user_agent[kiosk_idx:]
    kiosk_agents = models.KioskAgent.objects.filter(attendee=attendee)
    if kiosk_agents:
      kiosk_agents[0].agent = truncated_user_agent
      kiosk_agents[0].save()
    else:
      agent = models.KioskAgent()
      agent.attendee = attendee
      agent.agent = truncated_user_agent
      agent.save()
  except Exception as inst: # FIXME catch the specific db exceptions
    pass


def DoCheckIn(request, attendee):
  try:
    RecordAttendeeAgent(attendee, GetUserAgentFromRequest(request))
    attendee.checked_in = True
    attendee.save()
  except:
    return HttpResponseServerError('We encountered a problem with your checkin')

  return scale_render_to_response(request, 'reg6/reg_finish_checkin.html',
    {'title': 'Checked In',
     'attendee': attendee,
    })


def IsRequestFromKiosk(request):
  return ('kiosk' in request.session and
          settings.SCALEREG_KIOSK_AGENT_SECRET in
          GetUserAgentFromRequest(request))


def IsRequestFromKioskOrOutside(request):
  if 'kiosk' not in request.session:
    return True
  return IsRequestFromKiosk(request)


def scale_render_to_response(request, template, vars):
  if 'kiosk' in request.session:
    vars['kiosk'] = True
  return render(request, template, vars)


def index(request):
  if not IsRequestFromKioskOrOutside(request):
    return HttpResponse()

  avail_tickets = [
      ticket for ticket in
      models.Ticket.public_objects.order_by('priority', 'description')
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

    user_agent = GetUserAgentFromRequest(request)
    if settings.SCALEREG_KIOSK_AGENT_SECRET not in user_agent:
      return render(request, 'reg6/reg_kiosk.html')

    kiosk_idx = user_agent.find(settings.SCALEREG_KIOSK_AGENT_SECRET) + \
        len(settings.SCALEREG_KIOSK_AGENT_SECRET)
    truncated_user_agent = user_agent[kiosk_idx:]
    return render(request, 'reg6/reg_kiosk.html', {'agent': truncated_user_agent})

  return scale_render_to_response(request, 'reg6/reg_index.html',
    {'title': 'Registration',
     'tickets': avail_tickets,
     'promo': promo_name,
     'step': 1,
     'steps_total': STEPS_TOTAL,
    })


def kiosk_index(request):
  if request.method == 'POST':
    return render(request, 'reg6/reg_kiosk_clear.html', {})

  if 'clear' in request.GET:
    if 'attendee' in request.session:
      request.session.pop('attendee')
    if REGISTRATION_PAYMENT_COOKIE in request.session:
      request.session.pop(REGISTRATION_PAYMENT_COOKIE)
    request.session['kiosk'] = True
    return render(request, 'reg6/reg_kiosk.html')
  return render(request, 'reg6/reg_kiosk_clear.html', {})


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

  questions = FindAllRelevantQuestions(ticket, selected_items)

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

      # sanitize input
      new_attendee.first_name = new_attendee.first_name.strip();
      new_attendee.last_name = new_attendee.last_name.strip();
      new_attendee.title = new_attendee.title.strip();
      new_attendee.org = new_attendee.org.strip();
      new_attendee.email = new_attendee.email.strip();
      new_attendee.zip = new_attendee.zip.strip();
      new_attendee.phone = new_attendee.phone.strip();

      # add badge type
      new_attendee.badge_type = ticket
      # add promo
      new_attendee.promo = promo_in_use

      # save attendee
      new_attendee.save()
      form.save_m2m()

      # add ordered items
      for s in selected_items:
        if ShouldIgnoreKSPItem(s, request.POST):
          continue
        new_attendee.ordered_items.add(s)
      # add survey answers
      for q in questions:
        if q.type_value == 'list':
          key = 'lq%d' % q.id
          if key in request.POST and request.POST[key]:
            try:
              ans = models.Answer.objects.get(id=request.POST[key])
              new_attendee.answers.add(ans)
            except models.Answer.DoesNotExist:
              continue
        else:
          key = 'tq%d' % q.id
          if key in request.POST and request.POST[key]:
            answer = models.TextAnswer()
            answer.question = q
            answer.text = request.POST[key][:q.max_length]
            answer.save()
            new_attendee.answers.add(answer)

      request.session['attendee'] = new_attendee.id

      # add attendee to order
      if REGISTRATION_PAYMENT_COOKIE not in request.session:
        request.session[REGISTRATION_PAYMENT_COOKIE] = [new_attendee.id]
      else:
        request.session[REGISTRATION_PAYMENT_COOKIE].append(new_attendee.id)

      return HttpResponseRedirect('/reg6/registered_attendee/')

  pgp_questions = []
  pgp_question1_index = -1
  pgp_question2_index = -1
  if IsPGPEnabled():
    pgp_question1_index = GetPGPKeyQuestionIndex(1)
    pgp_question2_index = pgp_question1_index + PGP_KEY_QUESTION_INDEX_OFFSET

    q_range = range(len(questions))
    q_range.reverse()
    pgp_question_start = pgp_question1_index
    pgp_question_end = pgp_question_start + GetPGPTotalQuestions()
    for i in q_range:
      q_id = questions[i].id
      if q_id >= pgp_question_start and q_id < pgp_question_end:
        pgp_questions.append(questions.pop(i))
    pgp_questions.reverse()

  return scale_render_to_response(request, 'reg6/reg_attendee.html',
    {'title': 'Register Attendee',
     'ticket': ticket,
     'promo': promo_name,
     'items': selected_items,
     'offset_item': offset_item,
     'total': total,
     'pgp_num_keys': settings.SCALEREG_PGP_MAX_KEYS,
     'pgp_question1_index': pgp_question1_index,
     'pgp_question2_index': pgp_question2_index,
     'pgp_questions': pgp_questions,
     'questions': questions,
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

      search_email = request.POST['email'].strip()
      if attendee_id in all_attendees:
        new_attendee = None
      elif new_attendee and new_attendee.email == search_email:
        if not new_attendee.valid:
          if new_attendee not in all_attendees:
            all_attendees.append(attendee_id)
        else:
          paid_attendee = new_attendee
          new_attendee = None
      else:
        bad_attendee = [request.POST['id'], search_email]
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
  user_agent = GetUserAgentFromRequest(request)
  for person in all_attendees_data:
    if person.badge_type in attendees_by_ticket:
      attendees_by_ticket[person.badge_type] += 1
    else:
      attendees_by_ticket[person.badge_type] = 1
    RecordAttendeeAgent(person, user_agent)
  tickets_soldout = []
  for ticket, num_to_buy in attendees_by_ticket.items():
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
    except Exception as inst: # FIXME catch the specific db exceptions
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
     'payflow_url': settings.SCALEREG_PAYFLOW_URL,
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

  if ShouldRedirectPostToSponsorship(request.POST):
    return sponsorship_views.Sale(request)

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
  if 'AUTHCODE' not in request.POST:
    ScaleDebug('missing authcode')
    return HttpResponse('missing authcode')

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
  except Exception as inst: # FIXME catch the specific db exceptions
    ScaleDebug('cannot save order')
    print(inst)
    ScaleDebug(inst.args)
    ScaleDebug(inst)
    return HttpResponseServerError('cannot save order')

  at_kiosk = request.POST['USER2'] == 'Y'
  if upgrade:
    UpgradeAttendee(upgrade, order, at_kiosk)
  else:
    for person in all_attendees_data:
      person.valid = True
      person.order = order
      if at_kiosk:
        person.checked_in = True
      person.save()
      if not at_kiosk:
        NotifyAttendee(person)

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

  if ShouldRedirectPostToSponsorship(request.POST):
    return sponsorship_views.FinishPayment(request)

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
    ScaleDebug('Your registration order cannot be found')
    return HttpResponseServerError('Your registration order cannot be found')

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
  except Exception as inst: # FIXME catch the specific db exceptions
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
    except Exception as inst: # FIXME catch the specific db exceptions
      order_tries += 1
      if order_tries > 10:
        return scale_render_to_response(request, 'reg6/reg_error.html',
          {'title': 'Registration Problem',
           'error_message': 'We cannot generate an order ID for you.',
          })

  RecordAttendeeAgent(attendee, GetUserAgentFromRequest(request))
  return scale_render_to_response(request, 'reg6/reg_non_free_upgrade.html',
    {'title': 'Registration Upgrade',
     'attendee': attendee,
     'order': order_num,
     'payflow_url': settings.SCALEREG_PAYFLOW_URL,
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
  except Exception as inst: # FIXME catch the specific db exceptions
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
    except Exception as inst: # FIXME catch the specific db exceptions
      order_tries += 1
      if order_tries > 10:
        return scale_render_to_response(request, 'reg6/reg_error.html',
          {'title': 'Registration Problem',
           'error_message': 'We cannot generate an order ID for you.',
          })

  at_kiosk = 'USER2' in request.POST and request.POST['USER2'] == 'Y'
  UpgradeAttendee(upgrade, order, at_kiosk)
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
  if request.POST['zip'].strip() and request.POST['email'].strip():
    attendees = models.Attendee.objects.filter(zip=request.POST['zip'].strip(),
        email=request.POST['email'].strip())

  return scale_render_to_response(request, 'reg6/reg_lookup.html',
    {'title': 'Registration Lookup',
     'attendees': attendees,
     'email': request.POST['email'],
     'zip': request.POST['zip'],
     'search': 1,
    })


def CheckIn(request):
  if not IsRequestFromKiosk(request):
    return HttpResponse()

  if request.method == 'GET':
    if 'kiosk' in request.GET:
      request.session['kiosk'] = True
      return render(request, 'reg6/reg_kiosk.html')

    return scale_render_to_response(request, 'reg6/reg_checkin.html',
      {'title': 'Check In',
      })

  if 'express' in request.POST:
    code = request.POST['express'].lower()
    success = len(code) == 10
    if success:
      id_str = code[:4]
      try:
        attendee_id = int(id_str)
        attendee = models.Attendee.objects.get(id=attendee_id)
      except:
        success = False

    if success:
      success = attendee.checkin_code() == code

    if success:
      if attendee.checked_in:
        return scale_render_to_response(request, 'reg6/reg_checkin.html',
          {'title': 'Check In',
           'reprint': True,
          })
      return DoCheckIn(request, attendee)
    return scale_render_to_response(request, 'reg6/reg_checkin.html',
      {'title': 'Check In',
       'express_code': code,
       'express_fail': True,
      })

  attendees = []
  attendees_email = []
  attendees_zip = []
  if request.POST['zip'].strip() and request.POST['email'].strip():
    attendees = models.Attendee.objects.filter(valid=True, checked_in=False,
        zip=request.POST['zip'].strip(),
        email=request.POST['email'].strip())
  if not attendees:
    if request.POST['first'].strip() and request.POST['last'].strip():
      attendees = models.Attendee.objects.filter(valid=True, checked_in=False,
          first_name=request.POST['first'].strip(),
          last_name=request.POST['last'].strip())
    if attendees:
      has_email_or_zip = False
      if request.POST['email'].strip():
        has_email_or_zip = True
        attendees_email = attendees.filter(email=request.POST['email'].strip())
      if request.POST['zip'].strip():
        has_email_or_zip = True
        attendees_zip = attendees.filter(zip=request.POST['zip'].strip())
      if attendees_email:
        attendees = attendees_email
      elif attendees_zip:
        attendees = attendees_zip
      if not has_email_or_zip:
        attendees = []

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
  if not IsRequestFromKiosk(request):
    return HttpResponse()

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

  return DoCheckIn(request, attendee)


def RedeemCoupon(request):
  PAYMENT_STEP = 7

  if request.method != 'POST':
    return HttpResponseRedirect('/reg6/')
  r = CheckReferrer(request.META, '/reg6/payment/')
  if r:
    return r

  required_vars = [
    'code',
    'is_kiosk',
    'order',
  ]

  r = CheckVars(request, required_vars, [])
  if r:
    return r

  try:
    coupon = models.Coupon.objects.get(code=request.POST['code'].strip())
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

  at_kiosk = 'USER2' in request.POST and request.POST['USER2'] == 'Y'
  for person in all_attendees_data:
    # remove non-free addon items
    for item in person.ordered_items.all():
      if item.price > 0:
        person.ordered_items.remove(item)
    person.valid = True
    person.order = coupon.order
    person.badge_type = coupon.badge_type
    person.promo = None
    if request.POST['is_kiosk'] == 'Y':
      person.checked_in = True
    person.save()
    if not at_kiosk:
      NotifyAttendee(person)

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
  bad_order_nums = [ x.order_num for x in models.TempOrder.objects.all() ]
  bad_order_nums += [ x.order_num for x in models.Order.objects.all() ]
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
  except Exception as inst: # FIXME catch the specific db exceptions
    order.delete()
    return HttpResponseServerError('error saving the coupon')

  try:
    order.valid = True
    order.save()
  except Exception as inst: # FIXME catch the specific db exceptions
    order.delete()
    coupon.delete()
    return HttpResponseServerError('error saving the order')

  return HttpResponse('Success! Your coupon code is: %s' % order.order_num)


@login_required
def CheckedIn(request):
  if not request.user.is_superuser:
    return HttpResponse('')

  attendees = models.Attendee.objects.filter(valid=True)
  attendees = attendees.filter(checked_in=True)
  if request.method == 'GET' and 'idsonly' in request.GET:
    return HttpResponse('\n'.join([str(f.id) for f in attendees]),
                        content_type='text/plain')

  reprint_ids = [reprint.attendee.id
                 for reprint in models.Reprint.objects.all()]
  ksp_ids = []
  qpgp = []
  if IsPGPEnabled():
    ksp_attendees = models.Item.objects.get(
        name=settings.SCALEREG_PGP_KSP_ITEM_NAME).attendee_set.all()
    ksp_ids = [attendee.id for attendee in ksp_attendees]
    num_questions = GetPGPTotalQuestions()
    base_question_id = GetPGPKeyQuestionIndex(1)
    for i in xrange(base_question_id, base_question_id + num_questions):
      qpgp.append(models.Question.objects.get(id=i))

  if request.method == 'POST':
    # Only get requested attendees instead of all checked in attendees.
    attendee_ids = []
    if 'attendees' in request.POST and request.POST['attendees']:
      attendee_ids = [int(x) for x in request.POST['attendees'].split(',')]
    attendee_ids = set(attendee_ids + reprint_ids)
    checked_in_attendees = []
    for attendee_id in attendee_ids:
      try:
        attendee = attendees.get(id=attendee_id)
        checked_in_attendees.append(attendee)
      except:
        pass
    attendees = checked_in_attendees

  return HttpResponse(
      '\n'.join([PrintAttendee(f, reprint_ids, ksp_ids, qpgp)
                 for f in attendees]),
      content_type='text/plain')


@login_required
def MassAddAttendee(request):
  if not request.user.is_superuser:
    return HttpResponse('')
  if request.method == 'GET':
    response = HttpResponse()
    response.write('<html><head></head><body><form method="post">')
    response.write('<p>first_name,last_name,title,org,email,zip,phone,order_number,ticket_code</p>')
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
      'email': entry_split[4],
      'zip': entry_split[5],
      'phone': entry_split[6],
      'badge_type': ticket,
    }
    form = forms.MassAddAttendeeForm(entry_dict)
    if not form.is_valid():
      response.write('bad entry: %s, reason: %s<br />\n' % (entry, form.errors))
      continue
    attendee = form.save(commit=False)

    # sanitize input
    attendee.first_name = attendee.first_name.strip();
    attendee.last_name = attendee.last_name.strip();
    attendee.title = attendee.title.strip();
    attendee.org = attendee.org.strip();
    attendee.email = attendee.email.strip();
    attendee.zip = attendee.zip.strip();
    attendee.phone = attendee.phone.strip();

    attendee.valid = True
    attendee.checked_in = False
    attendee.can_email = False
    attendee.order = order
    attendee.badge_type = ticket
    attendee.save()
    form.save_m2m()
    NotifyAttendee(attendee)
    response.write('Added %s<br />\n' % entry)

  response.write('</body></html>')
  return response


@login_required
def MassAddCoupon(request):
  if not request.user.is_superuser:
    return HttpResponse('')
  if request.method == 'GET':
    response = HttpResponse()
    response.write('<html><head></head><body><form method="post">')
    response.write('<p>name addr city state zip email type max_att</p>')
    response.write('<textarea name="data" rows="25" cols="80"></textarea>')
    response.write('<br /><input type="submit" /></form>')
    response.write('</body></html>')
    return response

  if 'data' not in request.POST:
    return HttpResponse('No Data')

  # FIXME Add this to the Ticket model?
  ticket_types = {
    'expo': 'invitee',
    'full': 'invitee',
    'press': 'press',
    'speaker': 'speaker',
    'exhibitor': 'exhibitor',
    'friday': 'invitee',
  }

  response = HttpResponse()
  response.write('<html><head></head><body>')

  data = request.POST['data'].split('\n')
  entries = []
  for entry in data:
    entry = entry.strip()
    if not entry:
      return HttpResponse('Bad data: blank line found')
    entries.append(entry)

  if len(entries) % 8 != 0:
    return HttpResponse('Bad data: wrong number of lines')

  index = 0
  while index < len(entries):
    name = entries[index]
    addr = entries[index + 1]
    city = entries[index + 2]
    state = entries[index + 3]
    zip_code = entries[index + 4]
    email = entries[index + 5]
    badge_type = entries[index + 6]
    max_attendees = entries[index + 7]
    index += 8

    try:
      ticket = models.Ticket.objects.get(name=badge_type)
    except models.Ticket.DoesNotExist:
      response.write('bad entry: no such ticket: ')
      response.write('%s - %s<br />\n' % (name, badge_type))
      continue

    bad_order_nums = [ x.order_num for x in models.TempOrder.objects.all() ]
    bad_order_nums += [ x.order_num for x in models.Order.objects.all() ]
    order_num = GenerateOrderID(bad_order_nums)
    order = models.Order(order_num=order_num,
        valid=False,
        name=name,
        address=addr,
        city=city,
        state=state,
        zip=zip_code,
        email=email,
        amount=0,
        payment_type=ticket_types[ticket.type],
    )
    try:
      order.save()
    except Exception as inst: # FIXME catch the specific db exceptions
      order.delete()
      response.write('error while saving order for: %s' % name)
      break

    coupon = models.Coupon(code=order.order_num,
        badge_type = ticket,
        order = order,
        used = False,
        max_attendees = max_attendees,
    )
    try:
      coupon.save()
    except Exception as inst: # FIXME catch the specific db exceptions
      order.delete()
      response.write('error while saving coupon for: %s' % name)
      break

    try:
      order.valid = True
      order.save()
    except Exception as inst: # FIXME catch the specific db exceptions
      order.delete()
      coupon.delete()
      response.write('error while modifying order for: %s' % name)
      break

    response.write('Added %s - %s<br />\n' % (name, order.order_num))

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


@login_required
def ScannedBadge(request):
  if request.method != 'GET':
    return HttpResponse('Post?')

  response = ''
  color = 'red'
  if 'CODE' in request.GET and 'SIZE' in request.GET:
    code = request.GET['CODE']
    size = request.GET['SIZE']
    code_split = urllib.unquote(code).split('~')
    try:
      attendee_id = int(code_split[0][:-1])
      validators.isValidScannedBadge(code_split[0], None)
    except:
      response = 'Invalid barcode'

    if not response:
      try:
        attendee = models.Attendee.objects.get(id=attendee_id)
        if not attendee.checked_in:
          response = 'Attendee not checked in'
      except:
        response = 'Invalid attendee'

    if not response:
      badges = models.ScannedBadge.objects.filter(number=attendee_id)
      if badges:
        response = 'Badge already scanned: %d' % attendee_id
        color = 'orange'

    if not response:
      try:
        badge = models.ScannedBadge()
        badge.number = attendee_id
        badge.size = size
        badge.save()
        response = 'Scanned %d' % attendee_id
        color = 'green'
      except:
        response = 'Database error'

  returl = 'https://%s/reg6/scanned_badge/?CODE={CODE}' % request.get_host()
  url = 'zxing://scan/?ret=%s' % urllib.quote_plus(returl)
  return render(request, 'reg6/scanned_badge.html',
    {'color': color,
     'response': response,
     'url': url,
    })
