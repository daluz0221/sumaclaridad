from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import models
from django.utils import timezone

# Create your models here.


class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey('catalog.Course', on_delete=models.CASCADE, related_name='enrollments')
    active_access = models.BooleanField(default=False)
    activation_date = models.DateTimeField(blank=True, null=True)
    expiration_date = models.DateTimeField(blank=True, null=True)
    

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'course'],
                name='unique_enrollment_user_course'
            )
        ]

    def calculate_expiration_date(self, since=None):
        """Punto único de verdad para tests y admin."""
        base = since or self.activation_date or timezone.now()
        return base + relativedelta(months=6)

    def _assign_alumno_role(self):

        user = self.user
        if user.role != user.Role.ADMIN:
            user.role = user.Role.ALUMNO
            user.save(update_fields=['role'])

    def activate(self, when=None):
        when = when or timezone.now()
        self.active_access = True
        self.activation_date = when
        self.expiration_date = self.calculate_expiration_date(when)
        super().save()
        self._assign_alumno_role()

    def is_in_effect(self):
        if not self.active_access or not self.expiration_date:
            return False
        return timezone.now() < self.expiration_date

    def deactivate(self):
        self.active_access = False
        self.activation_date = None
        self.expiration_date = None
        super().save()

    def save(self, *args, **kwargs):
        if self.active_access and not self.activation_date:
            self.activation_date = timezone.now()
            self.expiration_date = self.calculate_expiration_date(self.activation_date)
        elif self.active_access and self.activation_date and not self.expiration_date:
            self.expiration_date = self.calculate_expiration_date(self.activation_date)
        
        is_new_activation = (
            self.active_access
            and self.pk is not None
        )

        previous_active = False
        if self.pk:
            previous_active = (
                Enrollment.objects.filter(pk=self.pk)
                .values_list('active_access', flat=True)
                .first()
            ) or False

        super().save(*args, **kwargs)

        if self.active_access and not previous_active:
            self._assign_alumno_role()