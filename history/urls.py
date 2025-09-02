from django.urls import path
from django.contrib.auth import views as auth_views

from . import views, api_views, authed_api_views, admin_views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload, name='upload'),
    path('upload_submission/', views.upload_submission, name='upload_submission'),
    path('search/', views.search, name='search'),
    path('daily/', views.daily, name='daily'),
    path('level/<online_id>/', views.view_level, name='level'),
    path('level/<online_id>/<record_id>/', views.view_level, name='level'),
    path('level/<online_id>/<record_id>/download/', views.download_record, name='download_record'),
    path('manual/<manual_id>/', views.view_manual, name='manual'),
    path('manual/<manual_id>/delete/', views.delete_manual, name='delete_manual'),
    path('submission/<save_id>/', views.view_submission, name='submission'),
    path('submission/<save_id>/<page>/', views.view_submission, name='submission'),
    path('submissions/', views.public_submissions, name='submissions'),
    path('my_submissions/', views.my_submissions, name='my_submissions'),
    path('my_submissions/<show_all>/', views.my_submissions, name='all_submissions'),
    path('my_manuals/', views.my_manuals, name='my_manuals'),
    path('my_manuals/<show_all>/', views.my_manuals, name='all_manuals'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='accounts/logout.html'), name='logout'),
    path('date_estimator/', views.date_estimator, name='date_estimator'),
    path('api/', views.api_documentation, name='api'),

    path('api/v1/counts/', api_views.index_counts, name='api_counts'),
    path('api/v1/recent/', api_views.index_levels, name='api_recent'),
    path('api/v1/user/<online_id>/', api_views.user_info, name='api_user'),
    path('api/v1/user/<online_id>/<view_mode>/', api_views.user_info, name='api_user'),
    path('api/v1/manual/<pk>/', api_views.manual_info, name='api_manual'),
    path('api/v1/level/<online_id>/', api_views.level_info, name='api_level'),
    path('api/v1/level/<online_id>/save/', api_views.save_level, name='api_level_save'),
    path('api/v1/level/<online_id>/record/', api_views.level_record, name='api_level_record'),
    path('api/v1/level/<online_id>/record/<record_id>/', api_views.level_record, name='api_level_record_id'),
    path('api/v1/level/<online_id>/<view_mode>/', api_views.level_info, name='api_level'),
    path('api/v1/date/user/<online_id>/', api_views.user_to_level_estimation, name='api_estimate_user'),
    path('api/v1/date/level/<online_id>/', api_views.level_date_estimation, name='api_estimate_level'),
    path('api/v1/date/comment/<level_id>/<comment_id>/', api_views.comment_date_estimation, name='api_estimate_comment'),
    path('api/v1/date/comment/<level_id>/<comment_id>/<estimation_type>/', api_views.comment_date_estimation, name='api_estimate_comment'),
    path('api/v1/date/date/<online_date>/', api_views.level_date_to_id_estimation, name='api_estimate_date'),
    path('api/v1/date/timestamp/<online_timestamp>/', api_views.level_timestamp_to_id_estimation, name='api_estimate_timestamp'),
    path('api/v1/search/level/advanced/', api_views.level_search, name='api_level_search'),
    path('api/v1/search/level/counts/', api_views.level_search_counts, name='api_level_search_counts'),
    path('api/v1/daily/', api_views.daily, name='api_daily'),
    path('api/v1/daily/current_year/', api_views.daily_current_year, name='api_daily_current_year'),

    path('api/v1/auth/levelrecord/<record_id>/sources/', authed_api_views.record_source_info, name='api_daily_current_year'),
    
    path('admin2/', admin_views.index, name='admin_index'),
    path('admin2/revalidate_all/', admin_views.revalidate_all, name='admin_revalidate_all'),
    path('admin2/search_update_all/', admin_views.search_update_all, name='admin_search_update_all'),
    path('admin2/force_username/', admin_views.force_username, name='admin_force_username'),

    #path('debug/<online_id>/', views.debug, name='debug'),
]