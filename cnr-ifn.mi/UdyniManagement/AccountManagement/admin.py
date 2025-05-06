from django.contrib import admin

# Register Permission model
from django.contrib.auth.models import Permission
admin.site.register(Permission)

# Register your models here
from AccountManagement.models import RegistrationRequest
admin.site.register(RegistrationRequest)
