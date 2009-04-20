# Create your views here.

from django.contrib.auth.decorators import login_required
from django.db.models import BooleanField
from django.db.models.base import ModelBase
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import loader
from django.views.generic.list_detail import object_list as django_object_list
from scale.auth_helper.models import Service
from scale.reg6 import models
import inspect
import re
import string

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


def paranoid_strip(value):
  valid_chars = string.ascii_letters + string.digits + '_'
  for c in value:
    if c not in valid_chars:
      raise ValueError
  return value

def reports_perm_checker(user, path):
  # figure out what services are available
  if user.is_superuser:
    return True

  services_user = Service.objects.filter(users=user)
  services_user = services_user.filter(active=True)

  services_group = []
  for f in user.groups.all():
    group_s = Service.objects.filter(groups=f)
    group_s = group_s.filter(active=True)
    for s in group_s:
      services_group.append(s)

  services = []
  for f in services_user:
    services.append(f)
  services = set(services + services_group)

  can_access = False
  for f in services:
    if re.compile('%s/.*' % f.url).match(path):
      can_access = True
      break
  return can_access

@login_required
def index(request):
  can_access = reports_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  perms = request.user.get_all_permissions()
  tables = [m[0] for m in inspect.getmembers(models, inspect.isclass)
             if type(m[1]) == ModelBase and m[1]._meta.admin]
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

@login_required
def object_list(request, queryset, paginate_by=None, page=None,
  allow_empty=False, template_name=None, template_loader=loader,
  extra_context=None, context_processors=None, template_object_name='object',
  mimetype=None):
  all_fields = [f.name for f in queryset.model._meta.fields]

  if not extra_context:
    extra_context = {}

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

  if 'order' in request.GET:
    if request.GET['order'] in all_fields:
      ordering = request.GET['order']
      extra_context['order'] = ordering
      if 'dec' in request.GET:
        ordering = '-' + ordering
        extra_context['dec'] = 1
      else:
        extra_context['dec'] = 0
      queryset = queryset.order_by(ordering)

  extra_context['numbers'] = len(queryset)

  return django_object_list(request, queryset, paginate_by, page, allow_empty,
    template_name, template_loader, extra_context, context_processors,
    template_object_name, mimetype)

@login_required
def reg6log(request):
  if not request.user.is_superuser:
    return HttpResponseRedirect('/accounts/profile/')

  response = HttpResponse(mimetype='text/plain')
  try:
    f = open('/tmp/scale_reg.log')
    response.write(f.read())
    f.close()
  except:
    response.write('error reading log files\n')
  return response
