# Generated by Django 2.0.3 on 2018-04-01 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0002_auto_20180402_0013'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='domain_rank',
            field=models.PositiveSmallIntegerField(null=True),
        ),
    ]
