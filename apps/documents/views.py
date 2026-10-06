from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.utils.text import slugify

from apps.catalog.models import Resource
from apps.documents.services import (
    is_s3_pdf_key,
    issue_watermarked_download,
    presigned_download_url,
)
from apps.enrollment.mixins import CourseEnrollmentRequiredMixin

class PdfDownloadView(CourseEnrollmentRequiredMixin, View):
    def get(self, request, course_slug, module_slug, resource_id):
        qs = Resource.objects.filter(
            pk=resource_id,
            tipo=Resource.Tipo.PDF,
            module__course=self.course,
            module__slug=module_slug,
        )
        if not (request.user.is_staff or request.user.is_superuser):
            qs = qs.filter(is_published=True, module__is_published=True)

        resource = qs.first()
        if resource is None or not is_s3_pdf_key(resource.pdf_ref):
            raise Http404

        lang = getattr(request.user, 'prefer_language', 'es') or 'es'
        parts = [
            resource.localized_titulo(lang),
            self.course.localized_titulo(lang),
            resource.module.localized_titulo(lang),
        ]
        stem = '-'.join(slugify(part) for part in parts if part)
        filename = f'{stem or "recurso"}.pdf'
        url = issue_watermarked_download(
            base_key=resource.pdf_ref,
            user=request.user,
            resource_id=resource.id,
            filename=filename,
        )
        return HttpResponseRedirect(url)

class CertificateDownloadView(CourseEnrollmentRequiredMixin, View):
    def get(self, request, course_slug):
        enrollment = self.enrollment
        allowed = (
            enrollment is not None
            and enrollment.is_in_effect()
            and enrollment.all_modules_approved()
        )
        if not allowed:
            return render(request, 'accounts/access_denied.html', status=403)

        certificate = enrollment.issue_certificate_if_ready()
        if certificate is None or not certificate.s3_key:
            return render(request, 'accounts/access_denied.html', status=403)

        lang = certificate.idioma if certificate.idioma in ('es', 'en') else 'es'
        filename = f'{slugify(self.course.localized_titulo(lang)) or "certificado"}.pdf'
        url = presigned_download_url(certificate.s3_key, filename)
        return HttpResponseRedirect(url)