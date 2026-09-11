from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from .forms import LoginForm, RegisterForm


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class UserLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self.request.user.prefer_language
        enrollments = (
            self.request.user.enrollments
            .select_related('course')
            .order_by('-activation_date', '-id')
        )
        items = []
        for enrollment in enrollments:
            vigente = enrollment.is_in_effect()
            if enrollment.active_access and vigente:
                estado = 'Vigente'
            elif enrollment.active_access and not vigente:
                estado = 'Caducada'
            else:
                estado = 'Pendiente de activación'
            items.append({
                'enrollment': enrollment,
                'curso_titulo': enrollment.course.localized_titulo(lang),
                'estado': estado,
                'vigente': vigente,
            })
        context['enrollment_items'] = items
        return context

class UserPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')

class UserPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'

class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')

class UserPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'

class AccessDeniedView(TemplateView):
    template_name = 'accounts/access_denied.html'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.status_code = 403
        return response
