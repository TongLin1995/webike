from flask import Flask, request, Response, flash, redirect, url_for
from flask import render_template
from flask.ext.security import login_required, login_user
from flask.ext.login import (LoginManager, current_user, login_required,
                             login_user, logout_user, UserMixin, confirm_login, fresh_login_required)
#!/usr/bin/env python2
from datetime import datetime, timedelta
from databaseConnector import *
from grapher import *
import builtins
import hashlib
from User import User
from compute import detectTrips
import json

from flask import g, Blueprint
from trajectory import trajectoryClean

builtins.unicode = str

app = Flask(__name__)

SECRET_KEY = "yeah, not actually a secret"

app.config.from_object(__name__)

app.config["APPLICATION_ROOT"] = "/webike"

login_manager = LoginManager()

login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."
login_manager.refresh_view = "reauth"

USERS = dict()

login_manager.setup_app(app)


@app.before_request
def db_connect():
    g.dbc = databaseConnector()


@app.teardown_request
def db_disconnect(exception=None):
    g.dbc.shutDown()


@login_manager.user_loader
def load_user(userid):
    if userid in USERS:
        uoldname = USERS[userid].imei
        uoldpass = USERS[userid].password
        if checkDB(uoldname, uoldpass):
            return USERS[userid]
    return None

from sys import stderr


def print_err(*args, **kwargs):
    print(*args, file=stderr, **kwargs)


def checkDB(username, password):
    stmt = "select name, passhash from users where imei = \"{0}\"".format(username)
    cpass = [i for i in g.dbc.SQLSelectGenerator(stmt)]
    if cpass == []:
        flash("Sorry, user does not exist")
        return False, None
    elif cpass[0][1] != hashlib.sha256((password + "webikesalt").encode('utf-8')).hexdigest():
        flash("Sorry, password does not match")
        return False, None
    elif cpass[0][1] == hashlib.sha256((password + "webikesalt").encode('utf-8')).hexdigest():
        return True, cpass[0][0]


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST" and "imei" in request.form and "password" in request.form:
        imei = request.form["imei"]
        password = request.form["password"]
        worked, name = checkDB(imei, password)
        if worked:
            uid = hashlib.sha256(imei.encode('utf-8')).hexdigest()
            u = User(imei, name, password, uid)
            USERS[uid] = u
            login_user(u)
            return redirect(url_for("analyzer"))
        else:
            return redirect(url_for("login") + "?failure=true")
    elif request.method == "GET" and request.args.get("failure"):
        return render_template("auth.html", fail="true")
    else:
        return render_template("auth.html", fail="false")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(somewhere)


@app.route('/analyzer', methods=['GET'])
@login_required
def analyzer():
    return render_template('index.html', i=current_user.imei, name=current_user.name)


@app.route('/plotTripsOnDay', methods=['GET'])
@login_required
def dph():
    imei = request.args.get('imei')  # also accepted in URL, but defaults to 1
    dt = request.args.get('s').split("/")  # also accepted in URL, but defaults to 1
    ret = plotTripsOnDay(g.dbc, imei, int(dt[0].replace("\"", "")), int(dt[1]), int(dt[2].replace("\"", "")))
    print_err(ret)
    resp = Response(response=ret,
                    status=200,
                    mimetype="image/png")
    return resp


@app.route('/voltageOverTime', methods=['GET'])
@login_required
def vot():
    imei = request.args.get('imei')  # also accepted in URL, but defaults to 1
    dt = request.args.get('s').split("/")  # also accepted in URL, but defaults to 1
    ret = plotVoltage(g.dbc, imei, int(dt[0].replace("\"", "")), int(dt[1]), int(dt[2].replace("\"", "")))
    resp = Response(response=ret,
                    status=200,
                    mimetype="image/png")
    return resp


@app.route('/plotDistanceVsDay', methods=['GET'])
@login_required
def dpd():
    imei = request.args.get('imei')
    dt = request.args.get('s').split("/")
    numdays = int(request.args.get('nd'))
    ret = plotDistanceVsDay(g.dbc, imei, int(dt[0].replace("\"", "")), int(dt[1]), int(dt[2].replace("\"", "")), numdays)
    print_err(ret)
    resp = Response(response=ret,
                    status=200,
                    mimetype="image/png")
    return resp


@app.route('/plotTripLengthDistribution', methods=['GET'])
@login_required
def tld():
    imei = request.args.get('imei')
    dt = request.args.get('s').split("/")
    numdays = int(request.args.get('nd'))
    ret = plotTripLengthDistribution(g.dbc, imei, int(dt[0].replace("\"", "")), int(dt[1]), int(dt[2].replace("\"", "")), numdays)
    resp = Response(response=ret,
                    status=200,
                    mimetype="image/png")
    return resp


@app.route('/plotSpeedOnDay', methods=['GET'])
@login_required
def needforspeed():
    imei = request.args.get('imei')  # also accepted in URL, but defaults to 1
    dt = request.args.get('s').split("/")  # also accepted in URL, but defaults to 1
    ret = plotMaxSpeedTripOnDay(g.dbc, imei, int(dt[0].replace("\"", "")), int(dt[1]), int(dt[2].replace("\"", "")))
    resp = Response(response=ret,
                    status=200,
                    mimetype="image/png")
    return resp


@app.route('/getCoordsForGoogle', methods=['GET'])
@login_required
def googemapscoords():
    imei = request.args.get('imei')  # also accepted in URL, but defaults to 1
    dt = request.args.get('date').split("/")  # also accepted in URL, but defaults to 1
    curdate = datetime(int(dt[2].replace("\"", "")), int(dt[0]), int(dt[1].replace("\"", "")))
    end = curdate + timedelta(hours=23, minutes=59, seconds=59)
    longs, lats, tripStartTimes, tripEndTimes, dist, totalTime, stamps = trajectoryClean(g.dbc, imei, 0.08, int(dt[2].replace("\"", "")), int(dt[0].replace("\"", "")), int(dt[1]))
    return json.dumps({"lats": lats, "longs": longs, "start": tripStartTimes, "end": tripEndTimes, "d": dist, "ttime": totalTime, "stamps": stamps})


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="blizzard.cs.uwaterloo.ca")
