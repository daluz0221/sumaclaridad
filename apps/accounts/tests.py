from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_with_email_login(self):
        user = User.objects.create_user(
            email='alumno@test.com',
            password='Secreta123!',
            name='Ana Pérez',
            phone='3001234567',
            position='Gerente',
        )
        self.assertEqual(user.email, 'alumno@test.com')
        self.assertEqual(user.USERNAME_FIELD, 'email')
        self.assertTrue(user.check_password('Secreta123!'))
        self.assertEqual(user.role, User.Role.VISITANT)
        self.assertFalse(user.is_staff)

    def test_create_superuser_flags(self):
        admin = User.objects.create_superuser(
            email='admin@test.com',
            password='Secreta123!',
            name='Admin Uno',
            phone='3000000001',
            position='Admin',
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, User.Role.ADMIN)

    def test_register_requires_consent(self):
        client = Client()
        url = reverse('accounts:register')
        payload = {
            'email': 'nuevo@test.com',
            'name': 'Nuevo',
            'phone': '3001112233',
            'position': 'Analista',
            'company': '',
            'profession': '',
            'prefer_language': 'es',
            'password1': 'Secreta123!',
            'password2': 'Secreta123!',
            # sin accepted_consent
        }
        response = client.post(url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='nuevo@test.com').exists())

    def test_register_with_consent_creates_user_and_logs_in(self):
        client = Client()
        url = reverse('accounts:register')
        payload = {
            'email': 'ok@test.com',
            'name': 'Ok User',
            'phone': '3001112233',
            'position': 'Analista',
            'company': 'ACME',
            'profession': '',
            'prefer_language': 'es',
            'password1': 'Secreta123!',
            'password2': 'Secreta123!',
            'accepted_consent': True,
        }
        response = client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email='ok@test.com')
        self.assertTrue(user.accepted_consent)
        self.assertIsNotNone(user.consent_date)
        self.assertEqual(user.role, User.Role.VISITANT)

    def test_login_with_email(self):
        User.objects.create_user(
            email='login@test.com',
            password='Secreta123!',
            name='Login',
            phone='3009998877',
            position='Cargo',
        )
        client = Client()
        logged = client.login(email='login@test.com', password='Secreta123!')
        self.assertTrue(logged)