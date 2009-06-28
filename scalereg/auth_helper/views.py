# Create your views here.

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from scalereg.auth_helper.models import Service

def index(request):
  return HttpResponseRedirect('/accounts/profile/')

@login_required
def profile(request):
  # figure out what servers are available
  if request.user.is_superuser:
    services = Service.objects.filter(active=True)
  else:
    services_user = Service.objects.filter(users=request.user)
    services_user = services_user.filter(active=True)

    services_group = []
    for f in request.user.groups.all():
      group_s = Service.objects.filter(groups=f)
      group_s = group_s.filter(active=True)
      for s in group_s:
        services_group.append(s)

    services = []
    for f in services_user:
      services.append(f)
    services = set(services + services_group)

  return render_to_response('profile/index.html',
    {'user': request.user, 'title': 'Available Services', 'services': services})
