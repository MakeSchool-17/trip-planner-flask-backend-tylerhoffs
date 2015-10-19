from flask import Flask, request, make_response, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient
from bson.objectid import ObjectId
from utils.mongo_json_encoder import JSONEncoder
import bcrypt
from functools import wraps

# Basic Setup
app = Flask(__name__)
mongo = MongoClient('localhost', 27017)
app.db = mongo.develop_database
api = Api(app)


def check_auth(username, password):
    return username == 'admin' and password == 'secret'


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            message = {'error': 'Basic Auth Required.'}
            resp = jsonify(message)
            resp.status_code = 401
            return resp

        return f(*args, **kwargs)
    return decorated


# Implement REST Resource
class MyObject(Resource):

    def post(self):
        # new_myobject = request.json
        myobject_collection = app.db.myobjects
        result = myobject_collection.insert_one(request.json)

        myobject = myobject_collection.find_one({"_id": ObjectId(result.inserted_id)})

        return myobject

    def get(self, myobject_id):
        myobject_collection = app.db.myobjects
        myobject = myobject_collection.find_one({"_id": ObjectId(myobject_id)})

        if myobject is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            return myobject

# Add REST resource to API
api.add_resource(MyObject, '/myobject/', '/myobject/<string:myobject_id>')


class User(Resource):
    def post(self):
        new_user = request.json
        user_collection = app.db.users
        user_pass = new_user["password"]
        user_pass = user_pass.encode('utf-8')
        hashed = bcrypt.hashpw(user_pass, bcrypt.gensalt(12))
        new_user["password"] = hashed.decode('utf-8')
        result = user_collection.insert_one(new_user)
        user = user_collection.find_one({"_id": ObjectId(result.inserted_id)})

        return user

    def get(self, user_id):
        user_collection = app.db.users
        user = user_collection.find_one({"_id": ObjectId(user_id)})

        if user is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            return user

api.add_resource(User, '/users/', '/users/<string:user_id>')


class Trip(Resource):
    # @requires_auth
    def post(self):
        # new_trip = request.json
        trip_collection = app.db.trips
        result = trip_collection.insert_one(request.json)

        trip = trip_collection.find_one({"_id": ObjectId(result.inserted_id)})

        return trip

    # @requires_auth
    def get(self, trip_id):
        trip_collection = app.db.trips
        trip = trip_collection.find_one({"_id": ObjectId(trip_id)})

        if trip is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            return trip

    def delete(self, trip_id):
        # new_trip = request.json
        trip_collection = app.db.trips

        result = trip_collection.delete_many({"_id": ObjectId(trip_id)})

        if result == 0:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            response = jsonify(data=[])
            response.status_code = 200
            return response

    def put(self, trip_id):
        new_trip = request.json
        trip_collection = app.db.trips
        result = trip_collection.replace_one({"_id": ObjectId(trip_id)}, new_trip)
        if result.modified_count == 0:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            response = jsonify(data=[])
            response.status_code = 200
            return response

api.add_resource(Trip, '/trips/', '/trips/<string:trip_id>')


# provide a custom JSON serializer for flaks_restful
@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(JSONEncoder().encode(data), code)
    resp.headers.extend(headers or {})
    return resp

if __name__ == '__main__':
    # Turn this on in debug mode to get detailled information about request related exceptions: http://flask.pocoo.org/docs/0.10/config/
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(debug=True)
