from django.conf.urls import url
from wechat import views

urlpatterns = [
    url(r'^check$',views.check, name='check' ),
]
