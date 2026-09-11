from django.contrib import admin


from .models import Enrollment

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
