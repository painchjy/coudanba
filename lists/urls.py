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
    url(r'^view_order/(\d+)/$',views.view_order, name='view_order' ),
    url(r'^new_order/(\d+)/$',views.new_order, name='new_order' ),
    url(r'^users/(.+)/$',views.my_lists, name='my_lists' ),
    url(r'^loadusers/(\d+)/$',views.load_users, name='load_users' ),
    url(r'^order/(\d+)/$',views.order, name='order' ),
    url(r'^next_ju/(\d+)/$',views.next_ju, name='next_ju' ),
    url(r'^category$',views.category, name='category' ),
    url(r'^next_category/(\d+)/$',views.next_category, name='next_category' ),
]
