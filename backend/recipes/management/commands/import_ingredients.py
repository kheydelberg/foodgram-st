import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Imports ingredients from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            help='Path to the JSON file with ingredients'
        )
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            choices=['json', 'csv'],
            help='Format of the ingredients file (json or csv)'
        )

    def handle(self, *args, **options):
        path = options['path']
        file_format = options.get('format', 'json')

        if not path:
            path = os.path.join(settings.BASE_DIR, '..',
                                'data', f'ingredients.{file_format}')

        try:
            if file_format == 'json':
                self._import_from_json(path)
            elif file_format == 'csv':
                self._import_from_csv(path)
            else:
                raise CommandError(f'Unsupported format: {file_format}')

        except FileNotFoundError:
            raise CommandError(f'File not found: {path}')
        except Exception as e:
            raise CommandError(f'Error importing ingredients: {str(e)}')

    def _import_from_json(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            existing_count = Ingredient.objects.count()
            if existing_count:
                self.stdout.write(
                    self.style.WARNING(
                        f'Found {existing_count} existing ingredients. Clearing...'
                    )
                )
                Ingredient.objects.all().delete()

            ingredients_to_create = [
                Ingredient(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                ) for item in data
            ]

            Ingredient.objects.bulk_create(ingredients_to_create)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported {len(ingredients_to_create)} ingredients from JSON'
                )
            )
        except json.JSONDecodeError:
            raise CommandError(f'Invalid JSON in file: {path}')

    def _import_from_csv(self, path):
        import csv
        try:
            with open(path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                existing_count = Ingredient.objects.count()
                if existing_count:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Found {existing_count} existing ingredients. Clearing...'
                        )
                    )
                    Ingredient.objects.all().delete()

                ingredients_to_create = []
                for i, row in enumerate(reader, 1):
                    if len(row) >= 2:
                        ingredients_to_create.append(
                            Ingredient(
                                name=row[0],
                                measurement_unit=row[1]
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Row {i} has incomplete data: {row}. Skipping.'
                            )
                        )

                if not ingredients_to_create:
                    self.stdout.write(
                        self.style.ERROR(
                            'No valid ingredients found in CSV file.'
                        )
                    )
                    return

                Ingredient.objects.bulk_create(ingredients_to_create)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully imported {len(ingredients_to_create)} ingredients from CSV'
                    )
                )
        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')
