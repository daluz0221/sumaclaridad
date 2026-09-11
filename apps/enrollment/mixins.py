from django.shortcuts import get_object_or_404, render
from apps.catalog.models import Course
from apps.enrollment.models import Enrollment

class CourseEnrollmentRequiredMixin:
    """Exige matrícula vigente del curso de la URL. Staff pasa."""

    course_slug_url_kwarg = 'course_slug'

    def dispatch(self, request, *args, **kwargs):
        courses = Course.objects.all()
        if not (request.user.is_staff or request.user.is_superuser):
            courses = courses.filter(is_published=True)
        self.course = get_object_or_404(
            courses,
            slug=kwargs[self.course_slug_url_kwarg],
        )

        if request.user.is_staff or request.user.is_superuser:
            self.enrollment = (
                Enrollment.objects.filter(
                    user=request.user,
                    course=self.course,
                ).first()
            )

            return super().dispatch(request, *args, **kwargs)

        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=self.course,
        ).first()

        if not enrollment or not enrollment.is_in_effect():
            return render(request, "accounts/access_denied.html", status=403)

        self.enrollment = enrollment
        return super().dispatch(request, *args, **kwargs)