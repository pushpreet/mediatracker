# Generated by Django 2.0.1 on 2018-05-02 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0014_auto_20180430_1717'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='author',
            field=models.CharField(max_length=500),
        ),
    ]
