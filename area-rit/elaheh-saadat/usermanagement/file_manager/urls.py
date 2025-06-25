from django.urls import path
from .views import (
    user_login, user_logout, admin_dashboard, regular_dashboard, 
    list_files_view,
    view_file_view,
    download_file_view,
    list_metadata_files_view,
    edit_metadata_view,
    save_metadata_view,
    delete_file_view,
    homepage_view,
    new_experiment_view,
)

urlpatterns = [
    path('login/', user_login, name='login'),  # Login page
    path('logout/', user_logout, name='logout'),  # Logout
    path('dashboard/admin/', admin_dashboard, name='admin_dashboard'),  # Admin dashboard
    path('dashboard/regular/', regular_dashboard, name='regular_dashboard'),  # Regular user dashboard
    path('files/', list_files_view, name='file_list'),
    path('files/<str:file_name>/', view_file_view, name='view_file'),
    path('files/download/<str:file_name>/', download_file_view, name='download_file'),
    path('edit-metadata/', edit_metadata_view, name='edit_metadata'),
    path('metadata/', list_metadata_files_view, name='list_metadata_files'),
    path('metadata/<str:file_name>/edit/', edit_metadata_view, name='edit_metadata'),   
    path('metadata/save/', save_metadata_view, name='save_metadata'),
    path('delete_file/', delete_file_view, name='delete_file'),
    path('new-experiment/', new_experiment_view, name='new_experiment'),
]

