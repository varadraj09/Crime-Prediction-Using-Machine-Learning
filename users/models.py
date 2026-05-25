from django.db import models

# Create your models here.
class UserRegistrationModel(models.Model):
    name = models.CharField(max_length=100)
    loginid = models.CharField(unique=True, max_length=100)
    password = models.CharField(max_length=100)
    mobile = models.CharField(unique=True, max_length=100)
    email = models.CharField(unique=True, max_length=100)
    locality = models.CharField(max_length=100)
    address = models.CharField(max_length=1000)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    status = models.CharField(max_length=100)

    def __str__(self):
        return self.loginid

    class Meta:
        db_table = 'UserRegistrations'

class CrimeReport(models.Model):

    city=models.CharField(
        max_length=100,
        default='Unknown'
    )

    crime_type=models.CharField(
        max_length=100,
        default='Unknown'
    )

    location=models.CharField(
        max_length=200,
        default='Unknown'
    )

    date=models.DateField(
        default='2026-01-01'
    )

    description=models.TextField(
        default='Unknown'
    )

    def __str__(self):
        return self.city     


