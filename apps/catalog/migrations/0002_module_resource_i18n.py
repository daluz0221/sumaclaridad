from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='course',
            old_name='titulo',
            new_name='titulo_es',
        ),
        migrations.AddField(
            model_name='course',
            name='titulo_en',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='course',
            name='descripcion_es',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='course',
            name='descripcion_en',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='course',
            name='is_published',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterModelOptions(
            name='course',
            options={'ordering': ['titulo_es']},
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(help_text='Único dentro del curso, no a nivel global.')),
                ('order', models.PositiveSmallIntegerField(default=1)),
                ('titulo_es', models.CharField(max_length=255)),
                ('titulo_en', models.CharField(blank=True, max_length=255)),
                ('intro_es', models.TextField(blank=True)),
                ('intro_en', models.TextField(blank=True)),
                ('is_published', models.BooleanField(default=True)),
                ('course', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='modules',
                    to='catalog.course',
                )),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(
                    choices=[('texto', 'Texto'), ('video', 'Vídeo'), ('pdf', 'PDF')],
                    max_length=10,
                )),
                ('order', models.PositiveSmallIntegerField(default=1)),
                ('titulo_es', models.CharField(max_length=255)),
                ('titulo_en', models.CharField(blank=True, max_length=255)),
                ('texto_es', models.TextField(blank=True)),
                ('texto_en', models.TextField(blank=True)),
                ('video_ref', models.CharField(blank=True, max_length=255)),
                ('pdf_ref', models.CharField(blank=True, max_length=255)),
                ('is_published', models.BooleanField(default=True)),
                ('module', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='resources',
                    to='catalog.module',
                )),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='module',
            constraint=models.UniqueConstraint(
                fields=('course', 'slug'),
                name='unique_module_slug_per_course',
            ),
        ),
    ]