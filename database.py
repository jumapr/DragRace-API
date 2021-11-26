import pandas as pd
import sqlite3
from typing import List, Tuple, Union
from input_validators import validate_integer_input, is_valid_date, process_outcome_search


class Database:
    def __init__(self):
        self.db_name = 'drag_race.db'
        self.contestant_df = pd.DataFrame(pd.read_csv('data/contestants.csv'))
        self.episode_df = pd.DataFrame(pd.read_csv('data/episodes.csv'))
        self.contestants_select_and_join = '''SELECT Contestants.name, Contestants.age, Hometowns.hometown, 
                        Outcomes.outcome, Contestants.season FROM Contestants JOIN Hometowns JOIN Outcomes 
                        ON (Contestants.hometown_id = Hometowns.id AND Contestants.outcome_id = Outcomes.id)'''
        self.episodes_select_and_join = '''SELECT Episodes.number, Episodes.title, Episodes.date, Contestants.name, 
                        Episodes.main_challenge, Episodes.season FROM Episodes 
                        LEFT JOIN Contestants ON Episodes.winner_id = Contestants.id'''

    def create_database(self):
        """
        Creates the Database table by creating the Hometown, Outcome, and Contestants tables in the proper order. Only needs
        to be run the first time the database is created.
        """
        self.create_hometown_table()
        self.create_outcome_table()
        self.create_contestant_table()
        self.create_episode_table()

    def create_hometown_table(self):
        """
        Creates Hometowns table in the database. Inserts unique hometowns from the Pandas DataFrame into the database.
        """
        # create hometown table
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Hometowns (
                        id INTEGER PRIMARY KEY,
                        hometown TEXT)
                        ''')
        # insert hometowns into table
        hometowns = self.contestant_df['hometown'].unique()
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
                        id INTEGER PRIMARY KEY,
                        outcome TEXT NOT NULL)
                        ''')
        # insert outcomes into table
        outcomes = self.contestant_df['outcome'].unique()
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
                       id INTEGER PRIMARY KEY,
                       name TEXT NOT NULL,
                       age INTEGER NOT NULL,
                       hometown_id INTEGER NOT NULL,
                       outcome_id INTEGER NOT NULL,
                       season INTEGER NOT NULL,
                       FOREIGN KEY (hometown_id) REFERENCES Hometowns (id),
                       FOREIGN KEY (outcome_id) REFERENCES Outcomes (id))
                       ''')
        # insert data from CSV into table
        for row in self.contestant_df.itertuples():
            # find hometown ID
            hometown_id = cursor.execute('SELECT id FROM Hometowns WHERE hometown=?', (row.hometown,)).fetchone()[0]
            # find outcome ID
            outcome_id = cursor.execute('SELECT id FROM Outcomes WHERE outcome=?', (row.outcome,)).fetchone()[0]
            cursor.execute('INSERT INTO Contestants (name, age, hometown_id, outcome_id, season) VALUES(?, ?, ?, ?, ?)',
                           (row.name, int(row.age), hometown_id, outcome_id, int(row.season))
                           )
        conn.commit()
        conn.close()

    def create_episode_table(self):
        """
        Gets data from episodes.csv and creates Episodes table in the database
        """
        # create table
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Episodes (
                       id INTEGER PRIMARY KEY,
                       number INTEGER NOT NULL,
                       title TEXT NOT NULL,
                       date TEXT NOT NULL,
                       winner_id INTEGER,
                       main_challenge TEXT,
                       season INTEGER NOT NULL,
                       FOREIGN KEY (winner_id) REFERENCES Contestants (id))
                       ''')
        # insert episodes into table
        for row in self.episode_df.itertuples():
            winner_id = cursor.execute('SELECT id FROM Contestants WHERE name=?', (row.winner,)).fetchone()
            if winner_id:
                winner_id = winner_id[0]
            main_challenge = None if row.main_challenge == 'None' else row.main_challenge
            cursor.execute('''INSERT INTO Episodes (number, title, date, winner_id, main_challenge, season) 
                           VALUES(?, ?, ?, ?, ?, ?)''',
                           (int(row.number), row.title, row.date, winner_id, main_challenge, int(row.season)))
        conn.commit()
        conn.close()

    def select_all(self, table: str) -> List[Tuple]:
        """
        Gets all items from a specified table in the database
        :param: table to get all items from
        :return: List with tuple for each item
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        if table == 'contestants':
            sql_query = self.contestants_select_and_join
        elif table == 'episodes':
            sql_query = self.episodes_select_and_join
        else:
            raise KeyError("No such table")
        all_items = cursor.execute(sql_query).fetchall()
        conn.close()
        return all_items

    def search_contestants(self, name: Union[str, None], outcome: Union[str, None], season: Union[str, None],
                           min_age: Union[str, None], max_age: Union[str, None]):
        """
        Searches for contestants matching specific criteria. One or more of the parameters may be None
        :param name: name of contestant, which may be partial
        :param outcome: outcome to search for (e.g. 4th for 4th place)
        :param season: season to search for; valid seasons are 1-13
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
        if conditions:
            conditions = " AND ".join(conditions)
            condition_values = tuple(condition_values)
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            matching_contestants = cursor.execute(self.contestants_select_and_join + ' WHERE ' + conditions,
                                                  condition_values).fetchall()
            conn.close()
        else:
            matching_contestants = None
        return matching_contestants

    def search_episodes(self, season: Union[str, None], after: Union[str, None], before: Union[str, None]):
        """
        Searches Episodes table for episodes matching search criteria
        :param season: season to search for; valid seasons are 1-13
        :param after: date to get episodes that aired after
        :param before: date to get episodes that aired before
        :return: List of Tuples, where each Tuple contains the data for one contestant
        """
        conditions = []
        condition_values = []
        if season:
            int_season = validate_integer_input(season)
            if int_season:
                conditions.append('Episodes.season=?')
                condition_values.append(int_season)
        if after and is_valid_date(after):
            conditions.append('Episodes.date > DATE(?)')
            condition_values.append(after)
        if before and is_valid_date(before):
            conditions.append('Episodes.date < DATE(?)')
            condition_values.append(before)
        if conditions:
            conditions = " AND ".join(conditions)
            condition_values = tuple(condition_values)
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            matching_episodes = cursor.execute(self.episodes_select_and_join + ' WHERE ' + conditions,
                                               condition_values).fetchall()
            conn.close()
        else:
            matching_episodes = None
        return matching_episodes
