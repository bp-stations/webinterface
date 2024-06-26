#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, g, send_file
from datetime import datetime, timezone
from os.path import isfile, join
from dotenv import load_dotenv
from pathlib import Path
from os import listdir
import requests
import sqlite3

load_dotenv()
app = Flask(__name__)
script_path = Path(__file__).parent.absolute()
icon_folder = script_path.joinpath("./static/images/icons")
icon_data = [f.replace(".avif", "") for f in listdir(icon_folder) if isfile(join(icon_folder, f))]


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("./data/aral.db")
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.template_filter("euro")
def euro(value):
    value = float(value) / 100
    return "{:,.2f} €".format(value)


@app.template_filter("strftime")
def _jinja2_filter_datetime(date):
    # Parse the input date string into a datetime object
    date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    date = date.replace(tzinfo=timezone.utc).astimezone(tz=None)

    # Format the datetime as a string
    return date.strftime("%H:%M")


@app.route("/sitemap.xml", methods=["GET"])
def sitemap():
    return send_file("./data/sitemap.xml")


@app.route("/robots.txt", methods=["GET"])
def robots():
    return send_file("./static/robots.txt")


@app.route("/", methods=["GET"])
def index():
    cursor = get_db().cursor()
    station_count = cursor.execute("SELECT COUNT(*) FROM stations;").fetchone()[0]
    return render_template("index.html", station_count=station_count)


def is_it_true(value):
    return value.lower() == "true"


@app.route("/map", methods=["GET"])
def display_map():
    lat = request.args.get("lat", default=51, type=float)
    lng = request.args.get("lng", default=11, type=float)
    zoom = request.args.get("zoom", default=6, type=int)
    disable_control = request.args.get(
        "disable_control", default=False, type=is_it_true
    )
    tmp_station_id = request.args.get("station", type=int)
    cursor = get_db().cursor()

    if tmp_station_id:
        tmp_stations = cursor.execute(
            "SELECT * FROM stations WHERE id = ?;", (tmp_station_id,)
        ).fetchall()
        bounds = cursor.execute(
            "SELECT MIN(lat)-1, MIN(lng)-1, MAX(lat)+1, MAX(lng)+1 FROM stations WHERE id = ?;",
            (tmp_station_id,),
        ).fetchone()
    else:
        tmp_stations = cursor.execute("SELECT * FROM stations;").fetchall()
        bounds = cursor.execute(
            "SELECT MIN(lat)-1, MIN(lng)-1, MAX(lat)+1, MAX(lng)+1 FROM stations;"
        ).fetchone()
    return render_template(
        "map.html",
        tmp_stations=tmp_stations,
        bounds=bounds,
        lat=lat,
        lng=lng,
        zoom=zoom,
        disable_control=disable_control,
    )


@app.route("/raw/search", methods=["GET"])
def search():
    search_term = request.args.get("search")

    if not search_term:
        return ""

    if len(search_term) < 4:
        return ""

    search_term = search_term.lower()
    cursor = get_db().cursor()

    return_stations = cursor.execute(
        "SELECT * FROM stations WHERE LOWER(name) LIKE ? OR LOWER(city) LIKE ? OR LOWER(postcode) LIKE ?",
        (
            f"%{search_term}%",
            f"%{search_term}%",
            f"%{search_term}%",
        ),
    ).fetchall()

    return render_template("raw_search.html", stations=return_stations)


@app.route("/station/<int:station_id>", methods=["GET"])
def station(station_id):
    if not station_id:
        return redirect(url_for("index"))

    cursor = get_db().cursor()
    local_station_data = cursor.execute(
        "SELECT postcode, city, name, lat, lng FROM stations WHERE id = ?;",
        (station_id,),
    ).fetchone()
    if not local_station_data:
        return redirect(url_for("index"))

    try:
        station_data = requests.get(
            f"https://api.tankstelle.aral.de/api/v2/stations/{station_id}/prices"
        ).json()
    except TimeoutError:
        print("api/we are offline, returning empty data")
        station_data = []

    return render_template(
        "station.html",
        local_station_data=local_station_data,
        station_data=station_data,
        station_id=station_id,
        icon_data=icon_data,
    )


if __name__ == "__main__":
    # during deploy waitress is used like this:
    # waitress-serve --host 127.0.0.1 --port 5000 app:app
    app.run(debug=True)
