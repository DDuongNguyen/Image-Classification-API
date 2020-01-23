from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import numpy
import subprocess
import json
import requests
import pdb

app = Flask(__name__)
api = Api(app)

# client = MongoClient('mongodb://localhost:27017')
client = MongoClient('mongodb://db:27017')
db = client.ImageRecognition
users = db.Users


def UserExist(username):
    return False if users.find({"Username": username}).count() == 0 else True


def verifyuser(username, password):
    if not UserExist(username):
        return False
    hashed_pw = users.find({'Username': username})[0]['Password']
    return True if bcrypt.checkpw(password.encode('UTF8'), hashed_pw) else False


def countTokens(username):
    tokens = users.find({'Username': username})[0]['Tokens']
    return tokens


class Register(Resource):
    def post(self):
        data = request.get_json()
        username = data['username']
        password = data['password']

        if UserExist(username):
            retJson = {
                'message': 'yo already exist this user'
            }
            return retJson

        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Tokens": 5
        })
        retJson = {
            "Message": "sucesfully created your user",
            "Username": username,
            "Password": str(hashed_pw),
            "Tokens": 5
        }
        return jsonify(retJson)


class Classify(Resource):
    def post(self):
        data = request.get_json()
        username = data['username']
        password = data['password']
        image_url = data['image_url']
        if not verifyuser(username, password):
            retJson = {
                'message': 'wrong user or password m8'
            }
            return jsonify(retJson)
        current_token = countTokens(username)
        if current_token <= 0:
            retJson = {
                'message': 'not enough token m8'
            }
            return jsonify(retJson)

        requested_image = requests.get(image_url)
        retJson = {}
        with open('temp.jpg', 'wb') as f:
            f.write(requested_image.content)
            proc = subprocess.Popen('python classify_image.py --model_dir=. --image_file=./temp.jpg',
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            ret = proc.communicate()[0]
            proc.wait()
            with open("text.txt") as f:
                retJson = json.load(f)


        users.update({"Username": username}, {
            "$set": {
                "Tokens": current_token - 1
            }
        })
        return retJson


class Refill(Resource):
    def post(self):
        data = request.get_json()
        username = data['username']
        password = data['admin_password']
        refill_amount = data['refill_amount']
        # verify user
        if not UserExist(username):
            retJson = {
                'message': 'wrong username'
            }
            return jsonify(retJson)
        # verify admin password
        admin_password = 'meow'
        if not password == admin_password:
            retJson = {
                'message': 'wrong admin password mang'
            }
            return jsonify(retJson)
        # update refill
        current_tokens = countTokens(username)
        users.update({
            'Username': username
        }, {
            '$set': {
                'Tokens': current_tokens + refill_amount
            }
        })
        retJson = {
            'message': 'you updated your tokens dough',
            'current_token': current_tokens + refill_amount,
        }
        return jsonify(retJson)


api.add_resource(Register, '/register')
api.add_resource(Refill, '/refill')
api.add_resource(Classify, '/classify')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
