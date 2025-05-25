#!/usr/bin/env python
import os
import sys
from pathlib import Path
import django
import requests
from django.contrib.auth import get_user_model


# Определяем корень проекта (на уровень выше от backend)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()


from django.core.management import call_command


def main():
    """Запуск команд инициализации."""
    # Определяем абсолютный путь к файлу ингредиентов
    ingredients_file = PROJECT_ROOT / "data" / "ingredients.json"

    # Применение миграций
    print('Applying migrations...')
    call_command('migrate')

    # Скачивание и импорт ингредиентов
    if not ingredients_file.exists():
        print('Importing ingredients...')
        call_command('import_ingredients', path=str(
            ingredients_file), format='json')
    else:
        print('Using existing ingredients file...')
        call_command('import_ingredients', path=str(
            ingredients_file), format='json')

    # Создание суперпользователя
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        print('Creating superuser...')
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            first_name='Admin',
            last_name='User'
        )
        print('Superuser created.')
    else:
        print('Superuser already exists.')


if __name__ == '__main__':
    main()
