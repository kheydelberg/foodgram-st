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
            required=True,  # Теперь путь обязательный
            help='Absolute path to the ingredients data file'
        )

    def handle(self, *args, **options):
        path = options['path']

        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            ingredients = [
                Ingredient(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                ) for item in data
            ]

            Ingredient.objects.bulk_create(ingredients)
            self.stdout.write(self.style.SUCCESS(
                f'Successfully imported {len(ingredients)} ingredients'))

        except Exception as e:
            raise CommandError(f'Error importing ingredients: {str(e)}')
