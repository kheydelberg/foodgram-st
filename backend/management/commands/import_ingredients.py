import json
import os
import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Imports ingredients from JSON or CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            help='Path to the ingredients data file (JSON or CSV)'
        )
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            choices=['json', 'csv'],
            help='Format of the input file (default: json)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing ingredients before import'
        )

    def handle(self, *args, **options):
        path = options['path']
        file_format = options['format']
        clear_existing = options['clear']

        # If path is not provided, use default location
        if not path:
            default_filename = f'ingredients.{file_format}'
            # Получаем путь к data на уровне проекта
            project_root = Path(settings.BASE_DIR).parent
            path = os.path.join(project_root, 'data', default_filename)

        try:
            if file_format == 'json':
                self._import_from_json(path, clear_existing)
            elif file_format == 'csv':
                self._import_from_csv(path, clear_existing)
            else:
                raise CommandError(f'Unsupported format: {file_format}')

        except FileNotFoundError:
            raise CommandError(f'File not found: {path}')
        except Exception as e:
            raise CommandError(f'Error importing ingredients: {str(e)}')

    def _import_from_json(self, path, clear_existing):
        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise CommandError(
                    'JSON file should contain an array of ingredients')

            return self._process_ingredients(
                data,
                clear_existing,
                f'Successfully imported {len(data)} ingredients from JSON'
            )

        except json.JSONDecodeError:
            raise CommandError(f'Invalid JSON in file: {path}')

    def _import_from_csv(self, path, clear_existing):
        try:
            with open(path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                data = list(reader)

            if not data:
                raise CommandError('CSV file is empty or has no valid data')

            # Validate CSV structure
            required_fields = ['name', 'measurement_unit']
            for field in required_fields:
                if field not in data[0]:
                    raise CommandError(
                        f'CSV file must contain columns: {", ".join(required_fields)}'
                    )

            return self._process_ingredients(
                data,
                clear_existing,
                f'Successfully imported {len(data)} ingredients from CSV'
            )

        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')

    def _process_ingredients(self, data, clear_existing, success_message):
        existing_count = Ingredient.objects.count()

        if clear_existing and existing_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'Found {existing_count} existing ingredients. Clearing...'
                )
            )
            Ingredient.objects.all().delete()

        ingredients_to_create = []
        for item in data:
            try:
                ingredients_to_create.append(
                    Ingredient(
                        name=item['name'],
                        measurement_unit=item['measurement_unit']
                    )
                )
            except KeyError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Skipping item due to missing field {str(e)}: {item}'
                    )
                )

        if not ingredients_to_create:
            raise CommandError('No valid ingredients found to import')

        Ingredient.objects.bulk_create(ingredients_to_create)

        self.stdout.write(
            self.style.SUCCESS(success_message)
        )
