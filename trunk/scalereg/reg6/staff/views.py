# Create your views here.

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from scalereg.common.utils import services_perm_checker
from scalereg.common.views import handler500
from scalereg.reg6 import models
from scalereg.reg6.views import GenerateOrderID

@login_required
def index(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')
  return render_to_response('reg6/staff/index.html',
    {'title': 'Staff Page',
    })

@login_required
def CheckIn(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  if request.method == 'GET':
    return render_to_response('reg6/staff/checkin.html',
      {'title': 'Attendee Check In',
      })

  attendees = []
  if request.POST['last_name']:
    attendees = models.Attendee.objects.filter(valid=True,
      last_name__icontains=request.POST['last_name'])
  if not attendees:
    attendees = models.Attendee.objects.filter(valid=True,
      zip=request.POST['zip'])
  for att in attendees:
    if att.checked_in:
      try:
        rp = models.Reprint.objects.get(attendee=att)
        count = rp.count
      except:
        count = 0
      att.rp_count = count + 1

  return render_to_response('reg6/staff/checkin.html',
    {'title': 'Attendee Check In',
     'attendees': attendees,
     'last': request.POST['last_name'],
     'zip': request.POST['zip'],
     'search': 1,
    })

@login_required
def FinishCheckIn(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  if request.method != 'POST':
    return HttpResponseRedirect('/reg6/')

  if 'id' not in request.POST:
    return handler500(request, msg='No ID')

  try:
    attendee = models.Attendee.objects.get(id=request.POST['id'])
  except models.Attendee.DoesNotExist:
    return handler500(request, msg='We could not find your registration')

  try:
    attendee.checked_in = True
    attendee.save()
  except:
    return handler500(request, msg='We encountered a problem with your checkin')

  return render_to_response('reg6/staff/finish_checkin.html',
    {'title': 'Attendee Check In',
     'attendee': attendee,
    })

@login_required
def CashPayment(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  tickets = models.Ticket.objects.filter(cash=True)
  if request.method == 'GET':
    return render_to_response('reg6/staff/cash.html',
      {'title': 'Cash Payment',
       'tickets': tickets,
      })

  for var in ['FIRST', 'LAST', 'EMAIL', 'ZIP', 'TICKET']:
    if var not in request.POST:
      return handler500(request, msg='missing data: no %s field' % var)

  try:
    ticket = models.Ticket.objects.get(name=request.POST['TICKET'])
  except:
    return handler500(request, msg='cannot find ticket type')

  order = models.Order()
  bad_order_nums = [ x.order_num for x in models.TempOrder.objects.all() ]
  bad_order_nums += [ x.order_num for x in models.Order.objects.all() ]
  order.order_num = GenerateOrderID(bad_order_nums)
  assert order.order_num
  order.valid = True
  order.name = '%s %s' % (request.POST['FIRST'], request.POST['LAST'])
  order.address = 'Cash'
  order.city = 'Cash'
  order.state = 'Cash'
  order.zip = request.POST['ZIP']
  order.email = request.POST['EMAIL']
  order.payment_type = 'cash'
  order.amount = ticket.price

  attendee = models.Attendee()
  attendee.first_name = request.POST['FIRST']
  attendee.last_name = request.POST['LAST']
  attendee.zip = request.POST['ZIP']
  attendee.email = request.POST['EMAIL']
  attendee.valid = True
  attendee.checked_in = True
  attendee.can_email = True
  attendee.order = order
  attendee.badge_type = ticket
  try:
    attendee.save()
    order.save()
  except: # FIXME catch the specific db exceptions
    attendee.delete()
    order.delete()
    return handler500(request, msg='cannot save order, bad data?')

  return render_to_response('reg6/staff/cash.html',
    {'title': 'Cash Payment',
     'success': True,
     'tickets': tickets,
    })

@login_required
def Reprint(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  if request.method == 'GET':
    return HttpResponseRedirect('/reg6/staff/checkin/')

  if request.POST['id']:
    REPRINT_TEMPLATE = 'reg6/staff/reprint.html'
    try:
      attendee = models.Attendee.objects.get(id=int(request.POST['id']))
      reprint = None
      try:
        reprint = models.Reprint.objects.get(attendee=attendee)
      except:
        reprint = models.Reprint()
        reprint.attendee = attendee
        reprint.count = 0
      reprint.count += 1
      reprint.save()
      return render_to_response(REPRINT_TEMPLATE,
        {'title': 'Attendee Reprint',
         'reprint': reprint,
        })
    except:
      return render_to_response(REPRINT_TEMPLATE,
        {'title': 'Attendee Reprint Error',
         'reprint': None,
        })
  else:
    return render_to_response(REPRINT_TEMPLATE,
      {'title': 'Attendee Reprint Invalid',
       'reprint': None,
      })
