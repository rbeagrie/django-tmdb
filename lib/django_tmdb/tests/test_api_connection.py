from django.test import TestCase
from .. import models
import tmdb3
import datetime


class LiveConnectionTests(TestCase):

    def test_can_get_movies(self):
        movie_list = list(models.get_rated_movies())
        self.assertTrue(len(movie_list), '')
        self.assertIsInstance(movie_list[0], tmdb3.Movie)

    def test_movie_from_tmdb_api(self):
        tmdb_movie = tmdb3.Movie.fromIMDB('tt0087363')
        movie = models.Media.movie_from_tmdb(tmdb_movie)
        self.assertEqual(movie.media_type, 'movie')
        self.assertEqual(movie.title, 'Gremlins')
        self.assertEqual(movie.tmdb_id, 927)
        self.assertIsInstance(movie.release, datetime.date)
        self.assertEqual(movie.poster_url[:7], 'http://')

    def test_can_get_tv(self):
        tv_list = list(models.get_rated_tv())
        self.assertTrue(len(tv_list), '')
        self.assertIsInstance(tv_list[0], tmdb3.Series)

    def test_tv_from_tmdb_api(self):
        tmdb_tv = tmdb3.Series(2153)
        tv = models.Media.tv_from_tmdb(tmdb_tv)
        self.assertEqual(tv.title, 'Arthur')
        self.assertEqual(tv.media_type, 'series')
        self.assertEqual(tv.tmdb_id, 2153)
        self.assertIsInstance(tv.release, datetime.date)
        self.assertEqual(tv.poster_url[:7], 'http://')

