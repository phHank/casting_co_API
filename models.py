import os
import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

database_path = os.environ['DATABASE_URL']

db = SQLAlchemy()

def setup_db(app, database_path=database_path):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    migrate = Migrate(app, db)    

class Project(db.Model):
    __tablename__ = 'projects'

    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('actors.id'), primary_key=True)
    movies = db.relationship('Movie', back_populates='actor')
    actors = db.relationship('Actor', back_populates='movie')

    def __repr__(self):
        return f'<Project - MovieID {self.movie_id}, ActorID {self.actor_id}>'

    def add(self):
        db.session.add(self)
        db.session.commit()

class Movie(db.Model):
    __tablename__ = 'movies'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False, unique=True)
    release_date = db.Column(db.Date, nullable=False)
    actor = db.relationship('Project', back_populates='movies', cascade='all, delete-orphan', lazy=True)
    
    def __repr__(self):
      return f'<Movie ID {self.id} and Title {self.title}>'

    def format(self):
        return {
            'id': self.id,
            'title': self.title, 
            'release_date': str(self.release_date)
        }

    def add(self):
        db.session.add(self)
        db.session.commit()

    def edit(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Actor(db.Model):
    __tablename__ = 'actors'

    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(120), nullable=False)
    surname = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    movie = db.relationship('Project', back_populates='actors', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
      return f'<Actor ID {self.id} and Name {self.firstname[0]}. {self.surname}>'

    def format(self):
        return {
            'id': self.id,
            'first name': self.firstname,
            'second name': self.surname, 
            'age': self.age,
            'gender': self.gender
        }
    
    def short_format(self):
        return {
            'id': self.id,
            'name': f'{self.firstname} {self.surname}'
        }

    def add(self):
        db.session.add(self)
        db.session.commit()

    def edit(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class Token(db.Model):
    __tablename__ = 'jwt_store'

    id = db.Column(db.Integer, primary_key=True)
    jwt = db.Column(db.String(), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<id: {id}, jwt: {jwt}, timestamp: {timestamp}>'

    def add(self):
        db.session.add(self)
        db.session.commit()

    def delete_expired(self):
        expiration_seconds = 36000
        limit = datetime.datetime.now() - datetime.timedelta(seconds=expiration_seconds)
        self.query.filter(self.timestamp <= limit).delete()
        db.session.commit() 

    def delete_all(self):
        self.query.delete()
        db.session.commit()