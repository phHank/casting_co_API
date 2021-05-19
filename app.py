import os
import datetime
from flask import Flask, request, abort, jsonify, redirect, render_template
from flask_cors import CORS

from models import setup_db, Project, Movie, Actor, Token, db
from auth import requires_auth, AUTH0_DOMAIN, API_AUDIENCE, AuthError

def create_app(test_config=None):
  app = Flask(__name__)
  setup_db(app)
  CORS(app)

####################### LOGIN ################################
  @app.route('/')
  def index():
    client_id = os.environ['CLIENT_ID']
    login_url = os.environ['LOGIN_URI']
    boiler_plate = f'authorize?audience={API_AUDIENCE}&response_type=token&client_id='
    return redirect(f'https://{AUTH0_DOMAIN}/{boiler_plate}{client_id}&redirect_uri={login_url}', code=302)

  @app.route('/login')
  def login():
    return render_template('login.html')

  @app.route('/login', methods=['GET', 'POST'])
  def get_jwt():
    try:
      # delete all old tokens in db
      Token.query.delete()
      db.session.commit()

      # insert latest token
      jwt = request.args.get('jwt')
      Token(jwt = jwt).add()
    except:
      abort(422)

    return jsonify({
      'success': True,
      }), 200

  @app.route('/jwt')
  @requires_auth('get:actors')
  def show_jwt(jwt):
    try: 
      token = Token.query.first().jwt
    except:
      abort(403)

    return jsonify({
      'token': token,
      'success': True 
    }), 200

  @app.route('/logged-in')
  @requires_auth('get:actors')
  def after_login(jwt):
    try:      
      web_template = render_template('logged-in.html')
    except:
      abort(403)

    return web_template

####################### ENDPOINTS ###########################
#######################  ACTORS   ###########################

  @app.route('/actors')
  @requires_auth('get:actors')
  def all_actors(jwt):
    try:
      testing = request.args.get('testing', False, type=bool)
      if testing == True:
        abort(404)
      
      # pagination
      page = request.args.get('page', 1, type=int)
      start = (page - 1) * 5
      end = start + 5
      
      actors = Actor.query.all()
      total_actors = len(actors)
      if total_actors + 5 < page * 5:
        abort(404)
      actors = [actor.short_format() for actor in actors]
    except:
      abort(404)
    finally:
      db.session.close()

    return jsonify({
      'actors': actors[start:end],
      'total_actors': total_actors,
      'success': True
      }), 200


  @app.route('/actors/<int:id>')
  @requires_auth('get:actors')
  def detailed_actor(jwt, id):
    try:
      actor = Actor.query.get(id)
      actor = actor.format()
      movies = db.session.query(Actor.surname, Movie.id, Movie.title)\
        .join(Project, Actor.id == Project.actor_id)\
          .join(Movie, Project.movie_id == Movie.id)\
            .filter(Project.actor_id == id).all()
      movies = [{'movie_title':movie.title, 'movie_id': movie.id} for movie in movies]
    except:
      abort(404)
    finally: 
      db.session.close()

    return jsonify({
      'success': True,
      'actor_details': actor, 
      'movies': movies,
      'movie_count': len(movies)
    }), 200

  @app.route('/actors', methods=('GET', 'POST'))
  @requires_auth('post:actors')
  def add_actor(jwt):
    try:
      first_name = request.get_json()['first_name'].title()
      second_name = request.get_json()['second_name'].title()
      gender = request.get_json()['gender'].title()
      age = request.get_json()['age']
      new_actor = Actor(firstname=first_name, surname=second_name, gender=gender, age=age)
      new_actor.add()
    except:
      abort(422)

    return jsonify({
      'success': True,
      'id': new_actor.id,
      'name': f'{new_actor.firstname} {new_actor.surname}',
      'gender': new_actor.gender,
      'age': new_actor.age
    }), 201

  @app.route('/actors/<int:id>', methods=('GET', 'PATCH'))
  @requires_auth('patch:actors')
  def edit_actor(jwt, id):
    try:
      actor = Actor.query.get(id)
      keys = list(request.get_json().keys())
    
      actor.firstname = request.get_json()['first_name'].title() \
        if 'first_name' in keys else actor.firstname
      actor.surname = request.get_json()['second_name'].title() \
        if 'second_name' in keys else actor.surname
      actor.gender = request.get_json()['gender'].title() \
        if 'gender' in keys else actor.gender
      actor.age = request.get_json()['age'] \
        if 'age' in keys else actor.age  

      actor.edit()
    except:
      abort(422)

    return jsonify({
      'id': actor.id,
      'first name': actor.firstname,
      'second name': actor.surname,
      'gender': actor.gender,
      'age': actor.age,
      'success': True,
    }), 200

  @app.route('/actors/<int:id>', methods=('GET', 'DELETE'))
  @requires_auth('delete:actors')
  def delete_actor(jwt, id):
    try:
      delete_actor = Actor.query.get(id)
      delete_actor.delete()
    except:
      abort(422)

    return jsonify({
      'success': True,
      'id': delete_actor.id,
      'name': f'{delete_actor.firstname} {delete_actor.surname}',
      'gender': delete_actor.gender,
      'age': delete_actor.age
    }), 200


 ######################## MOVIES ##############################

  @app.route('/movies')
  @requires_auth('get:movies')
  def all_moviess(jwt):
    try:
      test = request.args.get('testing', False, type=bool)
      if test == True:
        abort(404)

      page = request.args.get('page', 1, type=int)
      start = (page - 1) * 5
      end = start + 5
      
      movies = Movie.query.all()
      total_movies = len(movies)
      if total_movies + 5 <= page * 5:
        abort(404)
      movies = [movie.format() for movie in movies]
    except:
      abort(404)
    finally:
      db.session.close()

    return jsonify({
      'movies': movies[start:end],
      'total_movies': len(movies),
      'success': True
      }), 200


  @app.route('/movies/<int:id>')
  @requires_auth('get:movies')
  def detailed_movie(jwt, id):
    try:
      movie = Movie.query.get(id)
      movie = movie.format()
      actors = db.session.query(Actor.id, Actor.firstname, Actor.surname, Movie.title)\
        .join(Project, Movie.id == Project.movie_id)\
          .join(Actor, Project.actor_id == Actor.id)\
            .filter(Project.movie_id == id).all()
      actors = [{'actor_name':f'{actor.firstname} {actor.surname}', 'actor_id': actor.id} for actor in actors]
    except:
      abort(404)
    finally: 
      db.session.close()

    return jsonify({
      'success': True,
      'movie_details': movie, 
      'actors': actors,
      'actor_count': len(actors)
    }), 200

  @app.route('/movies', methods=('GET', 'POST'))
  @requires_auth('post:movies')
  def add_movie(jwt):
    try:
      title = request.get_json()['title'].title()
      release_date = request.get_json()['release_date']
      release_date = datetime.datetime.strptime(release_date, '%Y-%m-%d').date()
      new_movie = Movie(title=title, release_date=release_date)
      new_movie.add()
    except:
      abort(422)

    return jsonify({
      'success': True,
      'id': new_movie.id,
      'title': new_movie.title,
      'release_date': str(new_movie.release_date),
    }), 201

  @app.route('/movies/<int:id>', methods=('GET', 'PATCH'))
  @requires_auth('patch:movies')
  def edit_movie(jwt, id):
    try:
      movie = Movie.query.get(id)
      keys = list(request.get_json().keys())
    
      if 'title' in keys:
        movie.title = request.get_json()['title'].title()

      if 'release_date' in keys:
        movie.release_date = datetime.datetime.strptime(request.get_json()['release_date'], '%Y-%m-%d').date()

      # movie.edit()
    except:
      abort(422)

    return jsonify({
      'id': movie.id,
      'title': movie.title,
      'release_date': str(movie.release_date),
      'success': True 
    }), 200

  @app.route('/movies/<int:id>', methods=('GET', 'DELETE'))
  @requires_auth('delete:movies')
  def delete_movie(jwt, id):
    try:
      delete_movie = Movie.query.get(id)
      delete_movie.delete()
    except:
      abort(422)

    return jsonify({
      'success': True,
      'id': delete_movie.id,
      'title': delete_movie.title,
      'release_date': delete_movie.release_date,
    }), 200

##################  ERROR HANDLER ########################
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': 404,
      'message': "resource not found"
    }), 404

  @app.errorhandler(422)
  def could_not_process(error):
    return jsonify({
      'success': False,
      'error': 422,
      'message': "unprocessable"
    }), 422
  
  @app.errorhandler(AuthError)
  def auth_error(AuthError):
    error = AuthError.error
    status_code = AuthError.status_code
    return jsonify({
        'success': False,
        'error': status_code,
        'message': error
    }), status_code

  return app

APP = create_app()

if __name__ == '__main__':
    APP.run(host='0.0.0.0', port=8080, debug=True)