from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

class EnrollmentMiddleware:
    """
    Protege rutas bajo /curso/.
    - No autenticado → login
    - Staff/superuser → pasa
    - Autenticado sin matrícula vigente → 403 access_denied
    """

    PROTECTED_PREFIXES = ('/curso/',)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if not any(path.startswith(prefix) for prefix in self.PROTECTED_PREFIXES):
            return self.get_response(request)
        
        user = request.user

        if not user.is_authenticated:
            login_url = reverse('accounts:login')
            return redirect(f'{login_url}?next={path}')

        if user.is_staff or user.is_superuser:
            return self.get_response(request)

        vigente = user.enrollments.filter(
            active_access=True,
            expiration_date__gt=timezone.now()
        ).exists()

        if not vigente:
            return render(request, 'accounts/access_denied.html', status=403)
        
        return self.get_response(request)