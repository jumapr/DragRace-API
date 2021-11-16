import pandas as pd
import sqlite3
from typing import List, Tuple, Union


class Database:
    def __init__(self):
        self.db_name = 'drag_race.db'
        self.df = pd.DataFrame(pd.read_csv('data/contestants.csv'))
        self.select_all_and_join = '''SELECT Contestants.name, Contestants.age, Hometowns.hometown, Outcomes.outcome,
                        Contestants.season FROM Contestants JOIN Hometowns JOIN Outcomes 
                        ON (Contestants.hometown_id = Hometowns.id AND Contestants.outcome_id = Outcomes.id)'''

    def create_database(self):
        """
        Creates the Database table by creating the Hometown, Outcome, and Contestants tables in the proper order. Only needs
        to be run the first time the database is created.
        """
        self.create_hometown_table()
        self.create_outcome_table()
        self.create_contestant_table()

    def create_hometown_table(self):
        """
        Creates Hometowns table in the database. Inserts unique hometowns from the Pandas DataFrame into the database.
        """
        # create hometown table
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Hometowns (
                        id integer primary key,
                        hometown text)
                        ''')
        # insert hometowns into table
        hometowns = self.df['hometown'].unique()
        for hometown in hometowns:
            cursor.execute('INSERT INTO Hometowns (hometown) VALUES(?)', (hometown,))
        conn.commit()

    def create_outcome_table(self):
        """
        Creates Outcomes table in the database. Inserts the unique outcomes from the Pandas DataFrame into the table.
        """
        # create outcome table
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Outcomes (
                        id integer primary key,
                        outcome text)
                        ''')
        # insert outcomes into table
        outcomes = self.df['outcome'].unique()
        for outcome in outcomes:
            cursor.execute('INSERT INTO Outcomes (outcome) VALUES(?)', (outcome,))
        conn.commit()
        conn.close()

    def create_contestant_table(self):
        """
        Loads data from contestant CSV into database
        """
        # create table
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Contestants (
                       id integer primary key,
                       name text,
                       age integer,
                       hometown_id integer,
                       outcome_id integer,
                       season integer)
                       ''')
        # insert data from CSV into table
        for row in self.df.itertuples():
            # find hometown ID
            hometown_id = cursor.execute('SELECT id FROM Hometowns WHERE hometown=?', (row.hometown,)).fetchone()[0]
            # find outcome ID
            outcome_id = cursor.execute('SELECT id FROM Outcomes WHERE outcome=?', (row.outcome,)).fetchone()[0]
            cursor.execute('INSERT INTO Contestants (name, age, hometown_id, outcome_id, season) VALUES(?, ?, ?, ?, ?)',
                           (row.name, int(row.age), hometown_id, outcome_id, int(row.season))
                           )
        conn.commit()
        conn.close()

    def select_all(self) -> List[Tuple]:
        """
        Gets data from all contestants from the database
        :return: List with tuple for each contestant
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        all_contestants = cursor.execute(self.select_all_and_join).fetchall()
        conn.close()
        return all_contestants

    def search_contestants(self, name: Union[str, None], outcome: Union[str, None], season: Union[str, None],
                           min_age: Union[str, None], max_age: Union[str, None]):
        """
        Searches for contestants matching specific criteria. One or more of the parameters may be None
        :param name: name of contestant, which may be partial
        :param outcome: outcome to search for (e.g. 4th for 4th place)
        :param season: season to search for
        :param min_age: minimum age of contestants to search for
        :param max_age: maximum age of contestants to search for
        :return: List of Tuples, where each Tuple contains the data for one contestant
        """
        conditions = []
        condition_values = []
        if name:
            conditions.append('Contestants.name LIKE ?')
            condition_values.append('%' + name + '%')
        if outcome:
            processed_outcome = process_outcome_search(outcome)
            # can't search for exact match in case of ties (e.g. 13th/14th place)
            conditions.append('(Outcomes.outcome LIKE ? OR Outcomes.outcome LIKE ?)')
            condition_values.append(processed_outcome + '%')
            condition_values.append('%' + '/' + processed_outcome)
        if min_age:
            int_min_age = validate_integer_input(min_age)
            if int_min_age:
                conditions.append('Contestants.age >=?')
                condition_values.append(int_min_age)
        if max_age:
            int_max_age = validate_integer_input(max_age)
            if int_max_age:
                conditions.append('Contestants.age <=?')
                condition_values.append(int_max_age)
        if season:
            int_season = validate_integer_input(season)
            if int_season:
                conditions.append('Contestants.season=?')
                condition_values.append(int_season)
        conditions = " AND ".join(conditions)
        condition_values = tuple(condition_values)
        print(self.select_all_and_join + ' WHERE ' + conditions)
        print(condition_values)
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        matching_contestants = cursor.execute(self.select_all_and_join + ' WHERE ' + conditions, condition_values).fetchall()
        conn.close()
        return matching_contestants


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


def validate_integer_input(parameter: str) -> Union[None, str]:
    """
    Validates integer input
    :param parameter:
    :return:
    """
    try:
        result = int(parameter)
    except ValueError:
        result = None
    return result
