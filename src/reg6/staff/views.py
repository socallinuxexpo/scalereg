# Create your views here.

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from scale.reg6 import models
from scale.reports.views import reports_perm_checker

@login_required
def index(request):
  can_access = reports_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')
  return render_to_response('reg6/staff/index.html',
    {'title': 'Staff Page',
    })

@login_required
def CheckIn(request):
  can_access = reports_perm_checker(request.user, request.path)
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

  return render_to_response('reg6/staff/checkin.html',
    {'title': 'Attendee Check In',
     'attendees': attendees,
     'last': request.POST['last_name'],
     'zip': request.POST['zip'],
     'search': 1,
    })

@login_required
def FinishCheckIn(request):
  can_access = reports_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  if request.method != 'POST':
    return HttpResponseRedirect('/reg6/')

  if 'id' not in request.POST:
    return render_to_response('error.html',
      {'error_message': 'No ID'})

  try:
    attendee = models.Attendee.objects.get(id=request.POST['id'])
  except models.Attendee.DoesNotExist:
    return render_to_response('error.html',
      {'error_message': 'We could not find your registration'})

  try:
    attendee.checked_in = True
    attendee.save()
  except:
    return render_to_response('error.html',
      {'error_message': 'We encountered a problem with your checkin'})

  return render_to_response('reg6/staff/finish_checkin.html',
    {'title': 'Attendee Check In',
     'attendee': attendee,
    })
