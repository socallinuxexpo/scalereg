# Create your views here.

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, loader
from scale.auth_helper.models import Service

def index(request):
  return HttpResponseRedirect('/accounts/profile/')

@login_required
def profile(request):
  services = Service.objects.filter(users=request.user).order_by('name')
  t = loader.get_template('profile/index.html')
  c = Context({'user': request.user, 'title': 'Available Services', 'services': services})
  return HttpResponse(t.render(c))


