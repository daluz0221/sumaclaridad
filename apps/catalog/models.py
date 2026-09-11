from django.db import models


class TranslatableMixin:
    """Elige campo *_es / *_en con fallback a español."""

    def pick(self, field_base, lang='es'):
        lang = lang if lang in ('es', 'en') else 'es'
        value = getattr(self, f'{field_base}_{lang}', None) or ''
        if not value and lang != 'es':
            value = getattr(self, f'{field_base}_es', None) or ''
        return value


class Course(TranslatableMixin, models.Model):
    slug = models.SlugField(
        unique=True,
        help_text='Identificador en la URL. No cambia con el idioma.',
    )
    titulo_es = models.CharField(max_length=255)
    titulo_en = models.CharField(max_length=255, blank=True)
    descripcion_es = models.TextField(blank=True)
    descripcion_en = models.TextField(blank=True)
    is_published = models.BooleanField(
        default=True,
        help_text='Si está desmarcado, el alumno no lo ve en /curso/.',
    )

    class Meta:
        ordering = ['titulo_es']

    def __str__(self):
        return self.titulo_es

    def localized_titulo(self, lang='es'):
        return self.pick('titulo', lang)

    def localized_descripcion(self, lang='es'):
        return self.pick('descripcion', lang)


class Module(TranslatableMixin, models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
    )
    slug = models.SlugField(
        help_text='Único dentro del curso, no a nivel global.',
    )
    order = models.PositiveSmallIntegerField(
        default=1,
        help_text='Solo define el orden de visualización. No bloquea módulos.',
    )
    titulo_es = models.CharField(max_length=255)
    titulo_en = models.CharField(max_length=255, blank=True)
    intro_es = models.TextField(blank=True)
    intro_en = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['course', 'slug'],
                name='unique_module_slug_per_course',
            ),
        ]

    def __str__(self):
        return f'{self.course.slug} / {self.titulo_es}'

    def localized_titulo(self, lang='es'):
        return self.pick('titulo', lang)

    def localized_intro(self, lang='es'):
        return self.pick('intro', lang)


class Resource(TranslatableMixin, models.Model):
    class Tipo(models.TextChoices):
        TEXTO = 'texto', 'Texto'
        VIDEO = 'video', 'Vídeo'
        PDF = 'pdf', 'PDF'

    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='resources',
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    order = models.PositiveSmallIntegerField(default=1)
    titulo_es = models.CharField(max_length=255)
    titulo_en = models.CharField(max_length=255, blank=True)
    texto_es = models.TextField(blank=True)
    texto_en = models.TextField(blank=True)
    video_ref = models.CharField(
        max_length=255,
        blank=True,
        help_text='Placeholder Semana 2. En Semana 3 será el id/token de Bunny.',
    )
    pdf_ref = models.CharField(
        max_length=255,
        blank=True,
        help_text='Placeholder Semana 2. En Semana 3 será la key de S3.',
    )
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.get_tipo_display()}: {self.titulo_es}'

    def localized_titulo(self, lang='es'):
        return self.pick('titulo', lang)

    def localized_texto(self, lang='es'):
        return self.pick('texto', lang)