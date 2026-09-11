# Jefes a Punto — Suma Claridad

## Requisitos
- Docker Desktop
- Git

## Arranque local
cp .env.example .env
docker compose up --build

# En otra terminal, crear superusuario:
docker compose exec web python manage.py createsuperuser

## URLs
- App: http://localhost:8000
- Admin: http://localhost:8000/admin
- Registro: http://localhost:8000/accounts/register/
- Curso (requiere matrícula activa): http://localhost:8000/curso/

## Tests
docker compose exec web python manage.py test

