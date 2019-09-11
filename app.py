from flask import Flask, request, jsonify, render_template, redirect
import os
import json
import math
from pusher import Pusher
from datetime import datetime
from sqlalchemy import and_

from db import db_session, init_db
from models import Poll

app = Flask(__name__)


# PUSHER setup
pusher = Pusher(
	app_id = "855194",
	key = "918ee8d39b9cdd619aeb",
	secret = "2d29133b7be707d6649f",
	cluster = "us2",
	ssl = True
)

#######################################################################

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
	offsetX = request.form.get("offsetX")
	offsetY = request.form.get("offsetY")
	x = request.form.get("x")
	y = request.form.get("y")
	pid = request.form.get("pid")

	poll = db_session.query(Poll).filter_by(pid=pid).first()
	if(poll.started and not poll.completed):
		poll.x = poll.x + int(offsetX)
		poll.y = poll.y + int(offsetY)

		# calculate a win
		# complete if distance is greater than small radius
		dist = math.sqrt((poll.y - 300)**2 + (poll.x - 300)**2)
		if(dist > 240):
			print("COMPLETED")
			poll.completed = True


			# determine winner and add to list of winners
			options = poll.options.split("|")
			angle = float(math.atan2(poll.y - 300, poll.x-300))
			if(angle < 0):
				angle = math.pi * 2 + angle

			a = float(math.pi * 2) / len(options)
			print(angle, a)
			winner = "__UNKNOWN__"
			for index, o in enumerate(options):
				begin = a * index
				end = begin + a
				if (angle >= begin and angle < end):
					winner = o
					break

			poll.winners = poll.winners + winner + "|"

			pusher.trigger(pid, "notify-status", {"status": "COMPLETED", "winners": poll.winners.split("|")})

		db_session.commit()

		# push notification
		#if (math.sqrt((poll.x - int(x))**2 + (poll.y - int(y))**2) > 50):
		pusher.trigger(pid, "notify-move", {"x": poll.x, "y": poll.y})
		
		# get rid of this in response?
		resp = jsonify(new_point = {"x": poll.x, "y": poll.y})	
		resp.headers['Access-Control-Allow-Origin'] = '*'
		return resp, 200

	else:
		return "Unable to vote at this time.", 400


# get poll data
@app.route('/api/poll')
def getPoll():
	p = request.args.get("pid")

	# get by pid
	try:
		poll = db_session.query(Poll).filter_by(pid=p).first()

		
		resp = jsonify(
			data = {
				"question": poll.question,
				"options": poll.options.split("|"),
				"x": poll.x,
				"y": poll.y,
				"viewers": poll.viewers,
				"winners": poll.winners.split("|"),
				"status": "COMPLETED" if poll.completed else ("STARTED" if poll.started else "WAITING")
			}
		)

		resp.headers['Access-Control-Allow-Origin'] = '*'
		return resp, 200

	except Exception as e:
		print(e)
		return "This poll does not seem to exist.", 400

# start vote
@app.route('/api/start')
def start():
	pid = request.args.get("pid")
	password = request.args.get("password")

	# get by pid
	try:
		poll = db_session.query(Poll).filter_by(pid=pid).filter_by(password=password).first()
		poll.started = True
		db_session.commit()

		#push message saying owner started
		pusher.trigger(pid, "notify-status", {"status": "COMPLETED" if poll.completed else ("STARTED" if poll.started else "WAITING")})

		return "Poll started", 200

	except Exception as e:
		return "Invalid pid or password.", 400

# stop vote
@app.route('/api/stop')
def stop():
	pid = request.args.get("pid")
	password = request.args.get("password")

	# get by pid
	try:
		poll = db_session.query(Poll).filter_by(pid=pid).filter_by(password=password).first()
		poll.completed = True
		db_session.commit()
		#this is more like a stop-by-owner, push message saying owner stopped
		
		#push message saying owner started
		pusher.trigger(pid, "notify-status", {"status": "COMPLETED"})

		return "Poll completed", 200

	except:
		return "Invalid pid or password.", 400

# reset poll
@app.route('/api/reset')
def reset():
	pid = request.args.get("pid")
	password = request.args.get("password")

	# get by pid
	try:
		poll = db_session.query(Poll).filter_by(pid=pid).filter_by(password=password).first()
		poll.completed = False
		poll.started = False
		poll.viewers = 0 
		poll.x = 300
		poll.y = 300

		db_session.commit()
		
		#push message saying owner restarted
		pusher.trigger(pid, "notify-reset", {
			"question": poll.question,
			"options": poll.options.split("|"),
			"x": poll.x, 
			"y": poll.y, 
			"viewers": poll.viewers,
			"winners": poll.winners.split("|"),
			"status": "COMPLETED" if poll.completed else ("STARTED" if poll.started else "WAITING")
		})

		return "Poll reset", 200

	except:
		return "Invalid pid or password.", 400

# track leaving
@app.route('/api/enter')
def enter():
	pid = request.args.get("pid")
	
	# minus one viewer
	poll = db_session.query(Poll).filter_by(pid=pid).first()
	poll.viewers = poll.viewers + 1

	pusher.trigger(pid, "notify-viewers", {"total": poll.viewers})
	db_session.commit()

	return "Ok.", 200

# track leaving
@app.route('/api/leave')
def leave():
	pid = request.args.get("pid")
	
	# minus one viewer
	poll = db_session.query(Poll).filter_by(pid=pid).first()
	poll.viewers = max(poll.viewers - 1, 0)

	pusher.trigger(pid, "notify-viewers", {"total": poll.viewers})
	db_session.commit()

	return "Ok.", 200

# run Flask app
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == "__main__":
	app.run()
