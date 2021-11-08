from flask import Flask, jsonify, render_template, request
from typing import Tuple
from database import Database

app = Flask(__name__)
db = Database()

# success and error messages for JSON responses
errors = ({"Not Found:": "Sorry, we couldn't find that contestant."},)


def make_contestant_dict(tup: Tuple) -> dict:
    """
    Converts tuple of contestant data to dictionary
    :param tup: tuple of contestant data, consisting of name, age, hometown, and outcome
    :return: dictionary of contestant data
    """
    return {"name": tup[0], "age": tup[1], "hometown": tup[2], "outcome": tup[3], "season": tup[4]}


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/all')
def get_all_contestants():
    """
    Get all contestants from the database
    :return: JSON data for all contestants
    """
    all_contestants_dicts = [make_contestant_dict(contestant) for contestant in db.select_all()]
    return jsonify(contestants=all_contestants_dicts)


@app.route('/search')
def search_contestants():
    """
    Search for specific contestant(s)
    :return: JSON data for specific contestant
    """
    name = request.args.get('name')
    outcome = request.args.get('outcome')
    season = request.args.get('season')
    matching_contestants = db.search_contestants(name, outcome, season)
    if matching_contestants:
        matching_contestants_list = [make_contestant_dict(contestant) for contestant in matching_contestants]
        return jsonify(contestants=matching_contestants_list)
    # if it's not in the database, return a Not Found error
    else:
        return jsonify(error=errors[0])


if __name__ == '__main__':
    app.run(debug=True)
