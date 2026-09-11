#!/bin/sh
set -e

echo "Esperando PostgreSQL..."
until python -c "
import os, psycopg2
psycopg2.connect(
    dbname=os.environ['POSTGRES_DB'],
    user=os.environ['POSTGRES_USER'],
    password=os.environ['POSTGRES_PASSWORD'],
    host=os.environ['POSTGRES_HOST'],
    port=os.environ.get('POSTGRES_PORT', '5432'),
)
" 2>/dev/null; do
  sleep 1
done

echo "Aplicando migraciones..."
python manage.py migrate --noinput

exec "$@"