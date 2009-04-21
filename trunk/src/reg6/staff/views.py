# Create your views here.

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from scale.reports.views import reports_perm_checker

@login_required
def index(request):
  can_access = reports_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')
  return render_to_response('reg6/staff/index.html',
    {'title': 'Staff Page',
    })

