from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager

# Create your models here.


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        VISITANT = 'visitant', 'Visitante'
        ALUMNO = 'alumno', 'Alumno'
        ADMIN = 'admin', 'Administrador'

    class Idioma(models.TextChoices):
        ES = 'es', 'Español'
        EN = 'en', 'English'

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    position = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True, null=True)
    profession = models.CharField(max_length=255, blank=True, null=True)    
    prefer_language = models.CharField(max_length=5, choices=Idioma.choices, default=Idioma.ES)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VISITANT)
    accepted_consent = models.BooleanField(default=False)
    consent_date = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone', 'position']

    def __str__(self):
        return self.email

    def accept_consent(self):
        self.accepted_consent = True
        self.consent_date = timezone.now()
        self.save()

    def reject_consent(self):
        self.accepted_consent = False
        self.consent_date = None
        self.save()

    def is_admin(self):
        return self.role == self.Role.ADMIN