from django.core.management.base import BaseCommand

from apps.catalog.models import Course, Module, Resource


MODULES = [
    {
        'slug': 'bienvenida',
        'order': 1,
        'titulo_es': 'Bienvenida e introducción',
        'titulo_en': 'Welcome and introduction',
        'intro_es': 'STUB. Contenido pendiente del cliente. Módulo 1: panorama del curso.',
        'intro_en': 'STUB. Client content pending. Module 1 overview.',
    },
    {
        'slug': 'comunicacion',
        'order': 2,
        'titulo_es': 'Comunicación con el equipo',
        'titulo_en': 'Communicating with the team',
        'intro_es': 'STUB. Contenido pendiente del cliente. Módulo 2: comunicación.',
        'intro_en': 'STUB. Client content pending. Module 2 communication.',
    },
    {
        'slug': 'delegacion',
        'order': 3,
        'titulo_es': 'Delegación efectiva',
        'titulo_en': 'Effective delegation',
        'intro_es': 'STUB. Contenido pendiente del cliente. Módulo 3: delegación.',
        'intro_en': 'STUB. Client content pending. Module 3 delegation.',
    },
    {
        'slug': 'feedback',
        'order': 4,
        'titulo_es': 'Feedback y conversaciones difíciles',
        'titulo_en': 'Feedback and difficult conversations',
        'intro_es': 'STUB. Contenido pendiente del cliente. Módulo 4: feedback.',
        'intro_en': 'STUB. Client content pending. Module 4 feedback.',
    },
    {
        'slug': 'prioridades',
        'order': 5,
        'titulo_es': 'Prioridades y gestión del tiempo',
        'titulo_en': 'Priorities and time management',
        'intro_es': 'STUB. Contenido pendiente del cliente. Módulo 5: prioridades.',
        'intro_en': 'STUB. Client content pending. Module 5 priorities.',
    },
    {
        'slug': 'cierre',
        'order': 6,
        'titulo_es': 'Cierre y plan de acción',
        'titulo_en': 'Closing and action plan',
        'intro_es': 'STUB. Contenido pendiente del cliente. Módulo 6: cierre.',
        'intro_en': 'STUB. Client content pending. Module 6 closing.',
    },
]


class Command(BaseCommand):
    help = 'Crea o actualiza el curso Jefes a Punto con 6 módulos de ejemplo.'

    def handle(self, *args, **options):
        course, created = Course.objects.update_or_create(
            slug='jefes-a-punto',
            defaults={
                'titulo_es': 'Jefes a Punto',
                'titulo_en': 'Leaders Ready',
                'descripcion_es': 'STUB. Curso virtual Jefes a Punto. Contenido real pendiente del cliente.',
                'descripcion_en': 'STUB. Jefes a Punto virtual course. Real content pending.',
                'is_published': True,
            },
        )
        verb = 'Creado' if created else 'Actualizado'
        self.stdout.write(f'{verb} curso {course.slug}')

        for data in MODULES:
            module, _ = Module.objects.update_or_create(
                course=course,
                slug=data['slug'],
                defaults={
                    'order': data['order'],
                    'titulo_es': data['titulo_es'],
                    'titulo_en': data['titulo_en'],
                    'intro_es': data['intro_es'],
                    'intro_en': data['intro_en'],
                    'is_published': True,
                },
            )
            self._seed_resources(module)
            self.stdout.write(f'  Módulo {module.order}: {module.slug}')

        self.stdout.write(self.style.SUCCESS('Seed OK'))

    def _seed_resources(self, module):
        specs = [
            {
                'tipo': Resource.Tipo.VIDEO,
                'order': 1,
                'titulo_es': f'Vídeo principal — {module.titulo_es}',
                'titulo_en': f'Main video — {module.titulo_en}',
                'video_ref': f'pending://{module.slug}-video-1',
            },
            {
                'tipo': Resource.Tipo.TEXTO,
                'order': 2,
                'titulo_es': f'Notas del módulo — {module.titulo_es}',
                'titulo_en': f'Module notes — {module.titulo_en}',
                'texto_es': 'STUB. Texto de apoyo pendiente del cliente.',
                'texto_en': 'STUB. Support text pending.',
            },
            {
                'tipo': Resource.Tipo.PDF,
                'order': 3,
                'titulo_es': f'Guía PDF 1 — {module.titulo_es}',
                'titulo_en': f'PDF guide 1 — {module.titulo_en}',
                'pdf_ref': f'pending://{module.slug}-pdf-1',
            },
            {
                'tipo': Resource.Tipo.PDF,
                'order': 4,
                'titulo_es': f'Guía PDF 2 — {module.titulo_es}',
                'titulo_en': f'PDF guide 2 — {module.titulo_en}',
                'pdf_ref': f'pending://{module.slug}-pdf-2',
            },
        ]
        for spec in specs:
            lookup = {
                'module': module,
                'tipo': spec['tipo'],
                'order': spec['order'],
            }
            defaults = {
                'titulo_es': spec['titulo_es'],
                'titulo_en': spec.get('titulo_en', ''),
                'texto_es': spec.get('texto_es', ''),
                'texto_en': spec.get('texto_en', ''),
                'video_ref': spec.get('video_ref', ''),
                'pdf_ref': spec.get('pdf_ref', ''),
                'is_published': True,
            }
            Resource.objects.update_or_create(**lookup, defaults=defaults)