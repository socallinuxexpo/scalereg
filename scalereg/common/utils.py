import random
import string

def GenerateID(length):
  valid_chars = string.ascii_uppercase + string.digits
  return ''.join([random.choice(valid_chars) for x in xrange(length)])

def GenerateUniqueID(length, existing_ids):
  id = GenerateID(length)
  if not existing_ids:
    return id
  while id in existing_ids:
    id = GenerateID(length)
  return id
