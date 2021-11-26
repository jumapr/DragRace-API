import functools
import inspect
import refactor
from flask import Flask, jsonify, render_template, request, abort
from database import Database

app = Flask(__name__)
db = Database()
search_funcs = {'contestants': db.search_contestants, 'episodes': db.search_episodes}


@app.route("/")
def home():
    return render_template("index.html")


@app.errorhandler(404)
def page_not_found(e):
    """
    Renders 404.html when a page not found error occurs
    :param e: error
    :return: 404.html
    """
    return render_template('404.html'), 404


def check_table(func):
    """
    Decorator that checks if the table in the route is valid
    :param func: function to wrap
    :return: wrapper function
    """
    @functools.wraps(func)
    def wrapper_check_table(table):
        if table not in search_funcs:
            abort(404)
        else:
            return func(table)
    return wrapper_check_table


@app.route('/all/<table>')
@check_table
def get_all(table: str):
    """
    Get all data from a given table in the database
    :return: JSON response or 404 if invalid table name is provided
    """
    return jsonify(contestants=refactor.make_list(table, db.select_all(table)))


@app.route('/search/<table>')
@check_table
def search_api(table: str):
    """
    Handles search requests to the API
    :param table: database table - contestants or episodes
    :return: JSON response or 404 if invalid table name is provided
    """
    args = [request.args.get(param) for param in get_search_params(table)]
    return do_search(table, *args)


@app.route('/formsearch/<table>', methods=["GET", "POST"])
@check_table
def form_search(table: str):
    """
    Gets data from HTML form to do a search
    :param table: database table - contestants or episodes
    :return: for "GET" request, renders form template. For "POST" request, returns JSON response
    """
    if request.method == "POST":
        args = [request.form.get(param) for param in get_search_params(table)]
        return do_search(table, *args)
    return render_template("form.html", table=table)


def do_search(table, *args):
    """
    Calls the appropriate database search function, based on the table
    :param table: database table - contestants or episodes
    :param args: search parameters to use to supply to the search function
    :return: JSON response with matching data
    """
    search_result = search_funcs[table](*args)
    if search_result:
        return jsonify({table: refactor.make_list(table, search_result)})
    else:
        return jsonify({table: get_error_message(table)})


def get_error_message(table: str):
    """
    Creates error message for a given table
    :param table: database table - contestants or episodes
    :return: error message
    """
    return "Sorry, we couldn't find any {} matching that criteria.".format(table)


def get_search_params(table: str):
    """
    Gets supported search parameters for a given table
    :param table: database table - contestants or episodes
    :return: tuple of search parameters
    """
    return tuple(inspect.getfullargspec(search_funcs[table])[0][1:])


if __name__ == '__main__':
    app.run(debug=True)
