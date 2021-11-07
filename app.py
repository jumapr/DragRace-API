from flask import Flask, jsonify, render_template, request
from typing import Tuple
import database

app = Flask(__name__)


# success and error messages for JSON responses
errors = ({"Not Found:": "Sorry, we couldn't find that contestant."},)


def make_contestant_dict(tup: Tuple) -> dict:
    """
    Converts tuple of contestant data to dictionary
    :param tup: tuple of contestant data, consisting of name, age, hometown, and outcome
    :return: dictionary of contestant data
    """
    return {"name": tup[0], "age": tup[1], "hometown": tup[2], "outcome": tup[3]}


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/all')
def get_all_contestants():
    """
    Get all contestants from the database
    :return: JSON data for all contestants
    """
    all_contestants_dicts = [make_contestant_dict(contestant) for contestant in database.select_all()]
    return jsonify(contestants=all_contestants_dicts)


@app.route('/search')
def search_contestants():
    """
    Search for specific contestant(s)
    :return: JSON data for specific contestant
    """
    raise NotImplementedError


if __name__ == '__main__':
    app.run(debug=True)
