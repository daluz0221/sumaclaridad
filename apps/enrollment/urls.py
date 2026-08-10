from django.urls import path

from .views import CursoHomeView

app_name = 'curso'

urlpatterns = [
    path('', CursoHomeView.as_view(), name='home'),
]