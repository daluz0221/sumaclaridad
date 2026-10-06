

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Course, Module
from apps.enrollment.models import Enrollment, ModuleCompletion, Certificate

User = get_user_model()


class EnrollmentCaducidadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='alum@test.com',
            password='Secreta123!',
            name='Alumno',
            phone='3001234567',
            position='Jefe',
        )
        self.course = Course.objects.create(
            slug='jefes-a-punto',
            titulo_es='Jefes a Punto',
            titulo_en='Leaders Ready',
        )
        self.enrollment = Enrollment.objects.create(
            user=self.user,
            course=self.course,
        )

    def test_activate_sets_expiration_plus_6_months(self):
        when = timezone.now()
        self.enrollment.activate(when=when)

        self.enrollment.refresh_from_db()
        self.user.refresh_from_db()

        self.assertTrue(self.enrollment.active_access)
        self.assertEqual(self.enrollment.activation_date, when)
        self.assertEqual(
            self.enrollment.expiration_date,
            when + relativedelta(months=6),
        )
        self.assertEqual(self.user.role, User.Role.ALUMNO)
        self.assertTrue(self.enrollment.is_in_effect())

    def test_save_with_active_access_calculates_dates(self):
        self.enrollment.active_access = True
        self.enrollment.activation_date = None
        self.enrollment.expiration_date = None
        self.enrollment.save()

        self.enrollment.refresh_from_db()
        self.assertIsNotNone(self.enrollment.activation_date)
        self.assertEqual(
            self.enrollment.expiration_date,
            self.enrollment.calculate_expiration_date(self.enrollment.activation_date),
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Role.ALUMNO)

    def test_is_in_effect_false_when_expired(self):
        past = timezone.now() - relativedelta(months=7)
        self.enrollment.activate(when=past)
        # forzar caducidad en el pasado por si el reloj molesta
        self.enrollment.expiration_date = timezone.now() - relativedelta(days=1)
        Enrollment.objects.filter(pk=self.enrollment.pk).update(
            expiration_date=self.enrollment.expiration_date,
            active_access=True,
        )
        self.enrollment.refresh_from_db()
        self.assertFalse(self.enrollment.is_in_effect())

    def test_activate_does_not_downgrade_admin_role(self):
        admin = User.objects.create_superuser(
            email='admin@test.com',
            password='Secreta123!',
            name='Admin',
            phone='3000000000',
            position='Admin',
        )
        enrollment = Enrollment.objects.create(user=admin, course=self.course)
        enrollment.activate()
        admin.refresh_from_db()
        self.assertEqual(admin.role, User.Role.ADMIN)


class CursoAccessGuardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='guard@test.com',
            password='Secreta123!',
            name='Guard',
            phone='3005556677',
            position='Cargo',
        )
        self.course = Course.objects.create(slug='demo', titulo_es='Demo', titulo_en='Demo')
        self.url = reverse('curso:home')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_authenticated_without_enrollment_gets_403(self):
        self.client.login(email='guard@test.com', password='Secreta123!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_with_active_enrollment_ok(self):
        enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        enrollment.activate()
        self.client.login(email='guard@test.com', password='Secreta123!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

class CursoNavegacionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='nav@test.com',
            password='Secreta123!',
            name='Nav',
            phone='3001112233',
            position='Jefe',
        )
        self.course = Course.objects.create(
            slug='jefes-a-punto',
            titulo_es='Jefes a Punto',
            is_published=True,
        )
        self.other = Course.objects.create(
            slug='otro-curso',
            titulo_es='Otro curso',
            is_published=True,
        )
        from apps.catalog.models import Module, Resource
        self.mod1 = Module.objects.create(
            course=self.course,
            slug='bienvenida',
            order=1,
            titulo_es='Bienvenida',
            intro_es='Intro 1',
            is_published=True,
        )
        self.mod2 = Module.objects.create(
            course=self.course,
            slug='comunicacion',
            order=2,
            titulo_es='Comunicación',
            intro_es='Intro 2',
            is_published=True,
        )
        Module.objects.create(
            course=self.course,
            slug='borrador',
            order=3,
            titulo_es='Borrador',
            is_published=False,
        )
        Resource.objects.create(
            module=self.mod1,
            tipo=Resource.Tipo.VIDEO,
            order=1,
            titulo_es='Video 1',
            video_ref='pending://bienvenida-video-1',
        )
        Resource.objects.create(
            module=self.mod1,
            tipo=Resource.Tipo.PDF,
            order=2,
            titulo_es='PDF 1',
            pdf_ref='pending://bienvenida-pdf-1',
        )
        Resource.objects.create(
            module=self.mod1,
            tipo=Resource.Tipo.PDF,
            order=3,
            titulo_es='PDF 2',
            pdf_ref='pending://bienvenida-pdf-2',
        )
        self.list_url = reverse('curso:module_list', kwargs={'course_slug': self.course.slug})
        self.detail_url = reverse(
            'curso:module_detail',
            kwargs={'course_slug': self.course.slug, 'module_slug': self.mod1.slug},
        )
        self.other_url = reverse('curso:module_list', kwargs={'course_slug': self.other.slug})
    def _login_activo(self):
        enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        enrollment.activate()
        self.client.login(email='nav@test.com', password='Secreta123!')
        return enrollment
    def test_alumno_activo_ve_todos_los_modulos_publicados(self):
        self._login_activo()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        slugs = [item['module'].slug for item in response.context['module_items']]
        self.assertEqual(slugs, ['bienvenida', 'comunicacion'])
        self.assertNotIn('borrador', slugs)
    def test_detalle_muestra_intro_video_y_varios_pdf(self):
        self._login_activo()
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Intro 1')
        self.assertEqual(len(response.context['video_items']), 1)
        self.assertEqual(len(response.context['pdf_items']), 2)
    def test_modulo_no_publicado_es_404(self):
        self._login_activo()
        url = reverse(
            'curso:module_detail',
            kwargs={'course_slug': self.course.slug, 'module_slug': 'borrador'},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    def test_alumno_de_otro_curso_no_entra(self):
        self._login_activo()
        response = self.client.get(self.other_url)
        self.assertEqual(response.status_code, 403)
    def test_caducado_no_entra_al_listado(self):
        enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        enrollment.activate()
        Enrollment.objects.filter(pk=enrollment.pk).update(
            expiration_date=timezone.now() - relativedelta(days=1),
        )
        self.client.login(email='nav@test.com', password='Secreta123!')
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 403)
    def test_anonimo_sigue_yendo_a_login(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_curso_no_publicado_es_404(self):
        self.course.is_published = False
        self.course.save(update_fields=['is_published'])
        self._login_activo()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 404)

class ModuleApprovalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='cert@test.com',
            password='Secreta123!',
            name='Ana Perez',
            phone='3001234567',
            position='Jefe',
        )
        self.admin = User.objects.create_superuser(
            email='admin-cert@test.com',
            password='Secreta123!',
            name='Admin',
            phone='3000000000',
            position='Admin',
        )
        self.course = Course.objects.create(slug='jefes-a-punto', titulo_es='Jefes a Punto', titulo_en='Leaders Ready')
        self.module_a = Module.objects.create(course=self.course, slug='bienvenida', order=1, titulo_es='Bienvenida')
        self.module_b = Module.objects.create(course=self.course, slug='cierre', order=2, titulo_es='Cierre')
        self.enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        self.enrollment.activate()

    def test_nombres_describen_alumno_curso_y_modulo(self):
        row = ModuleCompletion.objects.get(enrollment=self.enrollment, module=self.module_a)
        self.assertEqual(str(self.enrollment), 'Ana Perez (cert@test.com) — Jefes a Punto')
        self.assertEqual(str(row), 'Ana Perez — Bienvenida (Pendiente)')

        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin:enrollment_modulecompletion_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ana Perez (cert@test.com) — Jefes a Punto')
        self.assertContains(response, 'Avances de módulo')
        self.assertNotContains(response, 'Enrollment object')

    def test_activar_crea_una_fila_pendiente_por_modulo(self):
        rows = ModuleCompletion.objects.filter(enrollment=self.enrollment)
        self.assertEqual(rows.count(), 2)
        self.assertTrue(all(row.estado == ModuleCompletion.Estado.PENDIENTE for row in rows))

    def test_un_rechazado_no_habilita_certificado(self):
        ModuleCompletion.objects.filter(enrollment=self.enrollment, module=self.module_a).update(
            estado=ModuleCompletion.Estado.APROBADO,
        )
        row_b = ModuleCompletion.objects.get(enrollment=self.enrollment, module=self.module_b)
        row_b.estado = ModuleCompletion.Estado.RECHAZADO
        row_b.save()
        self.enrollment.refresh_from_db()
        self.assertFalse(self.enrollment.all_modules_approved())
        self.assertFalse(Certificate.objects.filter(enrollment=self.enrollment).exists())

    def test_modulo_nuevo_crea_fila_en_matricula_activa(self):
        Module.objects.create(course=self.course, slug='extra', order=3, titulo_es='Extra')
        self.assertEqual(self.enrollment.module_completions.count(), 3)

    def test_listado_muestra_el_boton_solo_con_todos_aprobados(self):
        self.client.login(email='cert@test.com', password='Secreta123!')
        url = reverse('curso:module_list', kwargs={'course_slug': self.course.slug})
        response = self.client.get(url)
        self.assertNotContains(response, 'Descargar certificado')

        ModuleCompletion.objects.filter(enrollment=self.enrollment).update(
            estado=ModuleCompletion.Estado.APROBADO,
        )
        response = self.client.get(url)
        self.assertContains(response, 'Descargar certificado')
        self.assertContains(
            response,
            reverse('curso:certificate_download', kwargs={'course_slug': self.course.slug}),
        )   