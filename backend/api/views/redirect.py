from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from recipes.models import Recipe


def resolve_short_link(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug)
    return HttpResponseRedirect(recipe.get_absolute_url())
