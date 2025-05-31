from django.db import models
from django.conf import settings
import uuid
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from api.consts import (
    MIN_COOKING_TIME,
    MAX_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT,
    MAX_INGREDIENT_AMOUNT
)


class Ingredient(models.Model):
    """Model representing an ingredient with measurement unit."""

    name = models.CharField(
        _('name'), max_length=200, db_index=True
    )
    measurement_unit = models.CharField(
        _('measurement unit'), max_length=50
    )

    class Meta:
        """Meta options for Ingredient model."""

        ordering = ['name']
        unique_together = ['name', 'measurement_unit']
        verbose_name = _('ingredient')
        verbose_name_plural = _('ingredients')

    def __str__(self):
        """String representation of the ingredient."""
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Model representing a cooking recipe."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('author'),
        related_name='recipes'
    )
    name = models.CharField(_('name'), max_length=200)
    image = models.ImageField(
        _('image'), upload_to='recipes/images/'
    )
    text = models.TextField(_('description'))
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name=_('ingredients'),
        related_name='recipes'
    )
    cooking_time = models.PositiveSmallIntegerField(
        _('cooking time'),
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=_(
                    'Cooking time should be at least %(limit_value)s minute'
                ) % {'limit_value': MIN_COOKING_TIME}
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message=_(
                    'Cooking time should not exceed %(limit_value)s minutes'
                ) % {'limit_value': MAX_COOKING_TIME}
            )
        ],
    )
    pub_date = models.DateTimeField(
        _('publication date'),
        auto_now_add=True,
        db_index=True,
    )
    short_code = models.SlugField(
        max_length=15,
        unique=True,
        blank=True,
        editable=False,
        verbose_name=_('Short link code')
    )

    class Meta:
        """Meta options for Recipe model."""

        ordering = ['-pub_date']
        verbose_name = _('recipe')
        verbose_name_plural = _('recipes')

    def __str__(self):
        """String representation of the recipe."""
        return self.name

    def save(self, *args, **kwargs):
        """Generate short code for the recipe before saving."""
        if not self.short_code:
            base_slug = slugify(self.name)[:6] or 'recipe'
            self.short_code = f"{base_slug}-{uuid.uuid4().hex[:4]}".lower()

            while Recipe.objects.filter(
                short_code=self.short_code
            ).exists():
                self.short_code = (
                    f"{base_slug}-{uuid.uuid4().hex[:4]}".lower()
                )

        super().save(*args, **kwargs)

    @property
    def short_url(self):
        """Generate short URL for the recipe."""
        path = reverse(
            'recipe_short_link',
            kwargs={'short_code': self.short_code}
        )
        return f"{settings.BASE_URL}{path}"

    def get_absolute_url(self):
        """Get absolute URL for the recipe detail page."""
        return reverse('recipe_detail', kwargs={'pk': self.id})


class RecipeIngredient(models.Model):
    """Intermediate model for Recipe-Ingredient relationship."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name=_('recipe')
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name=_('ingredient'),
    )
    amount = models.PositiveSmallIntegerField(
        _('amount'),
        validators=[
            MinValueValidator(
                MIN_INGREDIENT_AMOUNT,
                message=_(
                    'Amount should be at least %(limit_value)s'
                ) % {'limit_value': MIN_INGREDIENT_AMOUNT}
            ),
            MaxValueValidator(
                MAX_INGREDIENT_AMOUNT,
                message=_(
                    'Amount should not exceed %(limit_value)s'
                ) % {'limit_value': MAX_INGREDIENT_AMOUNT}
            )
        ],
    )

    class Meta:
        """Meta options for RecipeIngredient model."""

        ordering = ['recipe', 'ingredient']
        verbose_name = _('recipe ingredient')
        verbose_name_plural = _('recipe ingredients')
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_per_recipe'
            )
        ]


class UserToRecipeLink(models.Model):
    """Abstract base model for user-recipe relationships."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('user'),
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name=_('recipe'),
    )

    class Meta:
        """Meta options for UserToRecipeLink model."""

        abstract = True
        ordering = ['recipe__name']
        indexes = [
            models.Index(fields=['user', 'recipe'])
        ]

    def __str__(self):
        """String representation of the user-recipe relationship."""
        return f'{self.user} - {self.recipe}'


class Favorite(UserToRecipeLink):
    """Model representing user's favorite recipes."""

    class Meta(UserToRecipeLink.Meta):
        """Meta options for Favorite model."""

        verbose_name = _('favorite')
        verbose_name_plural = _('favorites')
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='prevent_duplicate_saves'
            )
        ]


class ShoppingCart(UserToRecipeLink):
    """Model representing user's shopping cart items."""

    class Meta(UserToRecipeLink.Meta):
        """Meta options for ShoppingCart model."""

        verbose_name = _('shopping cart item')
        verbose_name_plural = _('shopping cart items')
        default_related_name = 'shopping_carts'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='prevent_duplicate_meal_plan',
            )
        ]
