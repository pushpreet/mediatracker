# Generated by Django 2.0.1 on 2018-04-02 05:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0005_auto_20180402_0020'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='main_image',
            field=models.URLField(max_length=500, null=True),
        ),
    ]
