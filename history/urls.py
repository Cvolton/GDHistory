from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload, name='upload'),
    path('search/', views.search, name='search'),
    path('level/<online_id>/', views.view_level, name='level'),
    path('level/<online_id>/<record_id>/', views.view_level, name='level'),
    path('level/<online_id>/<record_id>/download/', views.download_record, name='download_record'),
    path('my_submissions/', views.my_submissions, name='my_submissions'),
    path('my_submissions/<show_all>/', views.my_submissions, name='all_submissions'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='accounts/logout.html'), name='logout'),
]