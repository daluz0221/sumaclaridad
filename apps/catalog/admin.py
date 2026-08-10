from django.contrib import admin

from .models import Course

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'slug')
    prepopulated_fields = {'slug': ('titulo',)}
    search_fields = ('titulo', 'slug')