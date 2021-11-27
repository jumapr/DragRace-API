"""Contains functions to process and/or validate search parameters input by the user. Used by database.py"""
import datetime
from typing import Union


def process_outcome_search(searched_outcome: str) -> str:
    """
    Processes a provided parameter for outcome. Particularly, handles non-cardinal number outcomes: Winner, Runner-Up,
    and Disqualified.
    :param searched_outcome: user-provided value for `outcome` to search
    :return: processed string for `outcome`, to match database format
    """
    if searched_outcome[0].isalpha():
        searched_outcome = searched_outcome.title()
    elif searched_outcome in ('1', '1st'):
        searched_outcome = 'Winner'
    elif searched_outcome in ('2', '2nd'):
        searched_outcome = 'Runner-Up'
    return searched_outcome


def add_wildcards(string: str) -> str:
    """
    Prepends and appends a '%' to the string, which represents a SQL wildcard
    :param string: string
    :return: '%' + string + '%'
    """
    return '%' + string + '%'


def validate_integer_input(parameter: str) -> Union[None, int]:
    """
    Converts string input to integer or returns None if it can't be converted
    :param parameter: string input
    :return: `parameter` converted to integer or None
    """
    try:
        result = int(parameter)
    except ValueError:
        result = None
    return result


def is_valid_date(date_str) -> Union[str, None]:
    """
    Checks if `date_str` is a valid date in format YYYY-MM-DD
    :param date_str: user-input search parameter
    :return: input if valid date, None if not
    """
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        print('invalid date')
        return None
