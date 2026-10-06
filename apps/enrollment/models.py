import uuid

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

    def __str__(self):
        return f'{self.user.name} ({self.user.email}) — {self.course}'

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
        self.ensure_module_completions()
        self.issue_certificate_if_ready()

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
            self.ensure_module_completions()
            self.issue_certificate_if_ready()

    def ensure_module_completions(self):
        for module in self.course.modules.all():
            ModuleCompletion.objects.get_or_create(enrollment=self, module=module)

    def all_modules_approved(self):
        total = self.course.modules.count()
        if total == 0:
            return False
        approved = self.module_completions.filter(
            estado=ModuleCompletion.Estado.APROBADO,
            module__course=self.course
        ).count()
        return approved == total

    def issue_certificate_if_ready(self):
        if not self.is_in_effect() or not self.all_modules_approved():
            return None
        try:
            return self.certificate
        except Certificate.DoesNotExist:
            pass

        from apps.documents.services import render_certificate_pdf, store_certificate_pdf
        idioma = self.user.prefer_language if self.user.prefer_language in ('es', 'en') else 'es'
        codigo = uuid.uuid4().hex
        pdf_bytes = render_certificate_pdf(
            name=self.user.name,
            course_title=self.course.localized_titulo(idioma),
            codigo=codigo,
            idioma=idioma,
        )
        s3_key = store_certificate_pdf(pdf_bytes, self.pk, codigo)
        return Certificate.objects.create(
            enrollment=self,
            s3_key=s3_key,
            codigo=codigo,
            idioma=idioma,
            generado_en=timezone.now(),
        )


class ModuleCompletion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        APROBADO = 'aprobado', 'Aprobado'
        RECHAZADO = 'rechazado', 'Rechazado'

    enrollment = models.ForeignKey('Enrollment', on_delete=models.CASCADE, related_name='module_completions')
    module = models.ForeignKey('catalog.Module', on_delete=models.CASCADE, related_name='completions')
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    aprobado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='module_approvals', blank=True, null=True)
    fecha_aprobacion = models.DateTimeField(blank=True, null=True)
    notas_admin = models.TextField(blank=True, null=True, default='')

    class Meta:
        verbose_name = 'avance de módulo'
        verbose_name_plural = 'avances de módulo'
        constraints = [
            models.UniqueConstraint(
                fields=['enrollment', 'module'],
                name='unique_module_completion_enrollment_module'
            ),
        ]

    def __str__(self):
        return (
            f'{self.enrollment.user.name} — {self.module.titulo_es} '
            f'({self.get_estado_display()})'
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.estado == self.Estado.APROBADO:
            self.enrollment.issue_certificate_if_ready()


class Certificate(models.Model):
    
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='certificate',
    )
    idioma = models.CharField(max_length=5, choices=[('es', 'Español'), ('en', 'English')])
    codigo = models.CharField(max_length=255, unique=True)
    generado_en = models.DateTimeField()
    s3_key = models.CharField(max_length=255)

    def __str__(self):
        return self.codigo
