#!/usr/bin/env python
import os
import django
import sys
import shutil
from datetime import datetime
from django.core.management import call_command
from django.conf import settings


sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()


from django.contrib.auth import get_user_model
from recipes.models import Recipe, Ingredient, RecipeIngredient


def prepare_database_for_postman():
    """Подготовка базы данных для тестирования через Postman"""
    # 1. Проверка настроек
    print("\n1. Проверка настроек...")
    if not settings.DEBUG:
        print("⚠️ Внимание: DEBUG=False.")

    # 2. Создание резервной копии базы данных
    print("\n2. Создание резервной копии базы данных...")
    db_file = 'db.sqlite3'
    if os.path.exists(db_file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f'db_backup_{timestamp}.sqlite3'
        shutil.copy2(db_file, backup_name)
        print(f"✅ Создана резервная копия: {backup_name}")
    else:
        print("ℹ️ Файл базы данных не найден, будет создан новый")

    # 3. Применение миграций
    print("\n3. Применение миграций...")
    call_command('makemigrations')
    call_command('migrate')
    print("✅ Миграции выполнены")

    # 4. Создание тестовых данных
    print("\n4. Создание тестовых данных...")
    create_test_data()

    # 5. Запуск сервера (информация)
    print("\n5. Подготовка завершена. Для запуска сервера выполните:")
    print("python manage.py runserver\n")


def create_test_data():
    """Создание тестовых данных (сохранена оригинальная структура)"""
    User = get_user_model()

    # Создаем суперпользователя для тестирования
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            first_name='Admin',
            last_name='User'
        )
        print('✅ Суперпользователь admin создан')

    # Создаем стандартных пользователей
    users = [
        {'username': 'chef', 'email': 'chef@example.com',
            'password': 'chefpass', 'first_name': 'Gordon', 'last_name': 'Ramsay'},
        {'username': 'baker', 'email': 'baker@example.com',
            'password': 'bakerpass', 'first_name': 'Julia', 'last_name': 'Child'},
    ]

    for user_data in users:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
            }
        )
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f'✅ Пользователь {user.username} создан')

    # Создаем обязательные ингредиенты (минимум 2)
    ingredients = [
        {'name': 'Мука', 'measurement_unit': 'г'},
        {'name': 'Сахар', 'measurement_unit': 'г'},
    ]

    for ing_data in ingredients:
        ing, created = Ingredient.objects.get_or_create(**ing_data)
        if created:
            print(f'✅ Ингредиент {ing.name} создан')

    # Создаем тестовые рецепты
    recipe_data = {
        'name': 'Тестовый рецепт',
        'description': 'Описание тестового рецепта',
        'cooking_time': 30,
        'ingredients': [
            {'name': 'Мука', 'amount': 200, 'measurement_unit': 'г'},
            {'name': 'Сахар', 'amount': 100, 'measurement_unit': 'г'},
        ]
    }

    user = User.objects.first()
    recipe = Recipe.objects.create(
        author=user,
        name=recipe_data['name'],
        text=recipe_data['description'],
        cooking_time=recipe_data['cooking_time'],
    )

    for ing_data in recipe_data['ingredients']:
        ingredient = Ingredient.objects.get(name=ing_data['name'])
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=ingredient,
            amount=ing_data['amount'],
        )
    print(f'✅ Тестовый рецепт "{recipe.name}" создан')


if __name__ == '__main__':
    prepare_database_for_postman()
