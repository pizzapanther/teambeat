# Generated by Django 4.1.4 on 2022-12-29 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0013_remove_team_owners_team_org'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='view_ratings',
            field=models.BooleanField(default=False),
        ),
    ]
