# Generated by Django 2.0.1 on 2018-04-03 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0009_auto_20180403_1440'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tracker',
            name='color',
            field=models.CharField(default='#e67e22', max_length=7),
        ),
    ]