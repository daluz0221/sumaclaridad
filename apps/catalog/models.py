from django.db import models

# Create your models here.


class Course(models.Model):
    slug = models.SlugField(unique=True)
    titulo = models.CharField(max_length=255)

    def __str__(self):
        return self.titulo