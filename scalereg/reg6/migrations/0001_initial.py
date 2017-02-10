# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=200)),
            ],
            options={
                'permissions': (('view_answer', 'Can view answer'),),
            },
        ),
        migrations.CreateModel(
            name='Attendee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('valid', models.BooleanField(default=False)),
                ('checked_in', models.BooleanField(default=False, help_text=b'Only for valid attendees')),
                ('salutation', models.CharField(blank=True, max_length=10, choices=[(b'Mr', b'Mr.'), (b'Ms', b'Ms.'), (b'Mrs', b'Mrs.'), (b'Dr', b'Dr.')])),
                ('first_name', models.CharField(max_length=60)),
                ('last_name', models.CharField(max_length=60)),
                ('title', models.CharField(max_length=60, blank=True)),
                ('org', models.CharField(max_length=60, blank=True)),
                ('email', models.EmailField(max_length=254)),
                ('zip', models.CharField(max_length=20)),
                ('phone', models.CharField(max_length=20, blank=True)),
                ('obtained_items', models.CharField(help_text=b'comma separated list of items', max_length=60, blank=True)),
                ('can_email', models.BooleanField(default=False)),
            ],
            options={
                'permissions': (('view_attendee', 'Can view attendee'),),
            },
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('code', models.CharField(help_text=b'Unique 10 upper-case letters + numbers code', max_length=10, serialize=False, primary_key=True)),
                ('used', models.BooleanField(default=False)),
                ('max_attendees', models.PositiveSmallIntegerField()),
                ('expiration', models.DateField(help_text=b'Not usable on this day', null=True, blank=True)),
            ],
            options={
                'permissions': (('view_coupon', 'Can view coupon'),),
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Unique, up to 4 upper-case letters / numbers', max_length=4)),
                ('description', models.CharField(max_length=60)),
                ('price', models.DecimalField(max_digits=5, decimal_places=2)),
                ('active', models.BooleanField(default=False)),
                ('pickup', models.BooleanField(default=False, help_text=b'Can we track if this item gets picked up?')),
                ('promo', models.BooleanField(default=False, help_text=b'Price affected by promo code?')),
                ('ticket_offset', models.BooleanField(default=False, help_text=b'Item offsets ticket price?')),
                ('applies_to_all', models.BooleanField(default=False, help_text=b'Applies to all tickets')),
            ],
            options={
                'permissions': (('view_item', 'Can view item'),),
            },
        ),
        migrations.CreateModel(
            name='KioskAgent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('agent', models.CharField(max_length=20)),
                ('attendee', models.ForeignKey(to='reg6.Attendee')),
            ],
            options={
                'permissions': (('view_kiosk_agent', 'Can view kiosk agent'),),
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('order_num', models.CharField(help_text=b'Unique 10 upper-case letters + numbers code', max_length=10, serialize=False, primary_key=True)),
                ('valid', models.BooleanField(default=False)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=120)),
                ('address', models.CharField(max_length=120)),
                ('city', models.CharField(max_length=60)),
                ('state', models.CharField(max_length=60)),
                ('zip', models.CharField(max_length=20)),
                ('country', models.CharField(max_length=60, blank=True)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=20, blank=True)),
                ('amount', models.DecimalField(max_digits=6, decimal_places=2)),
                ('payment_type', models.CharField(max_length=10, choices=[(b'verisign', b'Verisign'), (b'google', b'Google Checkout'), (b'cash', b'Cash'), (b'invitee', b'Invitee'), (b'exhibitor', b'Exhibitor'), (b'speaker', b'Speaker'), (b'press', b'Press'), (b'freeup', b'Free Upgrade')])),
                ('auth_code', models.CharField(help_text=b'Only used by Verisign', max_length=30, blank=True)),
                ('pnref', models.CharField(help_text=b'Payment Network Reference ID (PNREF), a number generated by PayPal that uniquely identifies the transaction', max_length=15, blank=True)),
                ('resp_msg', models.CharField(help_text=b'Only used by Verisign', max_length=60, blank=True)),
                ('result', models.CharField(help_text=b'Only used by Verisign', max_length=60, blank=True)),
                ('already_paid_attendees', models.ManyToManyField(help_text=b'Attendees charged multiple times on this order', related_name='already_paid', to='reg6.Attendee', blank=True)),
            ],
            options={
                'permissions': (('view_order', 'Can view order'),),
            },
        ),
        migrations.CreateModel(
            name='PromoCode',
            fields=[
                ('name', models.CharField(help_text=b'Up to 5 letters, upper-case letters + numbers', max_length=5, serialize=False, primary_key=True)),
                ('description', models.CharField(max_length=60)),
                ('price_modifier', models.DecimalField(help_text=b'This is the price multiplier, i.e. for 0.4, $10 becomes $4.', max_digits=3, decimal_places=2)),
                ('active', models.BooleanField(default=False)),
                ('start_date', models.DateField(help_text=b'Available on this day', null=True, blank=True)),
                ('end_date', models.DateField(help_text=b'Not Usable on this day', null=True, blank=True)),
                ('applies_to_all', models.BooleanField(default=False, help_text=b'Applies to all tickets')),
            ],
            options={
                'permissions': (('view_promocode', 'Can view promo code'),),
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=200)),
                ('active', models.BooleanField(default=False)),
                ('applies_to_all', models.BooleanField(default=False, help_text=b'Applies to all tickets')),
            ],
            options={
                'permissions': (('view_question', 'Can view question'),),
            },
        ),
        migrations.CreateModel(
            name='Reprint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('count', models.IntegerField()),
                ('attendee', models.ForeignKey(to='reg6.Attendee')),
            ],
            options={
                'permissions': (('view_reprint', 'Can view reprint'),),
            },
        ),
        migrations.CreateModel(
            name='ScannedBadge',
            fields=[
                ('number', models.PositiveIntegerField(serialize=False, primary_key=True)),
                ('size', models.CharField(max_length=4)),
            ],
        ),
        migrations.CreateModel(
            name='TempOrder',
            fields=[
                ('order_num', models.CharField(help_text=b'Unique 10 upper-case letters + numbers code', max_length=10, serialize=False, primary_key=True)),
                ('attendees', models.TextField(blank=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('name', models.CharField(help_text=b'Up to 5 letters, upper-case letters + numbers', max_length=5, serialize=False, primary_key=True)),
                ('description', models.CharField(max_length=60)),
                ('type', models.CharField(max_length=10, choices=[(b'expo', b'Expo Only'), (b'full', b'Full'), (b'press', b'Press'), (b'speaker', b'Speaker'), (b'exhibitor', b'Exhibitor'), (b'staff', b'Staff'), (b'friday', b'Friday Only')])),
                ('price', models.DecimalField(max_digits=5, decimal_places=2)),
                ('public', models.BooleanField(default=False, help_text=b'Publicly available on the order page')),
                ('cash', models.BooleanField(default=False, help_text=b'Available for cash purchase')),
                ('upgradable', models.BooleanField(default=False, help_text=b'Eligible for upgrades')),
                ('limit', models.PositiveIntegerField(help_text=b'Maximum number of tickets, 0 for unlimited')),
                ('start_date', models.DateField(help_text=b'Available on this day', null=True, blank=True)),
                ('end_date', models.DateField(help_text=b'Not Usable on this day', null=True, blank=True)),
            ],
            options={
                'permissions': (('view_ticket', 'Can view ticket'),),
            },
        ),
        migrations.CreateModel(
            name='Upgrade',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('valid', models.BooleanField(default=False)),
                ('attendee', models.ForeignKey(to='reg6.Attendee')),
                ('new_badge_type', models.ForeignKey(to='reg6.Ticket')),
                ('new_order', models.ForeignKey(blank=True, to='reg6.Order', null=True)),
                ('new_ordered_items', models.ManyToManyField(to='reg6.Item', blank=True)),
                ('old_badge_type', models.ForeignKey(related_name='old_badge_type', to='reg6.Ticket')),
                ('old_order', models.ForeignKey(related_name='old_order', to='reg6.Order')),
                ('old_ordered_items', models.ManyToManyField(related_name='old_ordered_items', to='reg6.Item', blank=True)),
            ],
            options={
                'permissions': (('view_upgrade', 'Can view upgrade'),),
            },
        ),
        migrations.CreateModel(
            name='ListAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='reg6.Answer')),
            ],
            bases=('reg6.answer',),
        ),
        migrations.CreateModel(
            name='ListQuestion',
            fields=[
                ('question_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='reg6.Question')),
            ],
            bases=('reg6.question',),
        ),
        migrations.CreateModel(
            name='TextAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='reg6.Answer')),
            ],
            bases=('reg6.answer',),
        ),
        migrations.CreateModel(
            name='TextQuestion',
            fields=[
                ('question_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='reg6.Question')),
                ('max_length', models.IntegerField()),
            ],
            bases=('reg6.question',),
        ),
        migrations.AddField(
            model_name='temporder',
            name='upgrade',
            field=models.ForeignKey(blank=True, to='reg6.Upgrade', null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='applies_to_items',
            field=models.ManyToManyField(to='reg6.Item', blank=True),
        ),
        migrations.AddField(
            model_name='question',
            name='applies_to_tickets',
            field=models.ManyToManyField(to='reg6.Ticket', blank=True),
        ),
        migrations.AddField(
            model_name='promocode',
            name='applies_to',
            field=models.ManyToManyField(to='reg6.Ticket', blank=True),
        ),
        migrations.AddField(
            model_name='item',
            name='applies_to',
            field=models.ManyToManyField(to='reg6.Ticket', blank=True),
        ),
        migrations.AddField(
            model_name='coupon',
            name='badge_type',
            field=models.ForeignKey(to='reg6.Ticket'),
        ),
        migrations.AddField(
            model_name='coupon',
            name='order',
            field=models.ForeignKey(to='reg6.Order'),
        ),
        migrations.AddField(
            model_name='attendee',
            name='answers',
            field=models.ManyToManyField(to='reg6.Answer', blank=True),
        ),
        migrations.AddField(
            model_name='attendee',
            name='badge_type',
            field=models.ForeignKey(to='reg6.Ticket'),
        ),
        migrations.AddField(
            model_name='attendee',
            name='order',
            field=models.ForeignKey(blank=True, to='reg6.Order', null=True),
        ),
        migrations.AddField(
            model_name='attendee',
            name='ordered_items',
            field=models.ManyToManyField(to='reg6.Item', blank=True),
        ),
        migrations.AddField(
            model_name='attendee',
            name='promo',
            field=models.ForeignKey(blank=True, to='reg6.PromoCode', null=True),
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(to='reg6.Question'),
        ),
    ]
