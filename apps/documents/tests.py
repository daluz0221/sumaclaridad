from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse
from pypdf import PdfReader
from reportlab.pdfgen import canvas

from apps.catalog.models import Course, Module, Resource
from apps.documents.services import watermark_pdf
from apps.enrollment.models import Enrollment, ModuleCompletion, Certificate

User = get_user_model()


def _minimal_pdf_bytes():
    buf = BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, 'Pagina base')
    c.showPage()
    c.drawString(72, 720, 'Segunda pagina')
    c.save()
    return buf.getvalue()


class WatermarkTests(TestCase):
    def test_marca_nombre_email_fecha_en_todas_las_paginas(self):
        marked = watermark_pdf(_minimal_pdf_bytes(), 'Ana Perez', 'ana@test.com')
        reader = PdfReader(BytesIO(marked))
        self.assertEqual(len(reader.pages), 2)
        for page in reader.pages:
            text = page.extract_text() or ''
            self.assertIn('Ana Perez', text)
            self.assertIn('ana@test.com', text)


class PdfDownloadGuardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='alum@test.com',
            password='Secreta123!',
            name='Alumno',
            phone='3001234567',
            position='Jefe',
        )
        self.course = Course.objects.create(slug='jefes-a-punto', titulo_es='Jefes a Punto')
        self.module = Module.objects.create(
            course=self.course, slug='bienvenida', order=1, titulo_es='Bienvenida',
        )
        self.resource = Resource.objects.create(
            module=self.module,
            tipo=Resource.Tipo.PDF,
            order=1,
            titulo_es='Guia',
            pdf_ref='pdfs/jefes-a-punto/bienvenida/guia-1.pdf',
        )
        self.url = reverse(
            'curso:pdf_download',
            kwargs={
                'course_slug': self.course.slug,
                'module_slug': self.module.slug,
                'resource_id': self.resource.pk,
            },
        )

    def test_anonimo_va_a_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_sin_matricula_403(self):
        self.client.login(email='alum@test.com', password='Secreta123!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @patch('apps.documents.views.issue_watermarked_download', return_value='https://signed.example/file.pdf')
    def test_matricula_vigente_redirige_a_url_firmada(self, _mock):
        enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        enrollment.activate()
        self.client.login(email='alum@test.com', password='Secreta123!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://signed.example/file.pdf')

    def test_pending_es_404(self):
        self.resource.pdf_ref = 'pending://bienvenida-pdf-1'
        self.resource.save(update_fields=['pdf_ref'])
        enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        enrollment.activate()
        self.client.login(email='alum@test.com', password='Secreta123!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

class CertificatePdfTests(TestCase):
    def test_pdf_en_espanol_muestra_codigo(self):
        from apps.documents.services import render_certificate_pdf
        raw = render_certificate_pdf('Ana Perez', 'Jefes a Punto', 'abc123', 'es')
        text = '\n'.join((page.extract_text() or '') for page in PdfReader(BytesIO(raw)).pages)
        self.assertIn('Certificado', text)
        self.assertIn('Ana Perez', text)
        self.assertIn('Jefes a Punto', text)
        self.assertIn('abc123', text)

    def test_pdf_en_ingles(self):
        from apps.documents.services import render_certificate_pdf
        raw = render_certificate_pdf('Ana Perez', 'Leaders Ready', 'abc123', 'en')
        text = '\n'.join((page.extract_text() or '') for page in PdfReader(BytesIO(raw)).pages)
        self.assertIn('Certificate', text)
        self.assertIn('Leaders Ready', text)
        self.assertIn('abc123', text)


class CertificateDownloadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='cert-dl@test.com',
            password='Secreta123!',
            name='Ana Perez',
            phone='3001234567',
            position='Jefe',
        )
        self.course = Course.objects.create(
            slug='jefes-a-punto',
            titulo_es='Jefes a Punto',
            titulo_en='Leaders Ready',
        )
        self.module = Module.objects.create(
            course=self.course, slug='bienvenida', order=1, titulo_es='Bienvenida',
        )
        self.enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        self.enrollment.activate()
        self.url = reverse('curso:certificate_download', kwargs={'course_slug': self.course.slug})

    def test_pendiente_responde_403(self):
        self.client.login(email='cert-dl@test.com', password='Secreta123!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @patch('apps.documents.views.presigned_download_url', return_value='https://signed.example/cert.pdf')
    def test_todos_aprobados_redirige_a_url_firmada(self, _mock):
        ModuleCompletion.objects.filter(enrollment=self.enrollment).update(
            estado=ModuleCompletion.Estado.APROBADO,
        )
        Certificate.objects.create(
            enrollment=self.enrollment,
            idioma='es',
            codigo='abc123',
            generado_en=timezone.now(),
            s3_key='certificates/1/abc123.pdf',
        )
        self.client.login(email='cert-dl@test.com', password='Secreta123!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://signed.example/cert.pdf')

    def test_rechazado_no_descarga_aunque_exista_el_pdf(self):
        ModuleCompletion.objects.filter(enrollment=self.enrollment).update(
            estado=ModuleCompletion.Estado.RECHAZADO,
        )
        Certificate.objects.create(
            enrollment=self.enrollment,
            idioma='es',
            codigo='abc123',
            generado_en=timezone.now(),
            s3_key='certificates/1/abc123.pdf',
        )
        self.client.login(email='cert-dl@test.com', password='Secreta123!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)