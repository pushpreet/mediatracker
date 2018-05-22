# Generated by Django 2.0.1 on 2018-05-22 06:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0021_auto_20180518_1809'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='author',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='post',
            name='site_full',
            field=models.URLField(max_length=512),
        ),
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='post',
            name='url',
            field=models.URLField(max_length=512),
        ),
    ]
