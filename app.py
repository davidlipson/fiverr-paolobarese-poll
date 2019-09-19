from flask import Flask, request, jsonify, render_template, redirect
import os
import json
import math
from pusher import Pusher
from datetime import datetime
from sqlalchemy import and_
import time, threading

from db import db_session, init_db
from models import Poll, Voter

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

## used as timer; every 0.3 seconds updates survey.
def pulseNotify():
	# notify each active survey to update
	r = db_session.query(Poll).filter_by(started=True).filter_by(completed=False).all()
	for p in r:
		# voters
		voters = db_session.query(Voter).filter_by(poll_id=p.id).all()
		
		# get sum of offsets
		offsetX = 0
		offsetY = 0

		for v in voters:
			offsetX = offsetX + (v.x - p.x)
			offsetY = offsetY + (v.y - p.y)

		# reset poll to new location
		p.x = p.x + offsetX
		p.y = p.y + offsetY

		for v in voters:
			v.x = p.x
			v.y = p.y

		db_session.commit()

		pusher.trigger(str(p.pid), "notify-move", {"x": p.x, "y": p.y})


		# calculate a win
		# complete if distance is greater than small radius
		dist = math.sqrt((p.y - 300)**2 + (p.x - 300)**2)
		if(dist > 240):
			p.completed = True

			# determine winner and add to list of winners
			options = p.options.split("|")
			angle = float(math.atan2(p.y - 300, p.x-300))
			if(angle < 0):
				angle = math.pi * 2 + angle

			a = float(math.pi * 2) / len(options)
			winner = "__UNKNOWN__"
			for index, o in enumerate(options):
				begin = a * index
				end = begin + a
				if (angle >= begin and angle < end):
					winner = o
					break

			p.winners = p.winners + winner + "|"

			db_session.commit()
			pusher.trigger(str(p.pid), "notify-status", {"status": "COMPLETED", "winners": p.winners.split("|")})

	threading.Timer(0.3, pulseNotify).start()

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
	vid = request.form.get("vid")

	poll = db_session.query(Poll).filter_by(pid=pid).first()
	voter = db_session.query(Voter).filter_by(id=vid).first()
	if(poll.started and not poll.completed):
		voter.x = voter.x + int(offsetX)
		voter.y = voter.y + int(offsetY)
	
		db_session.commit()

		# push notification
		#if (math.sqrt((poll.x - int(x))**2 + (poll.y - int(y))**2) > 50):
		#pusher.trigger(pid, "notify-move", {"x": poll.x, "y": poll.y})
		
		# get rid of this in response?
		resp = jsonify(new_point = {"x": voter.x, "y": voter.y})	
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

		# create voter
		voter = Voter(poll.id, poll.x, poll.y)
		db_session.add(voter)
		db_session.flush()
		db_session.commit()

		resp = jsonify(
			data = {
				"question": poll.question,
				"options": poll.options.split("|"),
				"x": voter.x,
				"y": voter.y,
				"vid": voter.id,
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

		voters = db_session.query(Voter).filter_by(poll_id=poll.id).all()
		for v in voters:
			v.x = poll.x
			v.y = poll.y

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
	pulseNotify()
	app.run()

