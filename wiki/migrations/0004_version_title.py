# Generated by Django 4.1.7 on 2023-03-07 22:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0003_alter_page_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='version',
            name='title',
            field=models.CharField(default='Narf', max_length=75),
            preserve_default=False,
        ),
    ]
