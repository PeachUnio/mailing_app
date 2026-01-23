from django.urls import path, include
from django.views.decorators.cache import cache_page

from mailing.apps import MailingConfig


app_name = MailingConfig.name

urlpatterns = [

]