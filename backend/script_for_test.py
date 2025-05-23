#!/usr/bin/env python
import random
import os
import django
import sys
from django.core.files import File
from django.conf import settings

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()


from recipes.models import Recipe, Ingredient, RecipeIngredient
from django.contrib.auth import get_user_model
from django.core.management import call_command


def create_test_data():
    """Создание тестовых данных: пользователей, ингредиентов, рецептов."""
    User = get_user_model()

    # 1. Создаем тестовых пользователей
    users = [
        {'username': 'chef', 'email': 'chef@example.com',
            'password': 'chefpass', 'first_name': 'Gordon', 'last_name': 'Ramsay'},
        {'username': 'baker', 'email': 'baker@example.com',
            'password': 'bakerpass', 'first_name': 'Julia', 'last_name': 'Child'},
        {'username': 'foodie', 'email': 'foodie@example.com',
            'password': 'foodiepass', 'first_name': 'Jamie', 'last_name': 'Oliver'},
    ]

    created_users = []
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
            created_users.append(user)
            print(f'User {user.username} created.')
        else:
            print(f'User {user.username} already exists.')

    # 2. Создаем ингредиенты (если их нет)
    ingredients = [
        {'name': 'Мука', 'measurement_unit': 'г'},
        {'name': 'Сахар', 'measurement_unit': 'г'},
        {'name': 'Яйца', 'measurement_unit': 'шт'},
        {'name': 'Молоко', 'measurement_unit': 'мл'},
        {'name': 'Соль', 'measurement_unit': 'г'},
    ]

    for ing_data in ingredients:
        ing, created = Ingredient.objects.get_or_create(**ing_data)
        if created:
            print(f'Ingredient {ing.name} created.')

    # 3. Создаем рецепты от каждого пользователя
    recipes_data = [
        {
            'name': 'Блинчики',
            'description': 'Классические тонкие блинчики на молоке.',
            'cooking_time': 30,
            'ingredients': [
                {'name': 'Мука', 'amount': 200, 'measurement_unit': 'г'},
                {'name': 'Яйца', 'amount': 2, 'measurement_unit': 'шт'},
                {'name': 'Молоко', 'amount': 500, 'measurement_unit': 'мл'},
            ]
        },
        {
            'name': 'Омлет',
            'description': 'Пышный омлет с зеленью.',
            'cooking_time': 15,
            'ingredients': [
                {'name': 'Яйца', 'amount': 3, 'measurement_unit': 'шт'},
                {'name': 'Молоко', 'amount': 50, 'measurement_unit': 'мл'},
                {'name': 'Соль', 'amount': 5, 'measurement_unit': 'г'},
            ]
        },
    ]

    for user in created_users:
        for recipe_data in recipes_data:
            recipe = Recipe.objects.create(
                author=user,
                name=recipe_data['name'],
                text=recipe_data['description'],
                cooking_time=recipe_data['cooking_time'],
            )

            # Добавляем ингредиенты к рецепту
            for ing_data in recipe_data['ingredients']:
                ingredient = Ingredient.objects.get(name=ing_data['name'])
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ing_data['amount'],
                )

            print(f'Recipe "{recipe.name}" created by {user.username}.')


def main():
    """Основная логика инициализации."""
    print('Applying migrations...')
    call_command('migrate', '--noinput')
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        print('Creating superuser...')
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            first_name='Admin',
            last_name='User'
        )
        print('Superuser created.')
    else:
        print('Superuser already exists.')

    print('Generating test data...')
    create_test_data()

    print('Initialization complete.')


if __name__ == '__main__':
    main()
