# Create your views here.

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from scale.auth_helper.models import Service
from scale.reg6 import models
import inspect
import re

@login_required
def index(request):
  # figure out what services are available
  services_user = Service.objects.filter(users=request.user)
  services_group = None
  for f in request.user.groups.all():
    services_group = services_group or Service.objects.filter(groups=f)
  services = services_group or services_user
  services = services.filter(active=True).order_by('name')

  can_access = False
  for f in services.values():
    if re.compile('%s/.*' % f['url']).match(request.path):
      can_access = True
      break

  if not request.user.is_superuser and not can_access:
    return HttpResponseRedirect('/accounts/profile/')
  
  perms = request.user.get_all_permissions()
  tables = [ m[0] for m in inspect.getmembers(models, inspect.isclass) ]
  model_list = []
  for t in tables:
    if request.user.is_superuser or "reg6.view_%s" % t.lower() in perms:
      def foo(match):
	return '%s %s' % match.groups()
      name = re.sub('([a-z])([A-Z])', foo, t)
      if not name.endswith('s'):
        name = name + 's'
      url = t.lower() + '/'
      model_list.append({'name': name, 'url': url})

  return render_to_response('reports/index.html',
    {'user': request.user, 'title': 'Reports', 'model_list': model_list})
