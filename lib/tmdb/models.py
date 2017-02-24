from django.db import models
from django.conf import settings

import tmdb3
import datetime
from django.utils import timezone

tmdb3.set_key(settings.TMDB_API_KEY)
tmdb3.set_session(settings.TMDB_SESSION_ID)

def get_poster_url(movie):
    min_size = movie.poster.sizes()[0]
    return movie.poster.geturl(min_size)

def get_rated_movies():
    return tmdb3.Movie.ratedmovies()

def get_rated_tv():
    return tmdb3.Series.ratedtv()


class MediaManager(models.Manager):

    def sync_with_tmdb(self, media_type='all'):

        if self.data_is_stale():

            if media_type in ['movie', 'all']:
                self.update_movies_from_tmdb()
            if media_type in ['series', 'all']:
                self.update_tv_from_tmdb()

    def data_is_stale(self):

        yesterday = timezone.now() - datetime.timedelta(hours=24)
        media_db_state, created = MediaDB.objects.get_or_create()
        last_update_time = media_db_state.update_time

        if created:
            return True
        elif last_update_time > yesterday:
            return False
        else:
            return True

    def update_movies_from_tmdb(self):

        for tmdb_movie in get_rated_movies():
            local_movie = Media.movie_from_tmdb(tmdb_movie)
            local_movie.save()

        media_db_state, created = MediaDB.objects.get_or_create()
        media_db_state.save()

    def update_tv_from_tmdb(self):

        for tmdb_series in get_rated_tv():
            local_series = Media.tv_from_tmdb(tmdb_series)
            local_series.save()

        media_db_state, created = MediaDB.objects.get_or_create()
        media_db_state.save()

    def recently_rated(self, media_type='all', max_media=None):
        # Before fetching anything from the database, sync with tmdb
        self.sync_with_tmdb(media_type)

        if media_type == 'all':
            recent_media = self.order_by('-added', '-release')
        else:
            recent_media = self.filter(
                    media_type=media_type).order_by(
                            '-added', '-release')

        if max_media is None:
            return recent_media
        else:
            return recent_media[:max_media]
        

class Media(models.Model):
    MOVIE = 'movie'
    TV = 'series'
    MEDIATYPES = ((MOVIE, MOVIE), (TV, TV))

    tmdb_id = models.PositiveIntegerField(primary_key=True)
    media_type = models.CharField(max_length=6, choices=MEDIATYPES)
    title = models.CharField(max_length=255)
    release = models.DateField()
    poster_url = models.URLField()
    added = models.DateField(auto_now_add=True)

    objects = MediaManager()

    def __repr__(self):
        return '<TMDB {}: {}>'.format(self.media_type.capitalize(), self.title)

    @classmethod
    def movie_from_tmdb(cls, tmdb_movie):

        try:
            movie = cls.objects.get(tmdb_id=tmdb_movie.id)
        except cls.DoesNotExist:
            movie = cls(
                tmdb_id=tmdb_movie.id,
                media_type='movie',
                title=tmdb_movie.title,
                release=tmdb_movie.releasedate,
                poster_url=get_poster_url(tmdb_movie))

        return movie

    @classmethod
    def tv_from_tmdb(cls, tmdb_tv):

        try:
            tv = cls.objects.get(tmdb_id=tmdb_tv.id)
        except cls.DoesNotExist:
            tv = cls(
                tmdb_id=tmdb_tv.id,
                media_type='series',
                title=tmdb_tv.name,
                release=tmdb_tv.first_air_date,
                poster_url=get_poster_url(tmdb_tv))

        return tv

class MediaDB(models.Model):
    update_time = models.DateTimeField(auto_now=True)


