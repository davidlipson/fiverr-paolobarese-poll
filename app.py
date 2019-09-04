from flask import Flask, request, jsonify, render_template, redirect
import os
import json
import pusher
from datetime import datetime

from db import db_session
from models import Coord

app = Flask(__name__)

# ENDPOINTS

# home page - create new poll
@app.route('/')
def index():
	return render_template('index.html')

# poll page
@app.route('/poll')
def poll():
	pid = request.args.get('pid')
	print(pid)

	return render_template('poll.html')



#######################################################################

# API


# generate new poll from home page
@app.route('/api/generate', methods=["POST"])
def generate():
	# get password, questino and options from POST data
	question = request.form.get("question")
	options = request.form.get("options")
	password = request.form.get("password")

	# generate entry and new url pid

	# return url pid
	resp = jsonify(pid = "123")
	resp.headers['Access-Control-Allow-Origin'] = '*'
	return resp

# notify user move of mouse
@app.route('/api/notifyMove', methods=["POST"])
def notifyMove():
	#must also store the actual mouse value and check always that it hasn't been voted completely
	x = request.form.get("x")
	y = request.form.get("y")
	resp = jsonify(offset = {"x": int(x), "y": int(y)})
	resp.headers['Access-Control-Allow-Origin'] = '*'
	return resp

# get poll data
@app.route('/api/poll')
def getPoll():
	d = {
		"question": "What's the question?", 
		"options": ["Test1", "Test2", "Test3", "Test4", "Test5", "Test6"]
	}
	
	resp = jsonify(data = d)
	resp.headers['Access-Control-Allow-Origin'] = '*'
	return resp


# run Flask app
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == "__main__":
	app.run()
