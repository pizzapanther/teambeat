# Generated by Django 4.1.4 on 2022-12-29 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0014_member_view_ratings'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='report_status',
            field=models.BooleanField(default=True),
        ),
    ]