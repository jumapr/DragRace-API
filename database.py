import pandas as pd
import sqlite3
from typing import List, Tuple

DB_NAME = 'drag_race.db'
# read data from CSV
data = pd.read_csv('data/contestants.csv')
df = pd.DataFrame(data)
SELECT_ALL_AND_JOIN = '''SELECT Contestants.name, Contestants.age, Hometowns.hometown, Outcomes.outcome,
                        Contestants.season FROM Contestants JOIN Hometowns JOIN Outcomes 
                        ON Contestants.hometown_id = Hometowns.id AND Contestants.outcome_id = Outcomes.id'''


def create_hometown_table():
    # create hometown table
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Hometowns (
                    id integer primary key,
                    hometown text)
                    ''')
    # insert hometowns into table
    hometowns = df['hometown'].unique()
    for hometown in hometowns:
        cursor.execute('INSERT INTO Hometowns (hometown) VALUES(?)', (hometown,))
    conn.commit()


def create_outcome_table():
    # create outcome table
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Outcomes (
                    id integer primary key,
                    outcome text)
                    ''')
    # insert outcomes into table
    outcomes = df['outcome'].unique()
    for outcome in outcomes:
        cursor.execute('INSERT INTO Outcomes (outcome) VALUES(?)', (outcome,))
    conn.commit()
    conn.close()


def create_contestant_table():
    """
    Loads data from contestant CSV into database
    """
    # create table
    conn = sqlite3.connect(DB_NAME)
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
    for row in df.itertuples():
        # find hometown ID
        hometown_id = cursor.execute('SELECT id FROM Hometowns WHERE hometown=?', (row.hometown, )).fetchone()[0]
        # find outcome ID
        outcome_id = cursor.execute('SELECT id FROM Outcomes WHERE outcome=?', (row.outcome, )).fetchone()[0]
        cursor.execute('INSERT INTO Contestants (name, age, hometown_id, outcome_id, season) VALUES(?, ?, ?, ?, ?)',
                       (row.name, int(row.age), hometown_id, outcome_id, int(row.season))
                       )
    conn.commit()
    conn.close()


def select_all() -> List[Tuple]:
    """
    Gets data from all contestants from the database
    :return: List with tuple for each contestant
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    all_contestants = cursor.execute(SELECT_ALL_AND_JOIN).fetchall()
    conn.close()
    return all_contestants


def search_contestants(name: str, outcome: str, season: int) -> List[Tuple]:
    """
    Searches for contestants matching specific criteria
    :param name: name of contestant, which may be partial
    :param outcome:
    :param season:
    :return:
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    matching_contestants = None
    if name:
        matching_contestants = cursor.execute(SELECT_ALL_AND_JOIN + ' WHERE Contestants.name LIKE ?',
                                              ('%' + name + '%',)).fetchall()
        return matching_contestants
    elif outcome:
        try:
            # if a number is searched (e.g. 5)
            int(outcome)
        except ValueError:
            try:
                # if a ordinal number is searched (e.g. 5th)
                int(outcome[:-2])
            except ValueError:
                pass
    conn.close()
    return matching_contestants


# create_hometown_table()
# create_outcome_table()
# create_contestant_table()
print(search_contestants('Jinkx', '', 0))
