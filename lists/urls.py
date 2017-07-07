"""superlists URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
#from django.contrib import admin
from lists import views

urlpatterns = [
    url(r'^new$',views.new_list, name='new_list' ),
    url(r'^(\d+)/$',views.view_list, name='view_list' ),
    url(r'^users/(.+)/$',views.my_lists, name='my_lists' ),
    url(r'^loadusers/(\d+)/$',views.load_users, name='load_users' ),
    url(r'^manage_ju/(\d+)/$',views.manage_ju, name='manage_ju' ),
    url(r'^order/(\d+)/$',views.order, name='order' ),
    url(r'^jus/(\d+)/$',views.view_ju, name='view_ju' ),
    url(r'^jus/new/$',views.new_ju, name='new_ju' ),
    url(r'^jus/$',views.list_jus, name='list_jus' ),
]
