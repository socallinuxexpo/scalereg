# Create your views here.

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, loader
from scale.auth_helper.models import Service

def index(request):
  return HttpResponseRedirect('/accounts/profile/')

@login_required
def profile(request):
  # figure out what servers are available
  services_user = Service.objects.filter(users=request.user)
  services_group = None
  for f in request.user.groups.all():
    services_group = services_group or Service.objects.filter(groups=f)
  services = services_group or services_user
  services = services.filter(active=True).order_by('name')

  t = loader.get_template('profile/index.html')
  c = Context({'user': request.user, 'title': 'Available Services', 'services': services})
  return HttpResponse(t.render(c))


