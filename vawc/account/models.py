from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager

# Custom User model with email-based authentication
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username',)

    objects = UserManager()
    def __str__(self):
        return self.username

class Account(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=100)
    YES, NO = 'Yes', 'No'
    VERIFIED_CHOICES = [(YES, 'Yes'), (NO, 'No')]
    verified = models.CharField(
        max_length=3,
        choices=VERIFIED_CHOICES,
        null=True,
        blank=True,
        default=NO
    )

    ADMIN, STAFF = 'admin', 'staff'
    TYPE_CHOICES = [(ADMIN, 'Admin'), (STAFF, 'Staff')]
    type = models.CharField(
        max_length=5,
        choices=TYPE_CHOICES,
        default=STAFF
    )

    def __str__(self):
        return self.user.username
