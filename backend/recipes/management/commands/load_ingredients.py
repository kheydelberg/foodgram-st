import json
from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Imports ingredients from JSON file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            required=True,
            help='Path to the JSON file with ingredients'
        )

    def handle(self, *args, **options):
        path = options['path']

        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise CommandError(
                    'JSON file should contain an array of ingredients')

            # Очищаем существующие ингредиенты
            Ingredient.objects.all().delete()

            # Создаем новые ингредиенты
            ingredients = [
                Ingredient(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                ) for item in data
            ]

            Ingredient.objects.bulk_create(ingredients)
            self.stdout.write(self.style.SUCCESS(
                f'Successfully imported {len(ingredients)} ingredients'
            ))

        except FileNotFoundError:
            raise CommandError(f'File not found: {path}')
        except json.JSONDecodeError:
            raise CommandError(f'Invalid JSON in file: {path}')
        except KeyError as e:
            raise CommandError(f'Missing required field in JSON: {str(e)}')
        except Exception as e:
            raise CommandError(f'Error importing ingredients: {str(e)}')
