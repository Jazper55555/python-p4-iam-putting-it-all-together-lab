#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

@app.before_request
def check_login():
    access_list = [
        'home',
        'users',
        'signup',
        'login',
        'check_session'
    ]

    if request.endpoint not in access_list and not session.get('user_id'):
        return {'error': '401 Unauthorized'}, 401
    
@app.route('/', endpoint='home')
def Home():
    return 'Hello Luca<br><br>Welcome to the Home Page'

@app.route('/users', endpoint='users')
def users():
    users = User.query.all()
    return [user.to_dict() for user in users], 200


class Signup(Resource):
    def post(self):
        username = request.get_json().get('username')
        password = request.get_json().get('password')
        image_url = request.get_json().get('image_url')
        bio = request.get_json().get('bio')
        
        new_user = User(
            username = username,
            image_url = image_url,
            bio = bio
        )
        new_user.password_hash = password

        try:
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            return new_user.to_dict(), 201
        
        except IntegrityError:
            return {'error': '422 Unprocessable Entity'}, 422


class CheckSession(Resource):
    def get(self):
        user_id = session['user_id']
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            return user.to_dict(), 200
        
        return {}, 401


class Login(Resource):
    def post(self):
        username = request.get_json()['username']
        password = request.get_json()['password']

        user = User.query.filter(User.username == username).first()

        if user:
            if user.authenticate(password):
                session['user_id'] = user.id
                return user.to_dict(), 200
            
        return {'error': '401 Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        user_id = session['user_id']
        if user_id:
            session['user_id'] = None
            return {}, 204
        return {'error': '401 Unauthorized'}, 401


class RecipeIndex(Resource):
    def get(self):
        user = User.query.filter(User.id == session['user_id']).first()
        return [recipe.to_dict() for recipe in user.recipes], 200
    
    def post(self):
        title = request.get_json()['title']
        instructions = request.get_json()['instructions']
        minutes = request.get_json()['minutes_to_complete']

        if session.get('user_id'):
            try:
                recipe = Recipe(
                    title = title,
                    instructions = instructions,
                    minutes_to_complete = minutes,
                    user_id = session['user_id']
                )
                db.session.add(recipe)
                db.session.commit()
                return recipe.to_dict(), 201

            except IntegrityError:
                return {'error': '422 Unprocessable Entity'}, 422
            
        return {'error': '401 Unauthorized'}, 401
        

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)