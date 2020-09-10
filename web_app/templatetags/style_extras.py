from django import template
from django.urls import reverse

from recipe_db.models import Style

register = template.Library()


@register.filter(name='url')
def url(style: Style) -> str:
    if style.is_category:
        return reverse('style_category_detail', kwargs={'category_slug': style.slug})
    else:
        return reverse('style_detail', kwargs={'category_slug': style.category.slug, 'slug': style.slug})
