# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reg6', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='priority',
            field=models.IntegerField(default=0, help_text=b'Ordering priority, lower numbers first'),
            preserve_default=False,
        ),
    ]
