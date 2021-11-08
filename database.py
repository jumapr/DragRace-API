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

    def search_contestants(self, name: Union[str, None], outcome: Union[str, None], season: Union[str, None]):
        """
        Searches for contestants matching specific criteria. One or more of the parameters may be None
        :param name: name of contestant, which may be partial
        :param outcome: outcome to search for (e.g. 4th for 4th place)
        :param season: season to search for
        :return: List of Tuples, where each Tuple contains the data for one contestant
        """
        conditions = []
        condition_values = []
        if name:
            conditions.append('Contestants.name LIKE ?')
            condition_values.append('%' + name + '%')
        if outcome:
            # TODO: update to handle multiple possible outcomes for ties
            outcomes = process_outcome_search(outcome)
            # can't search for exact match in case of ties (e.g. 13th/14th place)
            conditions.append('Outcomes.outcome=?')
            condition_values.append(outcomes[0])
        if season:
            int_season = None
            try:
                int_season = int(season)
            except ValueError:
                print('invalid season')
            if int_season:
                conditions.append('Contestants.season=?')
                condition_values.append(int_season)
        conditions = " AND ".join(conditions)
        condition_values = tuple(condition_values)
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        matching_contestants = cursor.execute(self.select_all_and_join + ' WHERE ' + conditions, condition_values).fetchall()
        conn.close()
        return matching_contestants


def process_outcome_search(searched_outcome: str) -> str:
    """
    Processes a provided parameter for outcome to match the format used in the database
    :param searched_outcome: user-provided value for `outcome` to search
    :return: processed list of strings for `outcome`, to match database format
    """
    # create list of possible outcomes that are in the database
    outcomes = ["Winner", "Runner-Up", "3rd"]
    for i in range(4, 16):
        outcomes.append(str(i) + "th")
    processed_outcomes = None
    try:
        # handle case where user searches plain number (e.g. '4')
        outcome_int = int(searched_outcome)
    except ValueError:
        try:
            # handle case where user searches ordinal number (e.g. '4th')
            outcome_int = outcomes.index(searched_outcome) + 1
        except ValueError:
            if searched_outcome == '1st':
                outcome_int = 1
            elif searched_outcome == '2nd':
                outcome_int = 2
            else:
                outcome_int = None
    if outcome_int and outcome_int < 16:
        processed_outcomes = [outcomes[outcome_int-1]]
        # add the possibilities for ties with the place before or after
        if outcome_int >= 4:
            processed_outcomes.append(outcomes[outcome_int-2] + "/" + outcomes[outcome_int-1])
        if 3 <= outcome_int <= 14:
            processed_outcomes.append(outcomes[outcome_int-1] + "/" + outcomes[outcome_int])
    return processed_outcomes
