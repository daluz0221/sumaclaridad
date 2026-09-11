from django.contrib import admin

from .models import Course, Module, Resource


class ResourceInline(admin.TabularInline):
    model = Resource
    extra = 1
    fields = (
        'tipo',
        'order',
        'titulo_es',
        'titulo_en',
        'texto_es',
        'texto_en',
        'video_ref',
        'pdf_ref',
        'is_published',
    )


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    fields = ('order', 'slug', 'titulo_es', 'titulo_en', 'is_published')
    prepopulated_fields = {'slug': ('titulo_es',)}
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('titulo_es', 'slug', 'is_published')
    list_filter = ('is_published',)
    search_fields = ('titulo_es', 'titulo_en', 'slug')
    prepopulated_fields = {'slug': ('titulo_es',)}
    inlines = [ModuleInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('titulo_es', 'course', 'order', 'is_published')
    list_filter = ('course', 'is_published')
    search_fields = ('titulo_es', 'slug', 'course__titulo_es')
    prepopulated_fields = {'slug': ('titulo_es',)}
    autocomplete_fields = ('course',)
    inlines = [ResourceInline]


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('titulo_es', 'tipo', 'module', 'order', 'is_published')
    list_filter = ('tipo', 'is_published', 'module__course')
    search_fields = ('titulo_es', 'module__titulo_es')
    autocomplete_fields = ('module',)