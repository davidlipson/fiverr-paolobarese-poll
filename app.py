from flask import Flask, request, jsonify, render_template, redirect
import os
import json
import pusher
from datetime import datetime

from db import db_session, init_db
from models import Poll

app = Flask(__name__)

# ENDPOINTS

# home page - create new poll
@app.route('/')
def index():
	return render_template('index.html')

# poll page
@app.route('/poll')
def poll():
	return render_template('poll.html')



#######################################################################

# API


# generate new poll from home page
@app.route('/api/generate', methods=["POST"])
def generate():

	# get password, questino and options from POST data
	question = request.form.get("question")
	options = json.loads(request.form.get("options"))["options"]
	password = request.form.get("password")

	# generate entry and new url pid
	poll = Poll(question, options, password)
	db_session.add(poll)
	db_session.flush()
	db_session.commit()
	
	# return url pid
	resp = jsonify(pid = poll.pid)
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
	p = request.args.get("pid")

	# get by pid
	q, o = db_session.query(Poll.question, Poll.options).filter_by(pid=p).first()
	
	resp = jsonify(data = {
			"question": q,
			"options": o.split("|")
		})
	resp.headers['Access-Control-Allow-Origin'] = '*'
	return resp


# run Flask app
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == "__main__":
	app.run()
