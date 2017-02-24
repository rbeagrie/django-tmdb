from django.test import TestCase
from django.utils import timezone
from .. import models
import tmdb3
import datetime
import time
from mock import patch
from django.template import Template, Context

class MockTMDBPoster(object):
    def sizes(self):
        return ['100', '200']

    def geturl(self, size):
        return 'http://something.com/{}/img.png'.format(size)

class MockTMDBSeries(object):
    def __init__(self, id, name, first_air_date=None):
        self.id = id
        self.name = name
        if first_air_date is None:
            first_air_date = datetime.date.today()
        self.first_air_date = first_air_date
        self.poster = MockTMDBPoster()

class MockTMDBMovie(object):
    def __init__(self, id, title, releasedate=None):
        self.id = id
        self.title = title
        if releasedate is None:
            releasedate = datetime.date.today()
        self.releasedate = releasedate
        self.poster = MockTMDBPoster()

class MockGetRated(object):

    def __init__(self, media_type, start_id=None):
        self.start_id = start_id
        if media_type == 'movie':
            self.return_class = MockTMDBMovie
        elif media_type == 'series':
            self.return_class = MockTMDBSeries

    def __call__(self):

        if self.start_id is None:
            return
        else:
            for new_id in range(self.start_id, self.start_id+3):
                yield self.return_class(new_id, 'A Movie or TV show')

            self.start_id += 3

def set_last_update_time(new_time):

    media_db_state, created = models.MediaDB.objects.get_or_create()

    if created:
        media_db_state.save()

    models.MediaDB.objects.filter(pk=media_db_state.pk).update(update_time=new_time)


class TmdbMoviesTests(TestCase):

    def test_save_movie(self):
        movie = models.Media.movie_from_tmdb(MockTMDBMovie(100, 'A movie'))
        movie.save()
        self.assertEqual(models.Media.objects.get(), movie)

    def test_no_overwrite(self):

        original_movie = models.Media.movie_from_tmdb(
            MockTMDBMovie(100, 'Original title'))
        original_movie.save()

        new_movie = models.Media.movie_from_tmdb(
            MockTMDBMovie(100, 'New title'))
        new_movie.save()

        saved_movie = models.Media.objects.get()
        self.assertEqual(saved_movie, original_movie)
        self.assertEqual(saved_movie.title, 'Original title')

    @patch.object(models, 'get_rated_movies', MockGetRated('movie'))
    def test_get_latest_added(self):

        one_year_ago = datetime.date.today() - datetime.timedelta(days=365)
        two_year_ago = datetime.date.today() - datetime.timedelta(days=365*2)

        models.Media.movie_from_tmdb(MockTMDBMovie(100, 'A movie')).save()
        models.Media.objects.filter(pk=100).update(added=one_year_ago)

        models.Media.movie_from_tmdb(MockTMDBMovie(101, 'Another movie', two_year_ago)).save()
        models.Media.objects.filter(pk=101).update(added=one_year_ago)

        models.Media.movie_from_tmdb(MockTMDBMovie(102, 'A movie 3: movie harder', one_year_ago)).save()
        models.Media.objects.filter(pk=102).update(added=one_year_ago)

        models.Media.movie_from_tmdb(MockTMDBMovie(200, 'This movie')).save()
        models.Media.movie_from_tmdb(MockTMDBMovie(201, 'That movie', two_year_ago)).save()
        models.Media.movie_from_tmdb(MockTMDBMovie(202, 'Which movie?', one_year_ago)).save()

        added_recent = models.Media.objects.recently_rated('movie', 3)

        self.assertEqual([m.tmdb_id for m in added_recent], [200, 202, 201])

        added_recent_plus_1 = models.Media.objects.recently_rated('movie', 4)

        self.assertEqual([m.tmdb_id for m in added_recent_plus_1], [200, 202, 201, 100])

    @patch.object(models, 'get_rated_movies', MockGetRated('movie', 101))
    def test_database_update(self):

        models.Media.objects.update_movies_from_tmdb()
        all_movies = models.Media.objects.all()
        self.assertEqual([m.tmdb_id for m in all_movies], [101, 102, 103])

        models.Media.objects.update_movies_from_tmdb()
        all_movies = models.Media.objects.all()
        self.assertEqual([m.tmdb_id for m in all_movies], [101, 102, 103, 104, 105, 106])

    @patch.object(models, 'get_rated_movies', MockGetRated('movie', 101))
    def test_cached_update(self):

        all_movies = models.Media.objects.recently_rated('movie')
        self.assertEqual([m.tmdb_id for m in all_movies], [101, 102, 103])

        all_movies = models.Media.objects.recently_rated('movie')
        self.assertEqual([m.tmdb_id for m in all_movies], [101, 102, 103])

    @patch.object(models, 'get_rated_movies', MockGetRated('movie', 101))
    def test_update_23h_ago(self):

        now_minus_23h = timezone.now() - datetime.timedelta(hours=23)

        all_movies = models.Media.objects.recently_rated('movie')
        self.assertEqual([m.tmdb_id for m in all_movies], [101, 102, 103])

        set_last_update_time(now_minus_23h)

        all_movies = models.Media.objects.recently_rated('movie')
        self.assertEqual([m.tmdb_id for m in all_movies], [101, 102, 103])

    @patch.object(models, 'get_rated_movies', MockGetRated('movie', 101))
    def test_update_25h_ago(self):

        now_minus_25h = timezone.now() - datetime.timedelta(hours=25)

        all_movies = models.Media.objects.recently_rated('movie')
        self.assertEqual([m.tmdb_id for m in all_movies], [101, 102, 103])

        set_last_update_time(now_minus_25h)

        all_movies = models.Media.objects.recently_rated('movie')
        self.assertEqual([m.tmdb_id for m in all_movies], [101, 102, 103, 104, 105, 106])


class TmdbTVTests(TestCase):

    def test_save_tv(self):
        tv = models.Media.tv_from_tmdb(MockTMDBSeries(100, 'A tv show'))
        tv.save()
        self.assertEqual(models.Media.objects.get(), tv)

    def test_no_overwrite(self):

        original_tv = models.Media.tv_from_tmdb(
            MockTMDBSeries(100, 'Original title'))
        original_tv.save()

        new_tv = models.Media.tv_from_tmdb(
            MockTMDBSeries(100, 'New title'))
        new_tv.save()

        saved_tv = models.Media.objects.get()
        self.assertEqual(saved_tv, original_tv)
        self.assertEqual(saved_tv.title, 'Original title')

    @patch.object(models, 'get_rated_tv', MockGetRated('series'))
    def test_get_latest_added(self):

        one_year_ago = datetime.date.today() - datetime.timedelta(days=365)
        two_year_ago = datetime.date.today() - datetime.timedelta(days=365*2)

        models.Media.tv_from_tmdb(MockTMDBSeries(100, 'A tv show')).save()
        models.Media.objects.filter(pk=100).update(added=one_year_ago)

        models.Media.tv_from_tmdb(MockTMDBSeries(101, 'Another show', two_year_ago)).save()
        models.Media.objects.filter(pk=101).update(added=one_year_ago)

        models.Media.tv_from_tmdb(MockTMDBSeries(102, 'Sesame Street', one_year_ago)).save()
        models.Media.objects.filter(pk=102).update(added=one_year_ago)

        models.Media.tv_from_tmdb(MockTMDBSeries(200, 'This show')).save()
        models.Media.tv_from_tmdb(MockTMDBSeries(201, 'That show', two_year_ago)).save()
        models.Media.tv_from_tmdb(MockTMDBSeries(202, 'Which show?', one_year_ago)).save()

        added_recent = models.Media.objects.recently_rated('series', 3)

        self.assertEqual([m.tmdb_id for m in added_recent], [200, 202, 201])

        added_recent_plus_1 = models.Media.objects.recently_rated('series', 4)

        self.assertEqual([m.tmdb_id for m in added_recent_plus_1], [200, 202, 201, 100])

    @patch.object(models, 'get_rated_tv', MockGetRated('series', 101))
    def test_database_update(self):

        models.Media.objects.update_tv_from_tmdb()
        all_tv = models.Media.objects.all()
        self.assertEqual([m.tmdb_id for m in all_tv], [101, 102, 103])

        models.Media.objects.update_tv_from_tmdb()
        all_tv = models.Media.objects.all()
        self.assertEqual([m.tmdb_id for m in all_tv], [101, 102, 103, 104, 105, 106])

    @patch.object(models, 'get_rated_tv', MockGetRated('series', 101))
    def test_cached_update(self):

        all_tv = models.Media.objects.recently_rated('series')
        self.assertEqual([m.tmdb_id for m in all_tv], [101, 102, 103])

        all_tv = models.Media.objects.recently_rated('series')
        self.assertEqual([m.tmdb_id for m in all_tv], [101, 102, 103])

    @patch.object(models, 'get_rated_tv', MockGetRated('series', 101))
    def test_update_23h_ago(self):

        now_minus_23h = timezone.now() - datetime.timedelta(hours=23)
        
        all_tv = models.Media.objects.recently_rated('series')
        self.assertEqual([m.tmdb_id for m in all_tv], [101, 102, 103])

        set_last_update_time(now_minus_23h)

        all_tv = models.Media.objects.recently_rated('series')
        self.assertEqual([m.tmdb_id for m in all_tv], [101, 102, 103])

    @patch.object(models, 'get_rated_tv', MockGetRated('series', 101))
    def test_update_25h_ago(self):

        now_minus_25h = timezone.now() - datetime.timedelta(hours=25)

        all_tv = models.Media.objects.recently_rated('series')
        self.assertEqual([m.tmdb_id for m in all_tv], [101, 102, 103])

        set_last_update_time(now_minus_25h)

        all_tv = models.Media.objects.recently_rated('series')
        self.assertEqual([m.tmdb_id for m in all_tv], [101, 102, 103, 104, 105, 106])

class TmdbMixedMediaTests(TestCase):

    @patch.object(models, 'get_rated_tv', MockGetRated('series', 101))
    @patch.object(models, 'get_rated_movies', MockGetRated('movie', 201))
    def test_get_recent_tv(self):
        models.Media.objects.update_tv_from_tmdb()
        models.Media.objects.update_movies_from_tmdb()

        all_tv = models.Media.objects.recently_rated('series')

        self.assertEqual([m.tmdb_id for m in all_tv], [101, 102, 103])
        self.assertTrue(all([m.media_type == 'series' for m in all_tv]))

    @patch.object(models, 'get_rated_tv', MockGetRated('series', 101))
    @patch.object(models, 'get_rated_movies', MockGetRated('movie', 201))
    def test_get_recent_movies(self):
        models.Media.objects.update_tv_from_tmdb()
        models.Media.objects.update_movies_from_tmdb()

        all_movies = models.Media.objects.recently_rated('movie')

        self.assertEqual([m.tmdb_id for m in all_movies], [201, 202, 203])
        self.assertTrue(all([m.media_type == 'movie' for m in all_movies]))

    @patch.object(models, 'get_rated_tv', MockGetRated('series', 101))
    @patch.object(models, 'get_rated_movies', MockGetRated('movie', 201))
    def test_get_recent_media(self):
        models.Media.objects.update_tv_from_tmdb()
        models.Media.objects.update_movies_from_tmdb()

        all_media = models.Media.objects.recently_rated()

        self.assertEqual([m.tmdb_id for m in all_media], [101, 102, 103, 201, 202, 203])
        self.assertTrue('series' in [m.media_type for m in all_media])
        self.assertTrue('movie' in [m.media_type for m in all_media])

    @patch.object(models, 'get_rated_tv', MockGetRated('series', 101))
    @patch.object(models, 'get_rated_movies', MockGetRated('movie', 201))
    def test_get_tv_no_update_movies(self):
        all_tv = models.Media.objects.recently_rated('series')

        self.assertEqual([m.tmdb_id for m in all_tv], [101, 102, 103])
        self.assertFalse(models.Media.objects.filter(media_type='movie').exists())

    @patch.object(models, 'get_rated_tv', MockGetRated('series', 101))
    @patch.object(models, 'get_rated_movies', MockGetRated('movie', 201))
    def test_get_movies_no_update_tv(self):
        all_movies = models.Media.objects.recently_rated('movie')

        self.assertEqual([m.tmdb_id for m in all_movies], [201, 202, 203])
        self.assertFalse(models.Media.objects.filter(media_type='series').exists())

    @patch.object(models, 'get_rated_tv', MockGetRated('series', 101))
    @patch.object(models, 'get_rated_movies', MockGetRated('movie', 201))
    def test_get_all_update_all(self):
        all_media = models.Media.objects.recently_rated()

        self.assertEqual([m.tmdb_id for m in all_media], [201, 202, 203, 101, 102, 103])
        self.assertTrue('series' in [m.media_type for m in all_media])
        self.assertTrue('movie' in [m.media_type for m in all_media])

class TMDBTemplateTagTest(TestCase):

    TEMPLATE = Template(
    "{% load tmdb_tags %}{% tmdb_recent_media %}")

    @patch.object(models, 'get_rated_tv', MockGetRated('series'))
    @patch.object(models, 'get_rated_movies', MockGetRated('movie'))
    def test_movie_shows_up(self):

        movie = models.Media.objects.create(
                tmdb_id=101, title='101 Dalmations',
                media_type='movie', release=datetime.date.today())
        movie.save()

        rendered = self.TEMPLATE.render(Context({}))
        self.assertIn(movie.title, rendered)
