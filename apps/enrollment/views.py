from django.views.generic import TemplateView

# Create your views here.

class CursoHomeView(TemplateView):
    template_name = 'curso/home.html'