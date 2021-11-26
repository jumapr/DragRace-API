import inspect

import refactor
from flask import Flask, jsonify, render_template, request
from database import Database

app = Flask(__name__)
db = Database()

# error messages for JSON responses
errors = {'contestants': {"Not Found:": "Sorry, we couldn't find any contestants matching that criteria."},
          'episodes': {"Not Found:": "Sorry, we couldn't find any episodes matching that criteria."}}


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/all/<table>')
def get_all(table: str):
    """
    Get all data from a given table in the database
    :return: JSON data for table
    """
    return jsonify(contestants=refactor.make_list(table, db.select_all(table)))


@app.route('/search/<table>')
def search(table: str):
    search_funcs = {'contestants': db.search_contestants, 'episodes': db.search_episodes}
    search_params = {'contestants': tuple(inspect.getfullargspec(search_funcs['contestants'])[0][1:]),
                     'episodes': tuple(inspect.getfullargspec(search_funcs['episodes'])[0][1:])}
    args = [request.args.get(param) for param in search_params[table]]
    search_result = search_funcs[table](*args)
    if search_result:
        return jsonify({table: refactor.make_list(table, search_result)})
    else:
        return jsonify(error=errors[table])


if __name__ == '__main__':
    app.run(debug=True)
