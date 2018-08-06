# Generated by Django 2.0.7 on 2018-07-31 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mails', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='papermail',
            name='receivers',
        ),
        migrations.RemoveField(
            model_name='papermail',
            name='sender',
        ),
        migrations.AddField(
            model_name='papermail',
            name='receivers_address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='papermail',
            name='sender_address',
            field=models.CharField(default='', max_length=50),
        ),
    ]