
import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from app import create_app
from models import setup_db, Movie, Actor, Token, db
from auth import verify_decode_jwt, check_permissions

# run tests in order of definition
unittest.sortTestMethodsUsing = None

# prompt tester for a required access level to run test
accesses = {
    'assistant': 'get:actors',
    'director': 'post:actors',
    'executive': 'post:movies'
    }

# define unique movie title for test_edit_existing_movie() because of unique contraint on Movie.title field in model
unique_movie = ''

def get_user_access():
    user_access = input(f'Please confirm the access level by typing either {list(accesses)}. ').strip(' ,.').lower()
    while user_access not in accesses:
        user_access = input(f'That is not a valid access level, please type one of the following: {list(accesses)} ').strip(' ,.').lower()
    accesses.update({'user_type': user_access})
    return user_access
    
# prompt tester for a valid JWT for provided access level to run the test
def get_valid_jwt():
    user_access = get_user_access()
    
    test_token = input('Please provide a valid JWT for the choosen access level: ')
    while check_permissions(accesses[user_access], verify_decode_jwt(test_token)) != True:
        test_token = input('Not a valid token, please try again: ')

    # delete all old tokens in db
    Token.query.delete()
    db.session.commit()
    Token(jwt = test_token).add()

    if accesses['user_type'] != 'assistant':
        movies = Movie.query.all()
        movies = [movie.title for movie in movies]
        unique_movie = input('Please provide a unique movie title: ').strip(' ,.').title()
        while unique_movie == '' or unique_movie in movies:
            unique_movie = input('That is not a unique movie title, please try again: ').strip(' ,.').title()

    return f'Bearer {test_token}'

token = get_valid_jwt()

class TestLogin(unittest.TestCase):
    """This class represents the login test case"""

    def setUp(self):
        self.app = create_app(test_config=True)
        self.client = self.app.test_client
        self.database_path = os.environ.get('TEST_DATABASE_URL')
        setup_db(self.app, self.database_path)

        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            self.db.create_all()

        self.headers = {
            'Content-Type': 'application/json', 
            'Authorization': token
            }
    
    def tearDown(self):
        """Executed after each test"""
        pass

    def test_index(self):
        response = self.client().get('/')

        self.assertEqual(response.status_code, 302)

    def test_login(self):
        response = self.client().post(f'/login?jwt={token.split(" ")[1]}')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

class TestActors(unittest.TestCase):
    """This class represents the actors test case"""

    def setUp(self):
        self.app = create_app(test_config=True)
        self.client = self.app.test_client
        self.database_path = os.environ.get('TEST_DATABASE_URL')
        setup_db(self.app, self.database_path)

        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            self.db.create_all()
        
        self.new_actor = {
            'first_name': 'Amy',
            'second_name': 'Adams',
            'gender': 'Female',
            'age': 46
        }

        self.headers = {
            'Content-Type': 'application/json', 
            'Authorization': token
            }
    
    def tearDown(self):
        """Executed after each test"""
        pass

    def test_submit_new_actor(self):
        response = self.client().post('/actors', headers=self.headers, json=self.new_actor)
        data = json.loads(response.data)

        if accesses['user_type'] == 'assistant':
            self.assertEqual(response.status_code, 403)
            self.assertEqual(data['success'], False)
            self.assertFalse(data.get('id'))
            self.assertEqual(data['message']['description'], 'Incorrect claims. Please, check the permissions.')
            self.assertEqual(data['message']['code'], 'forbidden_access')
        else:
            self.assertEqual(response.status_code, 201)
            self.assertEqual(data['success'], True)
            self.assertTrue(data['id'])
            self.assertGreater(data['id'], 0)
            self.assertEqual(data['name'], f'{self.new_actor["first_name"]} {self.new_actor["second_name"]}')
            self.assertEqual(data['gender'], self.new_actor['gender'])
            self.assertEqual(data['age'], self.new_actor['age'])

    def test_422_add_actor_with_missing_values(self):
        new_actor={'first_name': 'John Doe'}
        response = self.client().post('/actors', headers=self.headers, json=new_actor)
        data = json.loads(response.data)
        
        if accesses['user_type'] == 'assistant':
            self.assertEqual(response.status_code, 403)
            self.assertEqual(data['success'], False)
            self.assertFalse(data.get('id'))
            self.assertEqual(data['message']['description'], 'Incorrect claims. Please, check the permissions.')
            self.assertEqual(data['message']['code'], 'forbidden_access')
        else:
            self.assertEqual(response.status_code, 422)
            self.assertFalse(data['success']) 
            self.assertEqual(data['message'], 'unprocessable')

    def test_get_paginated_actors(self):
        response = self.client().get('/actors?page=1', headers=self.headers)
        data = json.loads(response.data)
        actor_count = len(Actor.query.all())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['actors'])
        self.assertLessEqual(len(data['actors']), 5)
        self.assertGreaterEqual(len(data['actors']), 0)
        self.assertTrue(data['total_actors'])
        self.assertEqual(data['total_actors'], actor_count)

    def test_404_no_actors_returned_from_db(self):
        response = self.client().get('/actors?testing=True', headers=self.headers)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'resource not found')

    def test_404_request_actors_beyond_valid_page(self):
        response = self.client().get('/actors?page=100', headers=self.headers)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'resource not found')

    def test_get_actor_by_id(self):
        last_actor_id = Actor.query.order_by(db.desc(Actor.id)).first().id
        response = self.client().get(f'/actors/{last_actor_id}', headers=self.headers)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['actor_details'])
        self.assertGreater(data['actor_details']['id'], 0)
    
    def test_404_actor_not_in_db(self):
        response = self.client().get('/actors/1000', headers=self.headers)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'resource not found')

    def test_edit_existing_actor(self):
        actor = Actor.query.order_by(db.desc(Actor.id)).first()
        actor_id, gender, age = actor.id, actor.gender, actor.age
        new_first_name = 'Wesley'
        new_second_name = 'Snipes'
        response = self.client().patch(
            f'/actors/{actor_id}', headers=self.headers,
            json={
                'first_name': new_first_name, 
                'second_name': new_second_name
            }
        )
        data = json.loads(response.data)

        if accesses['user_type'] == 'assistant':
            self.assertEqual(response.status_code, 403)
            self.assertEqual(data['success'], False)
            self.assertFalse(data.get('id'))
            self.assertEqual(data['message']['description'], 'Incorrect claims. Please, check the permissions.')
            self.assertEqual(data['message']['code'], 'forbidden_access')
        else: 
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['success'], True)
            self.assertEqual(data['id'], actor_id)
            self.assertEqual(data['first name'], new_first_name)
            self.assertEqual(data['second name'], new_second_name)
            self.assertEqual(data['gender'], gender)
            self.assertEqual(data['age'], age)

    def test_422_edit_actor_not_in_db(self):
        response = self.client().patch('/actors/1000', headers=self.headers, \
            json={'first_name': 'foo'})
        data = json.loads(response.data)
        
        if accesses['user_type'] == 'assistant':
            self.assertEqual(response.status_code, 403)
            self.assertEqual(data['success'], False)
            self.assertFalse(data.get('id'))
            self.assertEqual(data['message']['description'], 'Incorrect claims. Please, check the permissions.')
            self.assertEqual(data['message']['code'], 'forbidden_access')
        else:
            self.assertEqual(response.status_code, 422)
            self.assertFalse(data['success']) 
            self.assertEqual(data['message'], 'unprocessable')


    def test_delete_actor(self):
        actor = Actor.query.order_by(db.desc(Actor.id)).first()
        actor_id = actor.id
        response = self.client().delete(f'/actors/{actor_id}', headers=self.headers)
        data = json.loads(response.data)
        
        if accesses['user_type'] == 'assistant':
            self.assertEqual(response.status_code, 403)
            self.assertEqual(data['success'], False)
            self.assertFalse(data.get('id'))
            self.assertEqual(data['message']['description'], 'Incorrect claims. Please, check the permissions.')
            self.assertEqual(data['message']['code'], 'forbidden_access')
        else:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['success'], True)
            self.assertEqual(data['id'], actor_id)
            self.assertTrue(data['name'])
            self.assertEqual(data['gender'], actor.gender)
            self.assertEqual(data['age'], actor.age)

    def test_422_delete_non_existent_actor(self):
        response = self.client().delete('/actors/1000', headers=self.headers)
        data = json.loads(response.data)

        if accesses['user_type'] == 'assistant':
            self.assertEqual(response.status_code, 403)
            self.assertEqual(data['success'], False)
            self.assertFalse(data.get('id'))
            self.assertEqual(data['message']['description'], 'Incorrect claims. Please, check the permissions.')
            self.assertEqual(data['message']['code'], 'forbidden_access')
        else:
            self.assertEqual(response.status_code, 422)
            self.assertFalse(data['success']) 
            self.assertEqual(data['message'], 'unprocessable')

class TestMovies(unittest.TestCase):
    """This class represents the movies test case"""

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client
        self.database_path = os.environ.get('TEST_DATABASE_URL')
        setup_db(self.app, self.database_path)

        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            self.db.create_all()
        
        self.new_movie = {
            'title': 'The Fighter',
            'release_date': '2010-12-06'
        }

        self.headers = {
            'Content-Type': 'application/json', 
            'Authorization': token
        }
    
    def tearDown(self):
        """Executed after each test"""
        pass

    def test_get_paginated_movies(self):
        response = self.client().get('/movies', headers=self.headers)
        data = json.loads(response.data)
        movie_count = len(Movie.query.all())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['movies'])
        self.assertTrue(data['total_movies'])
        self.assertEqual(data['total_movies'], movie_count)

    def test_404_no_movies_returned_from_db(self):
        response = self.client().get('/movies?testing=True', headers=self.headers)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'resource not found')

    def test_404_request_movies_beyond_valid_page(self):
        response = self.client().get('/movies?page=100', headers=self.headers)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'resource not found')

    def test_get_movie_by_id(self):
        response = self.client().get('/movies/1', headers=self.headers)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['movie_details'], True)
        self.assertTrue(len(data['movie_details']), True)
        self.assertGreater(data['movie_details']['id'], 0)
    
    def test_404_movie_not_in_db(self):
        response = self.client().get('/movies/1000', headers=self.headers)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'resource not found')

    def test_submit_new_movie(self):
        last_movie_id = Movie.query.order_by(db.desc(Movie.id)).first().id
        response = self.client().post('/movies', headers=self.headers, json=self.new_movie)
        data = json.loads(response.data)
        user_check = accesses['user_type'] == 'executive'

        self.assertEqual(response.status_code, 201) if user_check \
            else self.assertEqual(response.status_code, 403)
        self.assertEqual(data['success'], True) if user_check \
            else self.assertFalse(data['success'])
        self.assertTrue(data['id']) if user_check \
            else self.assertEqual(data['message']['code'], 'forbidden_access')
        self.assertGreater(data['id'], last_movie_id) if user_check \
            else self.assertEqual(data['message']['description'], 'Incorrect claims. Please, check the permissions.')
        self.assertEqual(data['title'], self.new_movie['title']) if user_check else None
        self.assertEqual(data['release_date'], self.new_movie['release_date']) if user_check else None

    def test_422_add_movie_with_wrong_date_format(self):
        self.new_movie['release_date'] = '06-12-2010'
        response = self.client().post('/movies', headers=self.headers, json=self.new_movie)
        data = json.loads(response.data)
        user_check = accesses['user_type'] == 'executive'
        
        self.assertEqual(response.status_code, 422) if user_check \
            else self.assertEqual(response.status_code, 403)
        self.assertFalse(data['success']) 
        self.assertEqual(data['message'], 'unprocessable') if user_check \
            else self.assertEqual(data['message']['code'], 'forbidden_access')
        if not user_check:
            self.assertEqual(data['message']['description'], 'Incorrect claims. Please, check the permissions.')

    def test_edit_existing_movie(self):
        title = unique_movie
        release = '1977-07-29'
        movie_id = Movie.query.order_by(db.desc(Movie.id)).first().id
        response = self.client().patch(f'/movies/{movie_id}', headers=self.headers,\
             json={'title': title, 'release_date': release})
        data = json.loads(response.data)

        if accesses['user_type'] == 'assistant':
            self.assertEqual(response.status_code, 403)
            self.assertEqual(data['success'], False)
            self.assertFalse(data.get('id'))
            self.assertEqual(data['message']['description'], 'Incorrect claims. Please, check the permissions.')
            self.assertEqual(data['message']['code'], 'forbidden_access')
        else:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['success'], True) 
            self.assertEqual(data['id'], movie_id) 
            self.assertEqual(data['title'], title)
            self.assertEqual(data['release_date'], release) 

    def test_422_edit_movie_not_in_db(self):
        response = self.client().patch('/movies/1000', headers=self.headers, \
            json={'title': 'bar'})
        data = json.loads(response.data)
        user_check = accesses['user_type'] != 'assistant'
        
        self.assertEqual(response.status_code, 422) if user_check \
            else self.assertEqual(response.status_code, 403)
        self.assertFalse(data['success']) 
        self.assertEqual(data['message'], 'unprocessable') if user_check \
            else self.assertEqual(data['message']['code'], 'forbidden_access')
        if user_check == False:
            self.assertEqual(data['message']['description'], 'Incorrect claims. Please, check the permissions.')
    
    def test_delete_movie(self):
        rows_before_delete = Movie.query.order_by(db.desc(Movie.id)).all()
        movie_id = rows_before_delete[0].id
        response = self.client().delete(f'/movies/{movie_id}', headers=self.headers)
        data = json.loads(response.data)
        rows_after_delete = len(Movie.query.all())
        user_check = accesses['user_type'] == 'executive'

        self.assertEqual(response.status_code, 200) if user_check \
            else self.assertEqual(response.status_code, 403) 
        self.assertEqual(data['success'], True) if user_check \
            else self.assertFalse(data['success']) 
        self.assertEqual(data['id'], movie_id) if user_check \
            else self.assertEqual(data['message']['code'], 'forbidden_access')
        self.assertTrue(data['title']) if user_check \
            else self.assertEqual(data['message']['description'], 'Incorrect claims. Please, check the permissions.')
        self.assertTrue(data['release_date']) if user_check else None
        self.assertEqual(len(rows_before_delete), rows_after_delete + 1) if user_check else None

    def test_422_delete_non_existent_movie(self):
        response = self.client().delete('/movies/1000', headers=self.headers)
        data = json.loads(response.data)
        user_check = accesses['user_type'] == 'executive'

        self.assertEqual(response.status_code, 422) if user_check \
            else self.assertEqual(response.status_code, 403)
        self.assertFalse(data['success']) 
        self.assertEqual(data['message'], 'unprocessable') if user_check \
            else self.assertEqual(data['message']['code'], 'forbidden_access')
        if not user_check:
            self.assertEqual(data['message']['description'], 'Incorrect claims. Please, check the permissions.')

if __name__ == "__main__":
    unittest.main()