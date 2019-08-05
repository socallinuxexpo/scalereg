# Create your views here.

from __future__ import division
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.db.models import BooleanField
from django.db.models.base import ModelBase
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import loader
from django.views.generic.list import ListView as django_object_list
from scalereg.common.utils import services_perm_checker
from scalereg.reg6 import models
import datetime
import inspect
import re
import string

PGP_KEY_QUESTION_INDEX_OFFSET = 3

class Filter:
  def __init__(self, name):
    self.name = name
    self.items = {}
    self.selected = -1

  def get_items(self):
    items = self.items.items()
    items.sort()
    return [v[1] for v in items]


class Item:
  def __init__(self, name, value):
    self.name = name
    self.value = value


class SurveyQuestion:
  def __init__(self, name):
    self.name = name
    self.answers = []


class Count:
  def __init__(self, name):
    self.name = name
    self.count = 0
    self.percentage = 0

  def CalcPercentage(self, total):
    total = float(total)
    if total > 0:
      self.percentage = 100 * round(self.count / total, 3)


class Attendee(Count):
  def __init__(self, name):
    Count.__init__(self, name)
    self.checked_in = 0


def paranoid_strip(value):
  valid_chars = string.ascii_letters + string.digits + '_'
  for c in value:
    if c not in valid_chars:
      raise ValueError
  return value


def get_model_list(user):
  perms = user.get_all_permissions()
  tables = [m[0] for m in inspect.getmembers(models, inspect.isclass)
            if type(m[1]) == ModelBase and admin.site.is_registered(m[1])]
  model_list = []
  for t in tables:
    if user.is_superuser or 'reg6.view_%s' % t.lower() in perms:
      def foo(match):
        return '%s %s' % match.groups()
      name = re.sub('([a-z])([A-Z])', foo, t)
      if not name.endswith('s'):
        name = name + 's'
      url = t.lower() + '/'
      model_list.append({'name': name, 'url': url})
  return model_list

@login_required
def index(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  model_list = get_model_list(request.user)
  model_list.insert(0, {'name': 'Dashboard', 'url': 'dashboard/'})
  model_list.insert(1, {'name': 'Scale-announce Subscribers',
                        'url': 'announce_subscribers/'})
  model_list.insert(2, {'name': 'Coupon Usage', 'url': 'coupon_usage/'})

  return render_to_response('reports/index.html',
    {'user': request.user, 'title': 'Reports', 'model_list': model_list})

@login_required
def object_list(request, queryset, paginate_by=None, page=None,
  allow_empty=False, template_name=None, template_loader=loader,
  extra_context=None, context_processors=None, template_object_name='object',
  mimetype=None):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  model_list = get_model_list(request.user)
  can_access = False
  for f in model_list:
    if re.compile('/reports/%s.*' % f['url']).match(request.path):
      can_access = True
      break
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  all_fields = [f.name for f in queryset.model._meta.fields]

  if not extra_context:
    extra_context = {}

  if 'admin_user' not in extra_context:
    if request.user.is_staff:
      extra_context['admin_user'] = True

  if 'title' not in extra_context:
    extra_context['title'] = queryset.model._meta.verbose_name_plural.title()

  if 'field_list' not in extra_context:
    extra_context['field_list'] = all_fields

  filter_select = {}
  for i in xrange(len(all_fields)):
    name = all_fields[i]
    filter = Filter(name)
    field_type = type(queryset.model._meta.fields[i])
    if field_type == BooleanField:
      filter.items[-1] = (Item('All', -1))
      filter.items[0] = (Item('False', 0))
      filter.items[1] = (Item('True', 1))
    else:
      continue
    filter_select[name] = filter

  urlparts = []
  for f in request.GET:
    if not f.startswith('filter__'):
      continue
    urlparts.append('%s=%s&' % (f, request.GET[f]))
    name = f[8:]
    field_type = type(queryset.model._meta.fields[all_fields.index(name)])
    if name and name in filter_select:
      if field_type == BooleanField:
        filter = filter_select[name]
        try:
          value = int(request.GET[f])
        except ValueError:
          continue
        if value in filter.items and value != -1:
          filter.selected = value
          query_string = '%s = %%s' % paranoid_strip(name)
          queryset = queryset.extra(where=[query_string], params=[value])
  extra_context['filter_select'] = filter_select.values()
  extra_context['urlpart'] = ''.join([part for part in urlparts])

  extra_context['numbers'] = queryset.count()

  return django_object_list(request, queryset, paginate_by, page, allow_empty,
    template_name, template_loader, extra_context, context_processors,
    template_object_name, mimetype)

@login_required
def dashboard(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  today = datetime.date.today()
  days_30 = today - datetime.timedelta(days=30)
  days_7 = today - datetime.timedelta(days=7)

  orders_data = {}
  orders_data['by_type'] = []
  orders = models.Order.objects.filter(valid=True)
  orders_data['numbers'] = orders.count()
  orders_data['revenue'] = sum([x.amount for x in orders])
  orders_30 = orders.filter(date__gt = days_30)
  orders_data['numbers_30'] = orders_30.count()
  orders_data['revenue_30'] = sum([x.amount for x in orders_30])
  orders_7 = orders_30.filter(date__gt = days_7)
  orders_data['numbers_7'] = orders_7.count()
  orders_data['revenue_7'] = sum([x.amount for x in orders_7])
  for pt in models.PAYMENT_CHOICES:
    orders_pt = orders.filter(payment_type=pt[0])
    data_pt = {}
    data_pt['name'] = pt[1]
    data_pt['numbers'] = orders_pt.count()
    data_pt['revenue'] = sum([x.amount for x in orders_pt])
    orders_pt_30 = orders_pt.filter(date__gt = days_30)
    data_pt['numbers_30'] = orders_pt_30.count()
    orders_pt_7 = orders_pt_30.filter(date__gt = days_7)
    data_pt['numbers_7'] = orders_pt_7.count()
    orders_data['by_type'].append(data_pt)

  attendees_data = {}
  attendees = models.Attendee.objects.filter(valid=True)
  num_attendees = attendees.count()
  attendees_data['numbers'] = num_attendees
  attendees_data['checked_in'] = attendees.filter(checked_in=True).count()

  type_attendees_data = {}
  ticket_attendees_data = {}
  for att in attendees:
    att_type = att.badge_type.type
    if att_type not in type_attendees_data:
      type_attendees_data[att_type] = Attendee(att_type)
    type_attendees_data[att_type].count += 1
    if att.checked_in:
      type_attendees_data[att_type].checked_in += 1

    att_ticket = att.badge_type.name
    if att_ticket not in ticket_attendees_data:
      ticket_attendees_data[att_ticket] = Count(att_ticket)
    ticket_attendees_data[att_ticket].count += 1
  type_attendees_data = type_attendees_data.items()
  type_attendees_data.sort()
  type_attendees_data = [v[1] for v in type_attendees_data]
  for t in type_attendees_data:
    t.CalcPercentage(num_attendees)
  ticket_attendees_data = ticket_attendees_data.items()
  ticket_attendees_data.sort()
  ticket_attendees_data = [v[1] for v in ticket_attendees_data]
  for t in ticket_attendees_data:
    t.CalcPercentage(num_attendees)

  promo_attendees_data = {}
  promo_attendees_data[None] = Count('None')
  for att in attendees:
    if att.promo:
      promo = att.promo.name
    else:
      promo = None
    if promo not in promo_attendees_data:
      promo_attendees_data[promo] = Count(promo)
    promo_attendees_data[promo].count += 1
  promo_attendees_data = promo_attendees_data.items()
  promo_attendees_data.sort()
  promo_attendees_data = [v[1] for v in promo_attendees_data]
  for p in promo_attendees_data:
    p.CalcPercentage(num_attendees)

  zipcode_orders_data = {}
  for x in orders:
    if x.zip not in zipcode_orders_data:
      zipcode_orders_data[x.zip] = Count(x.zip)
    zipcode_orders_data[x.zip].count += 1
  zipcode_orders_data = zipcode_orders_data.items()
  zipcode_orders_data.sort()
  zipcode_orders_data = [v[1] for v in zipcode_orders_data]
  for zip in zipcode_orders_data:
    zip.CalcPercentage(orders_data['numbers'])

  zipcode_attendees_data = {}
  for att in attendees:
    if att.zip not in zipcode_attendees_data:
      zipcode_attendees_data[att.zip] = Count(att.zip)
    zipcode_attendees_data[att.zip].count += 1
  zipcode_attendees_data = zipcode_attendees_data.items()
  zipcode_attendees_data.sort()
  zipcode_attendees_data = [v[1] for v in zipcode_attendees_data]
  for zip in zipcode_attendees_data:
    zip.CalcPercentage(num_attendees)

  questions_data = []
  questions = models.Question.objects.all()

  all_answers = {}
  for q in questions:
    all_answers[q.text] = {}
  for ans in models.Answer.objects.all():
    all_answers[ans.question.text][ans.text] = Count(ans.text)

  for att in attendees:
    for ans in att.answers.all():
      all_answers[ans.question.text][ans.text].count += 1

  for q in questions:
    possible_answers = q.answer_set.all()
    q_data = SurveyQuestion(q.text)
    for ans in possible_answers:
      a_data = all_answers[q.text][ans.text]
      a_data.CalcPercentage(num_attendees)
      q_data.answers.append(a_data)
    a_data = Count('No Answer')
    a_data.count = num_attendees - sum([x.count for x in q_data.answers])
    a_data.CalcPercentage(num_attendees)
    q_data.answers.append(a_data)
    questions_data.append(q_data)

  addon_attendees_data = {}
  unique_addon_attendees_data = Count('Unique')
  for att in attendees:
    if len(att.ordered_items.all()) > 0:
      unique_addon_attendees_data.count += 1
    for add in att.ordered_items.all():
      if add.name not in addon_attendees_data:
        addon_attendees_data[add.name] = Count(add.name)
      addon_attendees_data[add.name].count += 1
  addon_attendees_data = addon_attendees_data.items()
  addon_attendees_data.sort()
  addon_attendees_data = [v[1] for v in addon_attendees_data]
  for zip in addon_attendees_data:
    zip.CalcPercentage(num_attendees)
  unique_addon_attendees_data.CalcPercentage(num_attendees)

  return render_to_response('reports/dashboard.html',
    {'title': 'Dashboard',
     'addon_attendees': addon_attendees_data,
     'attendees': attendees_data,
     'orders': orders_data,
     'promo_attendees': promo_attendees_data,
     'questions': questions_data,
     'ticket_attendees': ticket_attendees_data,
     'type_attendees': type_attendees_data,
     'unique_addon_attendees': unique_addon_attendees_data,
     'zipcode_attendees': zipcode_attendees_data,
     'zipcode_orders': zipcode_orders_data,
    })

@login_required
def reg6log(request):
  if not request.user.is_superuser:
    return HttpResponseRedirect('/accounts/profile/')

  response = HttpResponse(content_type='text/plain')
  try:
    f = open('/tmp/scale_reg.log')
    response.write(f.read())
    f.close()
  except:
    response.write('error reading log files\n')
  return response

@login_required
def badorder(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  response = HttpResponse(content_type='text/plain')
  response.write('Bad orders:\n')
  order_invitees = models.Order.objects.filter(payment_type='invitee')
  order_exhibitors = models.Order.objects.filter(payment_type='exhibitor')
  order_speakers = models.Order.objects.filter(payment_type='speaker')
  order_press = models.Order.objects.filter(payment_type='press')
  free_orders = order_invitees|order_exhibitors|order_speakers|order_press
  for f in free_orders.filter(amount__gt=0):
    response.write('Free Order costs money: %s %s\n' % (f.order_num, f.name))

  bad_orders = models.Order.objects.filter(valid=False)
  for g in bad_orders:
    for f in g.attendee_set.all():
      if f.valid:
        response.write('Invalid Order: %d %s %s\n' % (f.id, f.first_name, f.last_name))

  valid_orders = models.Order.objects.filter(valid=True)
  order_verisign = valid_orders.filter(payment_type='verisign')
  order_google = valid_orders.filter(payment_type='google')
  order_cash = valid_orders.filter(payment_type='cash')
  paid_orders = order_verisign|order_google|order_cash
  valid_upgrades = models.Upgrade.objects.filter(valid=True)
  for f in paid_orders:
    if f.attendee_set.count() == 0 and not valid_upgrades.filter(old_order=f):
      response.write('Empty Order: %s %s\n' % (f.order_num, f.name))
  for f in paid_orders.filter(amount__lte=0):
    response.write('Paid Order with $0 cost: %s %s\n' % (f.order_num, f.name))

  attendees = models.Attendee.objects.filter(valid=True)
  no_order = attendees.filter(order__isnull=True)
  for f in no_order:
    response.write('No order: %d %s %s\n' % (f.id, f.first_name, f.last_name))

  return response

@login_required
def getleads(request):
  if not request.user.is_superuser:
    return HttpResponse('')
  if request.method == 'GET':
    response = HttpResponse()
    response.write('<html><head></head><body><form method="post">')
    response.write('<textarea name="data" rows="25" cols="80"></textarea>')
    response.write('<br /><input type="submit" /></form>')
    response.write('</body></html>')
    return response

  if 'data' not in request.POST:
    return HttpResponse('No Data')

  response = HttpResponse(content_type='text/plain')
  response.write('Salutation,First Name,Last Name,Title,Company,Phone,Email\n')

  data = request.POST['data'].split('\n')
  for entry in data:
    entry = entry.strip()
    if not entry:
      continue
    try:
      entry_int = int(entry)
    except ValueError:
      continue

    try:
      attendee = models.Attendee.objects.get(id=entry_int)
    except models.Attendee.DoesNotExist:
      response.write('bad attendee number: %s\n' % entry_int)
      continue
    if not attendee.valid:
      response.write('invalid attendee number: %s\n' % entry_int)
      continue
    if not attendee.checked_in:
      response.write('not checked in attendee number: %s\n' % entry_int)
      continue
    for field in (attendee.salutation, attendee.first_name, attendee.last_name,
      attendee.title, attendee.org, attendee.phone, attendee.email):
      if ',' in field:
        response.write('"%s",' % field)
      else:
        response.write('%s,' % field)
    response.write('\n')
  return response


def GetAttendeePGPData(attendee, qindex):
  answers = attendee.answers.filter(question=qindex)
  if answers:
    key = answers[0].text.replace(',', ' ')
  else:
    key = 'no pgp key'
  answers = attendee.answers.filter(question=qindex + 1)
  if answers:
    size = answers[0].text.replace(',', ' ')
  else:
    size = 'no size'
  answers = attendee.answers.filter(question=qindex + 2)
  if answers:
    keytype = answers[0].text.replace(',', ' ')
  else:
    keytype = 'no type'
  return (key, size, keytype)


@login_required
def getpgp(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  response = HttpResponse(content_type='text/plain')

  item = models.Item.objects.get(name=settings.SCALEREG_PGP_KSP_ITEM_NAME)
  for attendee in item.attendee_set.all():
    if attendee.valid:
      valid = 'V'
    else:
      valid = 'I'

    full_name = "%s %s" % (attendee.first_name, attendee.last_name)
    full_name = full_name.replace(',', ' ')
    email = attendee.email.replace(',', ' ')

    qindex = settings.SCALEREG_PGP_QUESTION_ID_START
    (key, size, keytype) = GetAttendeePGPData(attendee, qindex)
    response.write('%s,%d,%s,%s,%s,%s,%s\n' % (valid, 1, full_name, email, key,
                                               size, keytype))
    qindex += PGP_KEY_QUESTION_INDEX_OFFSET
    (key, size, keytype) = GetAttendeePGPData(attendee, qindex)
    if key != 'no pgp key':
      response.write('%s,%d,%s,%s,%s,%s,%s\n' % (valid, 2, full_name, email,
                                                 key, size, keytype))
  return response


@login_required
def putpgp(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  if request.method == 'GET':
    response = HttpResponse()
    response.write('<html><head></head><body><form method="post">')
    response.write('<p>email, nth (1 or 2), ')
    response.write('fingerprint, size, type (RSA, DSA, or NISTP)</p>')
    response.write('<textarea name="data" rows="25" cols="80"></textarea>')
    response.write('<br /><input type="submit" /></form>')
    response.write('</body></html>')
    return response

  if 'data' not in request.POST:
    return HttpResponse('No Data')

  item = models.Item.objects.get(name=settings.SCALEREG_PGP_KSP_ITEM_NAME)
  attendees = item.attendee_set.filter(valid=True)

  response = HttpResponse(content_type='text/plain')
  data = request.POST['data'].split('\n')

  qpgp = []
  start = settings.SCALEREG_PGP_QUESTION_ID_START
  stop = start + 2 * PGP_KEY_QUESTION_INDEX_OFFSET
  for i in range(start, stop):
     qpgp.append(models.Question.objects.get(id=i))

  for entry in data:
    entry = entry.strip()
    if not entry:
      continue
    entry_split = entry.split(',')
    if len(entry_split) != 5:
      response.write('bad data: %s<br />\n' % entry)
      continue
    (email, nth, fingerprint, size, keytype) = entry_split
    email = email.strip()
    nth = nth.strip()
    fingerprint = fingerprint.strip()
    size = size.strip()
    keytype = keytype.strip()

    if nth == '1':
      qfingerprint = qpgp[0]
      qsize = qpgp[1]
      qkeytype = qpgp[2]
    elif nth == '2':
      qfingerprint = qpgp[3]
      qsize = qpgp[4]
      qkeytype = qpgp[5]
    else:
      response.write('bad data (nth): %s<br />\n' % entry)
      continue

    try:
      int(size)
    except:
      response.write('bad size: %s\n' % size)
      continue

    if keytype not in ('RSA', 'DSA', 'NISTP'):
      response.write('bad fingerprint type: %s' % keytype)
      continue

    try:
      attendee = attendees.get(email=email)
    except:
      response.write('cannot find %s\n' % email)
      continue
    change = True
    try:
      afingerprint = attendee.answers.get(question=qfingerprint)
      asize = attendee.answers.get(question=qsize)
      akeytype = attendee.answers.get(question=qkeytype)
    except:
      change = False

    if change:
      afingerprint.text = fingerprint
      try:
        afingerprint.save()
        response.write('change part 1/3 ok: %s %s => %s\n' %
                       (attendee.email, afingerprint, fingerprint))
      except:
        response.write('change part 1/3 error: %s %s => %s\n' %
                       (attendee.email, afingerprint, fingerprint))
      asize.text = size
      try:
        asize.save()
        response.write('change part 2/3 ok: %s %s => %s\n' %
                       (attendee.email, asize, size))
      except:
        response.write('change part 2/3 error: %s %s => %s\n' %
                       (attendee.email, asize, size))
      akeytype.text = keytype
      try:
        akeytype.save()
        response.write('change part 3/3 ok: %s %s => %s\n' %
                       (attendee.email, akeytype, keytype))
      except:
        response.write('change part 3/3 error: %s %s => %s\n' %
                       (attendee.email, akeytype, keytype))
    else:
      afingerprint = models.TextAnswer()
      afingerprint.question = models.Question.objects.get(id=qfingerprint.id)
      afingerprint.text = fingerprint
      try:
        afingerprint.save()
        response.write('add part 1/4 ok: %s %s => %s\n' %
                       (attendee.email, afingerprint, fingerprint))
      except:
        response.write('add part 1/4 error: %s %s => %s\n' %
                       (attendee.email, afingerprint, fingerprint))
        continue
      asize = models.TextAnswer()
      asize.question = models.Question.objects.get(id=qsize.id)
      asize.text = size
      try:
        asize.save()
        response.write('add part 2/4 ok: %s %s => %s\n' %
                       (attendee.email, asize, size))
      except:
        response.write('add part 2/4 error: %s %s => %s\n' %
                       (attendee.email, asize, size))
        continue
      akeytype = models.TextAnswer()
      akeytype.question = models.Question.objects.get(id=qkeytype.id)
      akeytype.text = keytype
      try:
        akeytype.save()
        response.write('add part 3/4 ok: %s %s => %s\n' %
                       (attendee.email, akeytype, keytype))
      except:
        response.write('add part 3/4 error: %s %s => %s\n' %
                       (attendee.email, akeytype, keytype))
        continue

      try:
        attendee.answers.add(afingerprint)
        attendee.answers.add(asize)
        attendee.answers.add(akeytype)
        attendee.save()
        response.write('add part 4/4 ok: %s\n' % attendee.email)
      except:
        response.write('add part 4/4 error: %s\n' % attendee.email)
        continue
  return response


@login_required
def checkpgp(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  if request.method == 'GET':
    response = HttpResponse()
    response.write('<html><head></head><body><form method="post">')
    response.write('<p>email address(es) to check</p>')
    response.write('<textarea name="data" rows="25" cols="80"></textarea>')
    response.write('<br /><input type="submit" /></form>')
    response.write('</body></html>')
    return response

  if 'data' not in request.POST:
    return HttpResponse('No Data')

  item = models.Item.objects.get(name=settings.SCALEREG_PGP_KSP_ITEM_NAME)
  attendees = item.attendee_set

  response = HttpResponse(content_type='text/plain')
  data = request.POST['data'].split('\n')

  qpgp = []
  start = settings.SCALEREG_PGP_QUESTION_ID_START
  stop = start + 2 * PGP_KEY_QUESTION_INDEX_OFFSET
  for i in range(start, stop):
     qpgp.append(models.Question.objects.get(id=i))

  for email in data:
    email = email.strip()
    if not email:
      continue
    response.write('----\n')
    attendee = None
    try:
      attendee = attendees.get(email=email)
    except:
      pass

    if not attendee:
      attendees_with_email = models.Attendee.objects.filter(email=email)
      response.write('ERROR: ')
      if attendees_with_email:
        response.write('found attendee with email %s, '
                       'but not signed up for KSP\n' % email)
      else:
        response.write('cannot find attendee with email %s\n' % email)
      continue

    try:
      answer = attendee.answers.get(question=qpgp[0])
      response.write('fingerprint 1: %s\n' % answer)
    except:
      response.write('no fingerprint 1\n')
    try:
      answer = attendee.answers.get(question=qpgp[1])
      response.write('size 1: %s\n' % answer)
    except:
      response.write('no size 1\n')
    try:
      answer = attendee.answers.get(question=qpgp[2])
      response.write('type 1: %s\n' % answer)
    except:
      response.write('no type 1\n')
    try:
      answer = attendee.answers.get(question=qpgp[3])
      response.write('fingerprint 2: %s\n' % answer)
    except:
      response.write('no fingerprint 2\n')
    try:
      answer = attendee.answers.get(question=qpgp[4])
      response.write('size 2: %s\n' % answer)
    except:
      response.write('no size 2\n')
    try:
      answer = attendee.answers.get(question=qpgp[5])
      response.write('type 2: %s\n' % answer)
    except:
      response.write('no type 2\n')

  return response


@login_required
def AnnounceSubscribers(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  response = HttpResponse(content_type='text/plain')
  attendees = models.Attendee.objects.filter(valid=True).filter(can_email=True)
  for attendee in attendees:
    response.write('%d,%s\n' % (attendee.id, attendee.email))
  return response


@login_required
def CouponUsage(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  coupon_data = []
  for coupon in models.Coupon.objects.all():
    datum = {}
    datum['coupon'] = coupon
    datum['use_count'] = models.Attendee.objects.filter(
        order=coupon.order).filter(valid=True).count()
    coupon_data.append(datum)

  return render_to_response('reports/coupon_usage.html',
    {'title': 'Coupon Usage',
     'coupons': coupon_data,
    })
