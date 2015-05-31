# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
from jsonfield import JSONField

from connected_accounts.provider_pool import providers


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('provider', models.CharField(max_length=50, verbose_name='Provider', choices=providers.as_choices())),
                ('uid', models.CharField(max_length=255, verbose_name='UID')),
                ('last_login', models.DateTimeField(auto_now=True, verbose_name='Last login')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Date added')),
                ('raw_token', models.TextField(editable=False)),
                ('oauth_token', models.TextField(help_text='"oauth_token" (OAuth1) or access token (OAuth2)', verbose_name='OAuth Token')),
                ('oauth_token_secret', models.TextField(help_text='"oauth_token_secret" (OAuth1) or refresh token (OAuth2)', null=True, verbose_name='OAuth Token Secret', blank=True)),
                ('extra_data', JSONField(verbose_name='Extra data', editable=False)),
                ('expires_at', models.DateTimeField(null=True, verbose_name='Expires at', blank=True)),
                ('user', models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'ordering': ('-last_login',),
            },
            bases=(models.Model,),
        ),
    ]
