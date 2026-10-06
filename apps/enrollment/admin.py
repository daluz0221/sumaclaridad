from django.contrib import admin
from django.utils import timezone

from .models import Certificate, Enrollment, ModuleCompletion


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'course',
        'active_access',
        'activation_date',
        'expiration_date',
        'vigente',
    )
    list_filter = ('active_access', 'course')
    search_fields = ('user__email', 'user__name', 'course__titulo_es', 'course__slug')
    autocomplete_fields = ('user', 'course')
    readonly_fields = ('expiration_date',)
    actions = ('activar_matriculas', 'desactivar_matriculas')

    @admin.display(boolean=True, description='Vigente')
    def vigente(self, obj):
        return obj.is_in_effect()

    @admin.action(description='Activar matrículas (6 meses + role alumno)')
    def activar_matriculas(self, request, queryset):
        for enrollment in queryset:
            enrollment.activate()
        self.message_user(request, f'{queryset.count()} matrícula(s) activada(s).')

    @admin.action(description='Desactivar matrículas')
    def desactivar_matriculas(self, request, queryset):
        for enrollment in queryset:
            enrollment.deactivate()
        self.message_user(request, f'{queryset.count()} matrícula(s) desactivada(s).')


@admin.register(ModuleCompletion)
class ModuleCompletionAdmin(admin.ModelAdmin):
    list_display = (
        'enrollment',
        'module',
        'estado',
        'aprobado_por',
        'fecha_aprobacion',
    )
    list_filter = ('estado', 'enrollment__course')
    search_fields = (
        'enrollment__user__email',
        'enrollment__user__name',
        'module__titulo_es',
        'notas_admin',
    )
    autocomplete_fields = ('enrollment', 'module', 'aprobado_por')
    actions = ('aprobar', 'rechazar')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'enrollment__user',
            'enrollment__course',
            'module',
            'aprobado_por',
        )

    def save_model(self, request, obj, form, change):
        if 'estado' in form.changed_data:
            if obj.estado == ModuleCompletion.Estado.APROBADO:
                obj.aprobado_por = request.user
                obj.fecha_aprobacion = timezone.now()
            elif obj.estado == ModuleCompletion.Estado.RECHAZADO:
                obj.aprobado_por = None
                obj.fecha_aprobacion = None
        super().save_model(request, obj, form, change)

    @admin.action(description='Aprobar módulos seleccionados')
    def aprobar(self, request, queryset):
        now = timezone.now()
        for row in queryset:
            row.estado = ModuleCompletion.Estado.APROBADO
            row.aprobado_por = request.user
            row.fecha_aprobacion = now
            row.save()
        self.message_user(request, f'{queryset.count()} módulo(s) aprobado(s).')

    @admin.action(description='Rechazar módulos seleccionados')
    def rechazar(self, request, queryset):
        for row in queryset:
            row.estado = ModuleCompletion.Estado.RECHAZADO
            row.aprobado_por = None
            row.fecha_aprobacion = None
            row.save()
        self.message_user(request, f'{queryset.count()} módulo(s) rechazado(s).')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'enrollment', 'idioma', 'generado_en', 's3_key')
    search_fields = ('codigo', 'enrollment__user__email')
    readonly_fields = ('enrollment', 'idioma', 'codigo', 'generado_en', 's3_key')

    def has_add_permission(self, request):
        return False