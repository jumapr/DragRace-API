import pandas as pd
import sqlite3
from typing import List, Tuple, Union
from input_validators import validate_integer_input, is_valid_date, process_outcome_search, add_wildcards
from collections import namedtuple


SearchParamInfo = namedtuple('SearchParamInfo', ['searched_val', 'condition', 'validator'])


class Database:
    def __init__(self):
        self.db_name = 'drag_race.db'
        self.contestant_df = pd.DataFrame(pd.read_csv('data/contestants.csv'))
        self.episode_df = pd.DataFrame(pd.read_csv('data/episodes.csv'))
        self.select_and_join = {'contestants': '''SELECT Contestants.name, Contestants.age, Hometowns.hometown, 
                                Outcomes.outcome, Contestants.season FROM Contestants JOIN Hometowns JOIN Outcomes 
                                ON (Contestants.hometown_id = Hometowns.id AND Contestants.outcome_id = Outcomes.id)''',
                                'episodes': '''SELECT Episodes.number, Episodes.title, Episodes.date, Contestants.name, 
                                Episodes.main_challenge, Episodes.season FROM Episodes 
                                LEFT JOIN Contestants ON Episodes.winner_id = Contestants.id'''}

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
            sql_query = self.select_and_join['contestants']
        elif table == 'episodes':
            sql_query = self.select_and_join['episodes']
        else:
            raise KeyError("No such table")
        all_items = cursor.execute(sql_query).fetchall()
        conn.close()
        return all_items

    def search_contestants(self, name: Union[str, None], outcome: Union[str, None], season: Union[str, None],
                           min_age: Union[str, None], max_age: Union[str, None]):
        """
        Searches for contestants matching specific criteria.
        :param name: name of contestant, which may be partial
        :param outcome: outcome to search for (e.g. 4th for 4th place)
        :param season: season to search for; valid seasons are 1-13
        :param min_age: minimum age of contestants to search for
        :param max_age: maximum age of contestants to search for
        :return: List of Tuples, where each Tuple contains the data for one contestant or None if there were no valid
        search parameters
        """
        name_info = SearchParamInfo(searched_val=name, condition='Contestants.name LIKE ?', validator=add_wildcards)
        outcome_info = SearchParamInfo(searched_val=outcome,
                                       condition='(Outcomes.outcome LIKE ? OR Outcomes.outcome LIKE ?)',
                                       validator=process_outcome_search)
        min_age_info = SearchParamInfo(searched_val=min_age, condition='Contestants.age >=?',
                                       validator=validate_integer_input)
        max_age_info = SearchParamInfo(searched_val=max_age, condition='Contestants.age <=?',
                                       validator=process_outcome_search)
        season_info = SearchParamInfo(searched_val=season, condition='Contestants.season=?', validator=None)
        matching_contestants = self.generic_search('contestants', name_info, outcome_info, min_age_info, max_age_info,
                                                   season_info)
        return matching_contestants

    def search_episodes(self, season: Union[str, None], after: Union[str, None], before: Union[str, None]):
        """
        Searches Episodes table for episodes matching search criteria
        :param season: season to search for; valid seasons are 1-13
        :param after: date to get episodes that aired after
        :param before: date to get episodes that aired before
        :return: List of Tuples, where each Tuple contains the data for one contestant or None if there were no valid
        search parameters
        """
        season_info = SearchParamInfo(searched_val=season, condition='Episodes.season=?', validator=None)
        min_date_info = SearchParamInfo(searched_val=after, condition='Episodes.date > DATE(?)', validator=is_valid_date)
        max_date_info = SearchParamInfo(searched_val=before, condition='Episodes.date < DATE(?)', validator=is_valid_date)
        matching_episodes = self.generic_search('episodes', season_info, min_date_info, max_date_info)
        return matching_episodes

    def generic_search(self, table: str, *args: SearchParamInfo):
        """
        Does input validation & processing, builds the SQL query, queries the database, and returns the result
        :param table: database table - contestants or episodes
        :param args: a SearchParamInfo named tuple for each search parameter
        :return: list of tuples containing search results or None if there were no valid search parameters
        """
        all_conditions = []
        all_condition_vals = []
        for arg in args:
            if arg.searched_val:
                # step 1 - do input validation
                processed_val = arg.searched_val
                if arg.validator:
                    processed_val = arg.validator(arg.searched_val)
                    if not processed_val:
                        continue
                # step 2 - append condition and condition value
                all_conditions.append(arg.condition)
                # have to handle special case for outcome to include ties
                if arg.validator == process_outcome_search:
                    all_condition_vals.append(processed_val + '%')
                    all_condition_vals.append('%' + '/' + processed_val)
                else:
                    all_condition_vals.append(processed_val)
        # step 3 - form SQL query and execute
        if all_conditions:
            conditions = " AND ".join(all_conditions)
            condition_values = tuple(all_condition_vals)
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            matching = cursor.execute(self.select_and_join[table] + ' WHERE ' + conditions, condition_values).fetchall()
            conn.close()
        else:
            matching = None
        return matching
