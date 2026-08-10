from datetime import datetime, timezone as dt_timezone

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Course
from apps.enrollment.models import Enrollment

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
            titulo='Jefes a Punto',
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
        self.course = Course.objects.create(slug='demo', titulo='Demo')
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