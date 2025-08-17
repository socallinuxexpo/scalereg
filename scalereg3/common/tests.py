import random

from django.test import TestCase

from . import utils


class UtilsTest(TestCase):

    def test_generate_id(self):
        random.seed(0)
        self.assertEqual(utils.generate_id(5), 'Y0CQ6')
        self.assertEqual(utils.generate_id(10), '5ZT4WN6ISI')

    def test_generate_unique_id(self):
        random.seed(0)
        existing_ids = {'Y0C', 'Q65', 'ZT4'}
        new_id = utils.generate_unique_id(3, existing_ids)
        self.assertEqual(new_id, 'WN6')
