API for querying data about the television program RuPaul's Drag Race.
The database contains each contestant's name, age, hometown, outcome, and season. More data may be added in future
revisions. The data in the contestants.csv data was gathered from Wikipedia. Data regarding All Stars and other franchises (e.g.
Drag Race UK) are not included at this time.
The API contains the route "/all", which will return the data for all contestants in JSON format and the route
"/search". The search route accepts the following parameters: name, outcome, and season. Outcome can be supplied as an
ordinal number or a plain number. The search does not yet include matches for outcome searches involving ties.

Example or returned JSON:
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
