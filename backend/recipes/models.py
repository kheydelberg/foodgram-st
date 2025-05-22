from django.db import models
from django.conf import settings
import uuid
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.conf import settings

# CHECKED


class Ingredient(models.Model):
    name = models.CharField(_('name'), max_length=200, db_index=True)
    measurement_unit = models.CharField(_('measurement unit'), max_length=50)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'measurement_unit']  # pay attention
        verbose_name = _('ingredient')
        verbose_name_plural = _('ingredients')

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('author'),
        related_name='recipes'
    )
    name = models.CharField(_('name'), max_length=200)
    image = models.ImageField(_('image'), upload_to='recipes/images/')
    text = models.TextField(_('description'))
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name=_('ingredients'),
        related_name='recipes'
    )
    cooking_time = models.PositiveSmallIntegerField(
        _('cooking time'),
        validators=[MinValueValidator(
            1,
            message=_(
                f'Cooking time should be at least {1} minute'
            )
        )
        ],
    )
    pub_date = models.DateTimeField(
        _('publication date'), auto_now_add=True, db_index=True,)
    short_code = models.SlugField(  # somnitelno no okay
        max_length=10,
        unique=True,
        blank=True,
        editable=False,
        verbose_name=_('Short link code')
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = _('recipe')
        verbose_name_plural = _('recipes')
        """
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'], name='unique_recipe_per_author'
            )
        ]
        """

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):  # somnitelno no okay
        if not self.short_code:
            base_slug = slugify(self.name)[:6] or 'recipe'
            self.short_code = f"{base_slug}-{uuid.uuid4().hex[:4]}".lower()

            while Recipe.objects.filter(short_code=self.short_code).exists():
                self.short_code = f"{base_slug}-{uuid.uuid4().hex[:4]}".lower()

        super().save(*args, **kwargs)

    @property
    def short_url(self):  # somnitelno no okay
        path = reverse('recipe_short_link', kwargs={
                       'short_code': self.short_code})
        return f"{settings.BASE_URL}{path}"

    def get_absolute_url(self):  # somnitelno no okay
        return reverse('recipe_detail', kwargs={'pk': self.id})


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_ingredients',
                               verbose_name=_('recipe'))
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='recipe_ingredients',
                                   verbose_name=_('ingredient'),)
    amount = models.PositiveSmallIntegerField(_('amount'),
                                              validators=[
        MinValueValidator(
            1,
            message=_(
                f'Amount should be at least {1}'
            )
        )
    ],)

    class Meta:
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
        abstract = True
        ordering = ['recipe__name']
        indexes = [
            models.Index(fields=['user', 'recipe'])
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(UserToRecipeLink):
    class Meta(UserToRecipeLink.Meta):
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
    class Meta(UserToRecipeLink.Meta):
        verbose_name = _('shopping cart item')
        verbose_name_plural = _('shopping cart items')
        default_related_name = 'shopping_carts'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='prevent_duplicate_meal_plan',
            )
        ]
