#!/usr/bin/env python
import os
import sys
from pathlib import Path
import django

# Set the correct path to Django project
sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()


from django.contrib.auth import get_user_model
from django.core.management import call_command


def main():
    """Run initialization commands."""
    # Get absolute path to ingredients file
    ingredients_path = str(
        Path(__file__).resolve().parent.parent / 'data' / 'ingredients.json'
    )

    # Apply migrations
    print('🚀 Applying migrations...')
    call_command('migrate')

    # Import ingredients
    print('📦 Loading ingredients...')
    try:
        call_command('load_ingredients', path=ingredients_path)
    except Exception as e:
        print(f'❌ Error loading ingredients: {str(e)}')
        raise

    # Create superuser
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        print('👑 Creating superuser...')
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            first_name='Admin',
            last_name='User'
        )
        print('✅ Superuser created successfully!')
    else:
        print('ℹ️ Superuser already exists.')

    # Load test data if in development mode
    if os.environ.get('DEBUG', 'False') == 'True':
        print('🧪 Preparing test data...')
        call_command('prepare_test_data')

    print('🎉 Initialization complete!')


if __name__ == '__main__':
    main()
