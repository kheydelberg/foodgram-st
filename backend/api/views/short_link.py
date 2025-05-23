from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from recipes.models import Recipe


def redirect_short_link(request, slug):
    """Redirect from a short URL slug to the full recipe URL.

    Args:
        request: HttpRequest object
        slug: Short URL identifier for the recipe

    Returns:
        HttpResponseRedirect to the full recipe URL

    Raises:
        Http404: If no recipe exists with the given slug
    """
    recipe = get_object_or_404(Recipe, slug=slug)
    return HttpResponseRedirect(recipe.get_absolute_url())
