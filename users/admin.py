from django.contrib import admin
from .models import UserRegistrationModel
from .models import CrimeReport

admin.site.register(UserRegistrationModel)
admin.site.register(CrimeReport)
