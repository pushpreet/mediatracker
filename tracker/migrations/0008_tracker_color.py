# Generated by Django 2.0.1 on 2018-04-02 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0007_auto_20180402_1553'),
    ]

    operations = [
        migrations.AddField(
            model_name='tracker',
            name='color',
            field=models.CharField(default='e67e22', max_length=6),
        ),
    ]