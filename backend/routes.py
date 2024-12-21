from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route('/health', methods=['GET'])
def health():
    return {'status':'ok'}, 200

@app.route('/count', methods=['GET'])
def count():
    try:
        return {'count': db.songs.count_documents({})}, 200
    except:
        return {'message': 'Unknown server error'}, 500

@app.route('/song', methods=['GET'])
def songs():
    try:
        return {'songs': parse_json(list(db.songs.find({})))}, 200
    except:
        return {'message': 'Unknown server error'}, 500

@app.route('/song/<int:id>', methods=['GET'])
def get_song_by_id(id):
    try:
        song = db.songs.find_one({'id': id})
        return json_util.dumps(song), 200
    except:
        return {'message': 'Unknown server error'}, 500

@app.route('/song', methods=['POST'])
def create_song():
    try:
        song = request.json
        if db.songs.find_one({'id': song['id']}) is not None:
            return {'message': f'song with id {song["id"]} ready present'}
        id = db.songs.insert_one({'id': song['id'], 'lyrics': song['lyrics'], 'title': song['title']})
        return {'inserted id': json_util.dumps(id.inserted_id)}, 201
    except:
        return {'message': 'Unknown server error'}, 500

@app.route('/song/<int:id>', methods=['PUT'])
def update_song(id):
    try:
        song_data = request.json

        if db.songs.find_one({'id': id}) is None:
            return {'message': 'song not found'}

        new_values = {'lyrics': song_data['lyrics'], 'title': song_data['title']}
        result = db.songs.update_one({'id': id}, {'$set': new_values})

        if result.modified_count == 0:
            return {'message': 'song found, but nothing updated'}, 200

        song = db.songs.find_one(result.upserted_id)
        return json_util.dumps(song), 201
    except:
        return {'message': 'Unknown server error'}, 500

@app.route('/song/<int:id>', methods=['DELETE'])
def delete_song(id):
    try:
        result = db.songs.delete_one({'id': id})
        
        if result.deleted_count == 0:
            return {'message': 'song not found'}, 404

        return {}, 204
    except:
        return {'message': 'Unknown server error'}, 500
