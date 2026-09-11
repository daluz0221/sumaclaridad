from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase

from apps.catalog.models import Course, Module, Resource


class CatalogModelTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(
            slug='jefes-a-punto',
            titulo_es='Jefes a Punto',
            titulo_en='',
        )

    def test_pick_fallback_a_espanol_si_en_vacio(self):
        self.assertEqual(self.course.localized_titulo('en'), 'Jefes a Punto')
        self.course.titulo_en = 'Leaders Ready'
        self.assertEqual(self.course.localized_titulo('en'), 'Leaders Ready')

    def test_slug_de_modulo_unico_por_curso_no_global(self):
        other = Course.objects.create(slug='otro', titulo_es='Otro')
        Module.objects.create(
            course=self.course, slug='intro', order=1, titulo_es='Intro A',
        )
        Module.objects.create(
            course=other, slug='intro', order=1, titulo_es='Intro B',
        )
        with self.assertRaises(IntegrityError):
            Module.objects.create(
                course=self.course, slug='intro', order=2, titulo_es='Dup',
            )

    def test_resource_tipos(self):
        module = Module.objects.create(
            course=self.course, slug='m1', order=1, titulo_es='M1',
        )
        Resource.objects.create(
            module=module, tipo=Resource.Tipo.PDF, order=1, titulo_es='P1',
        )
        Resource.objects.create(
            module=module, tipo=Resource.Tipo.PDF, order=2, titulo_es='P2',
        )
        self.assertEqual(module.resources.filter(tipo=Resource.Tipo.PDF).count(), 2)


class SeedJefesAPuntoTests(TestCase):
    def test_seed_crea_curso_seis_modulos_y_recursos(self):
        call_command('seed_jefes_a_punto')
        course = Course.objects.get(slug='jefes-a-punto')
        modules = list(course.modules.order_by('order'))
        self.assertEqual(len(modules), 6)
        self.assertTrue(course.is_published)
        first = modules[0]
        self.assertEqual(first.slug, 'bienvenida')
        self.assertEqual(first.resources.filter(tipo=Resource.Tipo.PDF).count(), 2)
        self.assertEqual(first.resources.filter(tipo=Resource.Tipo.VIDEO).count(), 1)

    def test_seed_es_idempotente(self):
        call_command('seed_jefes_a_punto')
        call_command('seed_jefes_a_punto')
        self.assertEqual(Course.objects.filter(slug='jefes-a-punto').count(), 1)
        self.assertEqual(Module.objects.filter(course__slug='jefes-a-punto').count(), 6)