# Generated by Django 5.2.1 on 2025-05-31 19:07

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_alter_recipe_short_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, message='Cooking time should be at least 1 minute'), django.core.validators.MaxValueValidator(32000, message='Cooking time should not exceed 32000 minutes')], verbose_name='cooking time'),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, message='Amount should be at least 1'), django.core.validators.MaxValueValidator(32000, message='Amount should not exceed 32000')], verbose_name='amount'),
        ),
    ]
