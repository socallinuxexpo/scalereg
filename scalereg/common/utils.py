import random
import string

def GenerateID(length):
  valid_chars = string.ascii_uppercase + string.digits
  return ''.join([random.choice(valid_chars) for x in xrange(length)])
