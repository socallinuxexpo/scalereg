from decimal import Decimal

from django.apps import apps
from django.test import TestCase
from django.utils import timezone

from .views import get_orders_data


class GetOrdersDataTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = timezone.now()
        day = timezone.timedelta(days=1)

        order_objects = apps.get_model('reg23', 'Order').objects
        create_order_with_date = cls.create_order_with_date
        create_order_with_date(order_objects,
                               today,
                               order_num='0',
                               valid=True,
                               payment_type='cash',
                               amount=2)
        create_order_with_date(order_objects,
                               today - (6 * day),
                               order_num='1',
                               valid=True,
                               payment_type='cash',
                               amount=3)
        create_order_with_date(order_objects,
                               today - (7 * day),
                               order_num='2',
                               valid=True,
                               payment_type='payflow',
                               amount=5)
        create_order_with_date(order_objects,
                               today - (8 * day),
                               order_num='3',
                               valid=True,
                               payment_type='cash',
                               amount=7)
        create_order_with_date(order_objects,
                               today - (29 * day),
                               order_num='4',
                               valid=True,
                               payment_type='payflow',
                               amount=11)
        create_order_with_date(order_objects,
                               today - (30 * day),
                               order_num='5',
                               valid=True,
                               payment_type='cash',
                               amount=13)
        create_order_with_date(order_objects,
                               today - (31 * day),
                               order_num='6',
                               valid=True,
                               payment_type='cash',
                               amount=17)

        create_order_with_date(order_objects,
                               today - (2 * day),
                               order_num='7',
                               valid=False,
                               payment_type='cash',
                               amount=19)
        create_order_with_date(order_objects,
                               today - (10 * day),
                               order_num='8',
                               valid=False,
                               payment_type='payflow',
                               amount=23)
        create_order_with_date(order_objects,
                               today - (40 * day),
                               order_num='9',
                               valid=False,
                               payment_type='cash',
                               amount=29)

    @staticmethod
    def create_order_with_date(order_objects, date, **kwargs):
        order = order_objects.create(**kwargs)
        order.date = date
        order.save()

    def check_by_type_list(self, actual_list, expected_list):
        self.assertEqual(len(actual_list), len(expected_list))
        for actual, expected in zip(actual_list, expected_list):
            self.assertDictEqual(actual, expected)

    def test_get_orders_data(self):
        data = get_orders_data()
        self.assertTrue('by_type' in data)
        by_type_data = data.pop('by_type')
        expected_by_type = ({
            'name': 'Payflow',
            'numbers': 2,
            'numbers_30': 2,
            'numbers_7': 1,
            'revenue': Decimal('16.00'),
        }, {
            'name': 'Cash',
            'numbers': 5,
            'numbers_30': 4,
            'numbers_7': 2,
            'revenue': Decimal('42.00'),
        }, {
            'name': 'Invitee',
            'numbers': 0,
            'numbers_30': 0,
            'numbers_7': 0,
            'revenue': 0,
        }, {
            'name': 'Exhibitor',
            'numbers': 0,
            'numbers_30': 0,
            'numbers_7': 0,
            'revenue': 0,
        }, {
            'name': 'Speaker',
            'numbers': 0,
            'numbers_30': 0,
            'numbers_7': 0,
            'revenue': 0,
        }, {
            'name': 'Press',
            'numbers': 0,
            'numbers_30': 0,
            'numbers_7': 0,
            'revenue': 0,
        }, {
            'name': 'Free Upgrade',
            'numbers': 0,
            'numbers_30': 0,
            'numbers_7': 0,
            'revenue': 0,
        })
        self.check_by_type_list(by_type_data, expected_by_type)

        expected_dict = {
            'numbers': 7,
            'numbers_30': 6,
            'numbers_7': 3,
            'revenue': Decimal('58.00'),
            'revenue_30': Decimal('41.00'),
            'revenue_7': Decimal('10.00'),
        }
        self.assertDictEqual(data, expected_dict)
