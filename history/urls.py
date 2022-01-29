from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload', views.upload, name='upload'),
    path('search', views.search, name='search'),
    path('level/<online_id>', views.view_level, name='level'),
    path('level/<online_id>/<record_id>/download', views.download_record, name='download_record'),
    path('accounts/login/', views.login_page_placeholder, name='login'),
]