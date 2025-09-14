import hashlib
import random
import string

from django.conf import settings


def generate_id(length):
    valid_chars = string.ascii_uppercase + string.digits
    return ''.join([random.choice(valid_chars) for x in range(length)])


def generate_unique_id(length, existing_ids):
    existing_ids = set(existing_ids)
    while True:
        new_id = generate_id(length)
        if new_id not in existing_ids:
            return new_id


def checkin_hash(data):
    data += settings.SCALEREG_EXPRESS_CHECKIN_SECRET
    return hashlib.sha1(data.encode('utf-8')).hexdigest()[:6]
