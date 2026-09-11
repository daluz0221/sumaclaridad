from django.http import Http404
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView
from apps.catalog.models import Course, Module, Resource
from apps.enrollment.mixins import CourseEnrollmentRequiredMixin
from apps.enrollment.models import Enrollment

def _lang(user):
    return getattr(user, 'prefer_language', 'es') or 'es'

def _published(qs, user):
    if user.is_staff or user.is_superuser:
        return qs
    
    return qs.filter(is_published=True)

class CursoHomeView(TemplateView):
    template_name = 'curso/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        lang = _lang(user)

        if user.is_staff or user.is_superuser:
            courses = Course.objects.all()
            courses = _published(courses, user)
        else:
            course_ids = Enrollment.objects.filter(
                user=user,
                active_access=True,
                expiration_date__gt=timezone.now(),
            ).values_list('course_id', flat=True)
            courses = Course.objects.filter(pk__in=course_ids)
            courses = _published(courses, user)
        labeled = []
        for course in courses:
            labeled.append({
                'course': course,
                'titulo': course.localized_titulo(lang),
                'descripcion': course.localized_descripcion(lang),
            })

        context['courses'] = labeled
        context['lang'] = lang
        return context

class CourseModuleListView(CourseEnrollmentRequiredMixin, ListView):
    template_name = 'curso/modules_list.html'
    context_object_name = 'modules'

    def get_queryset(self):
        qs = self.course.modules.all()
        return _published(qs, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = _lang(self.request.user)
        context['lang'] = lang
        context['course'] = self.course
        context['enrollment'] = self.enrollment
        context['course_titulo'] = self.course.localized_titulo(lang)
        context['course_descripcion'] = self.course.localized_descripcion(lang)
        labeled_modules = []
        for module in context['modules']:
            labeled_modules.append({
                'module': module,
                'titulo': module.localized_titulo(lang),
            })
        context['module_items'] = labeled_modules
        return context

class ModuleDetailView(CourseEnrollmentRequiredMixin, DetailView):
    template_name = 'curso/module_detail.html'
    context_object_name = 'module'

    def get_queryset(self):
        qs = Module.objects.filter(course=self.course)
        return _published(qs, self.request.user)

    def get_object(self, queryset=None):
        queryset = queryset or self.get_queryset()
        try:
            return queryset.get(slug=self.kwargs['module_slug'])
        except Module.DoesNotExist:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = _lang(self.request.user)
        resources = self.object.resources.all()
        resources = _published(resources, self.request.user)
        context['lang'] = lang
        context['course'] = self.course
        context['enrollment'] = self.enrollment
        context['resources'] = resources
        context['videos'] = [r for r in resources if r.tipo == Resource.Tipo.VIDEO]
        context['textos'] = [r for r in resources if r.tipo == Resource.Tipo.TEXTO]
        context['pdfs'] = [r for r in resources if r.tipo == Resource.Tipo.PDF]
        context['course_titulo'] = self.course.localized_titulo(lang)
        context['module_titulo'] = self.object.localized_titulo(lang)
        context['module_intro'] = self.object.localized_intro(lang)
        def pack(res_list):
            packed = []
            for r in res_list:
                packed.append({
                    'resource': r,
                    'titulo': r.localized_titulo(lang),
                    'texto': r.localized_texto(lang),
                })
            return packed
        context['video_items'] = pack(context['videos'])
        context['texto_items'] = pack(context['textos'])
        context['pdf_items'] = pack(context['pdfs'])
        return context