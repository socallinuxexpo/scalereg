from django.test import TestCase

from .models import Item
from .views import get_posted_items


class GetPostedItemsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.item1 = Item.objects.create(name='I1',
                                        description='Item 1',
                                        price=10,
                                        active=True,
                                        promo=False,
                                        ticket_offset=False,
                                        applies_to_all=True)
        cls.item2 = Item.objects.create(name='I2',
                                        description='Item 2',
                                        price=20,
                                        active=True,
                                        promo=False,
                                        ticket_offset=False,
                                        applies_to_all=True)
        cls.item3 = Item.objects.create(name='I3',
                                        description='Item 3',
                                        price=30,
                                        active=False,
                                        promo=False,
                                        ticket_offset=False,
                                        applies_to_all=True)

    def test_no_items_posted(self):
        post = {}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 0)

    def test_one_item_posted(self):
        post = {'item0': 'I1'}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 1)
        self.assertIn(self.item1, selected_items)

    def test_multiple_items_posted(self):
        post = {'item0': 'I1', 'item1': 'I2'}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 2)
        self.assertIn(self.item1, selected_items)
        self.assertIn(self.item2, selected_items)

    def test_item_not_in_avail_items(self):
        post = {'item0': 'I3'}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 0)

    def test_item_name_does_not_exist(self):
        post = {'item0': 'I4'}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 0)

    def test_post_with_extra_keys(self):
        post = {'item0': 'I1', 'foo': 'bar'}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 1)
        self.assertIn(self.item1, selected_items)

    def test_too_many_items_posted(self):
        post = {'item0': 'I1', 'item1': 'I2'}
        avail_items = [self.item1]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 1)
        self.assertIn(self.item1, selected_items)

    def test_repeated_items_posted(self):
        post = {'item0': 'I1', 'item1': 'I1', 'item2': 'I2'}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 1)
        self.assertIn(self.item1, selected_items)
