from scalereg.auth_helper.models import Service
import random
import re
import string

def GenerateID(length):
  valid_chars = string.ascii_uppercase + string.digits
  return ''.join([random.choice(valid_chars) for x in xrange(length)])

def GenerateUniqueID(length, existing_ids):
  id = GenerateID(length)
  if not existing_ids:
    return id
  existing_ids = set(existing_ids)
  while id in existing_ids:
    id = GenerateID(length)
  return id


def services_perm_checker(user, path):
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
