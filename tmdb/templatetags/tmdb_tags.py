from django import template
from ..models import Media

register = template.Library()

@register.inclusion_tag('tmdb_tags/_recent_media.html')
def tmdb_recent_media():
    print 'all media', Media.objects.all()
    print 'filter_type', Media.objects.filter(media_type='movie')
    print 'filter_and_order', Media.objects.filter(media_type='movie').order_by('-added', '-release')
    print 'filter_order_limit', Media.objects.filter(media_type='movie').order_by('-added', '-release')[:5]

    recent_media = Media.objects.recently_rated(max_media=5)
                
    print recent_media
    return {'recent_media': recent_media}
