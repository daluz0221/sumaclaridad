from django.urls import path

from .views import CourseModuleListView, CursoHomeView, ModuleDetailView

app_name = 'curso'

urlpatterns = [
    path('', CursoHomeView.as_view(), name='home'),
    path('<slug:course_slug>/', CourseModuleListView.as_view(), name='module_list'),
    path(
        '<slug:course_slug>/<slug:module_slug>/',
        ModuleDetailView.as_view(),
        name='module_detail',
    ),
]