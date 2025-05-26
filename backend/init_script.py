#!/usr/bin/env python
import os
import sys
from pathlib import Path
import django

# Указываем правильный путь к Django проекту
sys.path.append(str(Path(__file__).resolve().parent))  # Добавляем папку backend в PYTHONPATH
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.core.management import call_command

def main():
    """Запуск команд инициализации."""
    # Определяем абсолютный путь к файлу ингредиентов
    ingredients_path = str(Path(__file__).resolve().parent.parent / 'data' / 'ingredients.json')
    
    # Применение миграций
    print('Applying migrations...')
    call_command('migrate')

    # Импорт ингредиентов
    print('Importing ingredients...')
    try:
        call_command('import_ingredients', path=ingredients_path, format='json')
    except Exception as e:
        print(f'Error importing ingredients: {str(e)}')
        raise

    # Создание суперпользователя
    from django.contrib.auth import get_user_model
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