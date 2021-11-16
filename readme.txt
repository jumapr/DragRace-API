API for querying data about the television program RuPaul's Drag Race.
Uses Flask web framework, sqlite3 for SQL, and pandas for reading/handling CSV data.
The database contains each contestant's name, age, hometown, outcome, and season. More data may be added in future revisions.
The data in contestants.csv was scraped from Wikipedia (https://en.wikipedia.org/wiki/List_of_RuPaul%27s_Drag_Race_contestants) using Beautiful Soup. Data regarding All Stars and other franchises (e.g. Drag Race UK) are not included at this time. The data in episodes.csv was also scraped from Wikipedia but is not yet included in the database or API.

The API contains the route "/all", which will return the data for all contestants in JSON format and the route
"/search". The search route accepts the following parameters: name, outcome, season, minage, and maxage.
Outcome can be supplied as an ordinal number or a cardinal number.

Example of returned JSON:
{
  "contestants": [
    {
      "age": 26,
      "hometown": "Las Vegas, Nevada",
      "name": "Shannel",
      "outcome": "4th",
      "season": 1
    },
    {
      "age": 21,
      "hometown": "Falls Church, Virginia",
      "name": "Tatianna",
      "outcome": "4th",
      "season": 2
    },
  ]
}
