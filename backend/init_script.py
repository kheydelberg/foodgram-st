#!/usr/bin/env python
import os
import django
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram.settings')
django.setup()


from django.core.management import call_command


def main():
    """Запуск команд инициализации."""
    # Применение миграций
    print('Applying migrations...')
    call_command('migrate')

    # Импорт ингредиентов
    print('Importing ingredients...')
    call_command('import_ingredients', format='json')

    # Создание суперпользователя, если он не существует
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

    print('Initialization complete.')


if __name__ == '__main__':
    main()
