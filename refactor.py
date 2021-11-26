"""Contains function to transform data received from SQL query to data suitable for JSONifying. Used by app.py"""

from typing import Tuple, List
from scraper import file_headers


def make_dict(tup: Tuple, table: str) -> dict:
    """
    Converts tuple of contestant data to dictionary
    :param tup: tuple of contestant data, consisting of name, age, hometown, and outcome
    :param table: string indicating which table the data is from
    :return: dictionary of contestant data
    """
    key_list = file_headers[table].split(",")
    return {k: v for k, v in zip(key_list, tup)}


def make_list(table: str, search_result: List[Tuple]) -> List[dict]:
    """
    Converts list of tuples to list of dictionary
    :param table: table data came from
    :param search_result: list of tuples generated from database search
    :return: list of dictionaries, where each dictionary represents one table row
    """
    return [make_dict(row, table) for row in search_result]
