# Generated by Django 2.0.1 on 2018-05-18 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0020_auto_20180503_1626'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userpostrelevant',
            name='relevancy',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Default'), (1, 'Starred'), (2, 'Removed')], default=0),
        ),
    ]
