# Generated by Django 2.0.1 on 2018-04-02 10:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0006_auto_20180402_1035'),
    ]

    operations = [
        migrations.RenameField(
            model_name='post',
            old_name='site',
            new_name='site_full',
        ),
    ]