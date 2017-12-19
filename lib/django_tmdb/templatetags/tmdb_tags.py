from django import template
from ..models import Media

register = template.Library()

@register.inclusion_tag('tmdb_tags/_recent_media.html')
def tmdb_recent_media():

    recent_media = Media.objects.recently_rated(max_media=5)
                
    return {'recent_media': recent_media}
