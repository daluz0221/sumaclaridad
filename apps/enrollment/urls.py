from django.urls import path

from apps.documents.views import PdfDownloadView

from .views import CourseModuleListView, CursoHomeView, ModuleDetailView

app_name = 'curso'

urlpatterns = [
    path('', CursoHomeView.as_view(), name='home'),
    path('<slug:course_slug>/', CourseModuleListView.as_view(), name='module_list'),
    path(
        '<slug:course_slug>/<slug:module_slug>/pdf/<int:resource_id>/',
        PdfDownloadView.as_view(),
        name='pdf_download',
    ),
    path(
        '<slug:course_slug>/<slug:module_slug>/',
        ModuleDetailView.as_view(),
        name='module_detail',
    ),
]