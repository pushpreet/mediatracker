# Generated by Django 2.0.1 on 2018-05-03 10:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0019_tracker_auto_refresh'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='main_image',
            field=models.URLField(max_length=1024, null=True),
        ),
    ]
