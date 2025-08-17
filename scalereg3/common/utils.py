import random
import string


def generate_id(length):
    valid_chars = string.ascii_uppercase + string.digits
    return ''.join([random.choice(valid_chars) for x in range(length)])


def generate_unique_id(length, existing_ids):
    existing_ids = set(existing_ids)
    while True:
        new_id = generate_id(length)
        if new_id not in existing_ids:
            return new_id
