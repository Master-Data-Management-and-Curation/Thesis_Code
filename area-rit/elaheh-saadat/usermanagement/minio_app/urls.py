"""
URL configuration for minio_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from file_manager.views import homepage_view

def redirect_to_login(request):
    """Redirects unauthenticated users to the login page"""
    return redirect('/login/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_login),  # Redirect root (/) to login
    path('', include('file_manager.urls')),  # Include app URLs
]
