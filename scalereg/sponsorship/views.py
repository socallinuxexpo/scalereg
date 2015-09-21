# Create your views here.

from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response
from scalereg.common import utils
from scalereg.sponsorship import forms
from scalereg.sponsorship import models
import datetime
import sys

from django.http import HttpRequest

STEPS_TOTAL = 5

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


def ApplyPromoToPackages(promo, packages):
  if not promo:
    return None

  for t in packages:
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


def ApplyPromoToPostedItems(package, promo, post):
  avail_items = GetPackageItems(package)
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


def ItemNameCompare(x, y):
  if x.name == y.name:
    return 0
  if x.name < y.name:
    return -1
  return 1


def GetPackageItems(package):
  set1 = package.item_set.all()
  set2 = models.Item.objects.filter(applies_to_all=True)
  combined_set = [ s for s in set1 if s.active ]
  for s in set2:
    if not s.active:
      continue
    if s not in combined_set:
      combined_set.append(s)
  combined_set.sort(cmp=ItemNameCompare)
  return combined_set


def CalculatePackageCost(package, items):
  total = package.price
  offset_item = None
  for item in items:
    total += item.price
    if offset_item:
      continue
    if item.package_offset:
      offset_item = item
  if offset_item:
    total -= package.price
  return (total, offset_item)


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
      return render_to_response('sponsorship/reg_error.html',
        {'title': 'Registration Problem',
         'error_message': 'No %s information.' % var,
        })
  for var in cookies:
    if var not in request.session:
      return render_to_response('sponsorship/reg_error.html',
        {'title': 'Registration Problem',
         'error_message': 'No %s information.' % var,
        })
  return None


def CheckReferrer(meta, path):
  if 'HTTP_REFERER' in meta and path in meta['HTTP_REFERER']:
    return None
  return HttpResponseRedirect('/sponsorship/')


def GenerateOrderID(bad_nums):
  return utils.GenerateUniqueID(10, bad_nums)


def index(request):
  avail_packages = [package for package in
                    models.Package.public_objects.order_by('name')]
  active_promocode_set = models.PromoCode.active_objects
  avail_promocodes = active_promocode_set.names()

  request_dict = None
  if request.method == 'GET':
    request_dict = request.GET
  elif request.method == 'POST':
    request_dict = request.POST

  promo_in_use = None
  if request_dict:
    if 'promo' in request_dict and request_dict['promo'] in avail_promocodes:
      promo_in_use = active_promocode_set.get(name=request_dict['promo'])

  promo_name = ApplyPromoToPackages(promo_in_use, avail_packages)

  request.session.set_test_cookie()

  return render_to_response('sponsorship/reg_index.html',
    {'title': 'Sponsorship',
     'packages': avail_packages,
     'promo': promo_name,
     'step': 1,
     'steps_total': STEPS_TOTAL,
    })


def AddItems(request):
  if request.method != 'POST':
    return HttpResponseRedirect('/sponsorship/')
  r = CheckReferrer(request.META, '/sponsorship/')
  if r:
    return r

  required_vars = ['promo', 'package']
  r = CheckVars(request, required_vars, [])
  if r:
    return r

  package = models.Package.public_objects.filter(name=request.POST['package'])
  active_promocode_set = models.PromoCode.active_objects
  avail_promocodes = active_promocode_set.names()

  promo = request.POST['promo'].upper()
  promo_in_use = None
  if promo in avail_promocodes:
    promo_in_use = active_promocode_set.get(name=promo)

  promo_name = ApplyPromoToPackages(promo_in_use, package)
  items = GetPackageItems(package[0])
  ApplyPromoToItems(promo_in_use, items)

  return render_to_response('sponsorship/reg_items.html',
    {'title': 'Sponsorship - Add Items',
     'package': package[0],
     'promo': promo_name,
     'items': items,
     'step': 2,
     'steps_total': STEPS_TOTAL,
    })


def AddSponsor(request):
  if request.method != 'POST':
    return HttpResponseRedirect('/sponsorship/')

  action = None
  if 'HTTP_REFERER' in request.META:
    if '/sponsorship/add_items/' in request.META['HTTP_REFERER']:
      action = 'add'
    elif '/sponsorship/add_sponsor/' in request.META['HTTP_REFERER']:
      action = 'check'

  if not action:
    return HttpResponseRedirect('/sponsorship/')

  required_vars = ['package', 'promo']
  r = CheckVars(request, required_vars, [])
  if r:
    return r

  try:
    package = models.Package.public_objects.get(name=request.POST['package'])
  except models.Package.DoesNotExist:
    return render_to_response('sponsorship/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'You have selected an invalid package type.',
      })
  active_promocode_set = models.PromoCode.active_objects
  avail_promocodes = active_promocode_set.names()

  promo_in_use = None
  if request.POST['promo'] in avail_promocodes:
    promo_in_use = active_promocode_set.get(name=request.POST['promo'])

  promo_name = ApplyPromoToPackages(promo_in_use, [package])
  selected_items = ApplyPromoToPostedItems(package, promo_in_use, request.POST)
  (total, offset_item) = CalculatePackageCost(package, selected_items)

  if action == 'add':
    request.session['sponsor'] = ''
    form = forms.SponsorForm()
  else:
    form = forms.SponsorForm(request.POST)
    if form.is_valid():
      if not request.session.test_cookie_worked():
        return render_to_response('sponsorship/reg_error.html',
          {'title': 'Registration Problem',
           'error_message': 'Please do not register multiple sponsors at the same time. Please make sure you have cookies enabled.',
          })

      # create sponsor
      new_sponsor = form.save(commit=False)

      # add badge type
      new_sponsor.package = package
      # add promo
      new_sponsor.promo = promo_in_use

      # save sponsor
      new_sponsor.save()
      form.save_m2m()

      # add ordered items
      for item in selected_items:
        new_sponsor.ordered_items.add(item)

      request.session['sponsor'] = new_sponsor.id

      return HttpResponseRedirect('/sponsorship/payment/')

  return render_to_response('sponsorship/reg_sponsor.html',
    {'title': 'Sponsorship - Register Sponsor',
     'package': package,
     'promo': promo_name,
     'items': selected_items,
     'offset_item': offset_item,
     'total': total,
     'form': form,
     'agreement_url': settings.SCALEREG_SPONSORSHIP_AGREEMENT_URL,
     'step': 3,
     'steps_total': STEPS_TOTAL,
    })


def Payment(request):
  if request.method != 'GET':
    return HttpResponseRedirect('/sponsorship/')
  r = CheckReferrer(request.META, '/sponsorship/add_sponsor/')
  if r:
    print 'fail1'
    return r

  required_cookies = ['sponsor']
  r = CheckVars(request, [], required_cookies)
  if r:
    print 'fail2'
    return r

  sponsor = None
  try:
    sponsor = models.Sponsor.objects.get(id=request.session['sponsor'])
    if sponsor.valid:
      sponsor = None
  except models.Sponsor.DoesNotExist:
    pass

  if not sponsor:
    return render_to_response('sponsorship/reg_error.html',
      {'title': 'Registration Problem',
       'error_message': 'No sponsor to pay for.',
      })

  order_tries = 0
  while True:
    try:
      bad_order_nums = [ x.order_num for x in models.TempOrder.objects.all() ]
      bad_order_nums += [ x.order_num for x in models.Order.objects.all() ]
      order_num = GenerateOrderID(bad_order_nums)
      print order_num
      temp_order = models.TempOrder(order_num=order_num, sponsor=sponsor)
      temp_order.save()
      break
    except: # FIXME catch the specific db exceptions
      raise
      order_tries += 1
      if order_tries > 10:
        return render_to_response('sponsorship/reg_error.html',
          {'title': 'Registration Problem',
           'error_message': 'We cannot generate an order ID for you.',
          })

  return render_to_response('sponsorship/reg_payment.html',
    {'title': 'Sponsorship - Payment',
     'sponsor': sponsor,
     'order': order_num,
     'payflow_url': settings.SCALEREG_PAYFLOW_URL,
     'payflow_partner': settings.SCALEREG_PAYFLOW_PARTNER,
     'payflow_login': settings.SCALEREG_PAYFLOW_LOGIN,
     'step': 4,
     'steps_total': STEPS_TOTAL,
    })


def Sale(request):
  if request.method != 'POST':
    ScaleDebug('not POST')
    return HttpResponse('Method not allowed: %s' % request.method, status=405)

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

  already_paid_sponsor = False
  sponsor = temp_order.sponsor
  if sponsor.valid:
    already_paid_sponsor = True

  total = sponsor.package_cost()
  r = CheckPaymentAmount(request, total)
  if r:
    return r

  try:
    order = models.Order(
        order_num=request.POST['USER1'],
        valid=True,
        name=request.POST['NAME'],
        address=request.POST['ADDRESS'],
        city=request.POST['CITY'],
        state=request.POST['STATE'],
        zip_code=request.POST['ZIP'],
        country=request.POST['COUNTRY'],
        email=request.POST['EMAIL'],
        phone=request.POST['PHONE'],
        amount=request.POST['AMOUNT'],
        auth_code=request.POST['AUTHCODE'],
        pnref=request.POST['PNREF'],
        resp_msg=request.POST['RESPMSG'],
        result=request.POST['RESULT'],
        sponsor=sponsor,
        already_paid_sponsor=already_paid_sponsor)
    order.save()
  except Exception, inst: # FIXME catch the specific db exceptions
    ScaleDebug('cannot save order')
    ScaleDebug(inst.args)
    ScaleDebug(inst)
    return HttpResponseServerError('cannot save order')

  if not already_paid_sponsor:
    sponsor.valid = True
    sponsor.save()

  return HttpResponse('success')


def FailedPayment(request):
  return render_to_response('sponsorship/reg_failed.html',
    {'title': 'Sponsorship Payment Failed',
    })


def FinishPayment(request):
  if request.method != 'POST':
    return HttpResponseRedirect('/sponsorship/')

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

  return render_to_response('sponsorship/reg_receipt.html',
    {'title': 'Sponsorship - Payment Receipt',
     'name': request.POST['NAME'],
     'email': request.POST['EMAIL'],
     'sponsor': order.sponsor,
     'already_paid_sponsor': order.already_paid_sponsor,
     'order': request.POST['USER1'],
     'step': 5,
     'steps_total': STEPS_TOTAL,
     'total': request.POST['AMOUNT'],
    })
