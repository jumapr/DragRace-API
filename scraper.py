import requests
from bs4 import BeautifulSoup

episode_file = 'data/episodes1.csv'
season_file = 'data/seasons.csv'
file_headers = {'episodes': 'number,title,date,winner,main_challenge,season',
                'contestants': 'name,age,hometown,outcome,season',
                'seasons': 'number,winner'}


class Franchise:
    def __init__(self, name: str, num_seasons: int, base_url: str):
        self.name = name
        self.num_seasons = num_seasons
        self.base_url = base_url

    def get_season_data(self):
        with open(episode_file, 'w') as ef:
            # write header row
            ef.write(file_headers['episodes'] + '\n')
        with open(season_file, 'w') as sf:
            # write header row
            sf.write(file_headers['seasons'] + '\n')
        for i in range(1, self.num_seasons + 1):
            season = Season(self.base_url.format(i), i)
            season.write_episode_data()


class Season:
    def __init__(self, url: str, season_num: int):
        self.season_num = season_num
        self.url = url
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        episode_table = soup.find('table', class_='wikitable plainrowheaders wikiepisodetable')
        self.basic_info_rows = episode_table.find_all('tr', 'vevent')
        self.detailed_info_rows = episode_table.find_all('tr', class_='expand-child')
        self.winner = self.get_season_winner()
        self.episodes = self.get_episode_data()

    def get_episode_data(self) -> list:
        episode_list = []
        for basic_info_row, detailed_info_row in zip(self.basic_info_rows, self.detailed_info_rows):
            episode_list.append(Episode(basic_info_row, detailed_info_row))
        return episode_list

    def write_episode_data(self):
        with open(episode_file, 'a') as fh:
            for episode in self.episodes:
                line = ",".join([str(episode.number), episode.title, episode.date, episode.winner,
                                 episode.main_challenge, str(self.season_num)]) + '\n'
                fh.write(line)

    def get_season_winner(self):
        """
        Gets season winner from episodes table and writes to file
        :return: season winner
        """
        # TODO: test
        for detailed_info_row in self.detailed_info_rows:
            episode_bullets = detailed_info_row.find_all('li')
            for bullet in episode_bullets:
                if "Winner of RuPaul's Drag Race Season" in bullet.text:
                    season_winner = get_string_after_colon(bullet.text)
                    with open(season_file, 'a') as fh:
                        line = str(self.season_num) + ',' + season_winner + '\n'
                        fh.write(line)
                    return season_winner


class Episode:
    def __init__(self, basic_info_row, detailed_info_row):
        """
        Does scraping and processing to get episode information
        :param basic_info_row: bs4 Tag object representing a table row
        :param detailed_info_row: bs4 Tag object representing a table row
        """
        cells = basic_info_row.find_all('td')
        self.number = cells[0].text.rstrip()
        self.title = cells[1].text.rstrip()
        date_raw = cells[2].text.rstrip()
        start = date_raw.find('(')
        self.date = date_raw[start + 1:start + 11]
        assert(len(self.date) == 10)
        print(self.number, self.title, self.date)
        challenge_winner = detailed_info_row.find(style='color:royalblue')
        if challenge_winner:
            self.winner = get_string_after_colon(challenge_winner.text)
        else:
            self.winner = 'None'
        self.main_challenge = 'None'
        episode_bullets = detailed_info_row.find_all('li')
        for bullet in episode_bullets:
            # Wikipedia pages for Seasons 7, 8, and 8 call it the Maxi Challenge instead of the Main Challenge
            if ('Main Challenge:' in bullet.text) or ('Maxi Challenge:' in bullet.text):
                # add double quotes around challenge description, since it may contain commas
                self.main_challenge = '"' + get_string_after_colon(bullet.text) + '"'
        print(self.winner, self.main_challenge)


def get_contestant_data():
    """
    Scrapes the contestant data from wikipedia
    """
    # get contestant table from Wikipedia
    file_name = 'data/constestants2.csv'
    contestants_url = "https://en.wikipedia.org/wiki/List_of_RuPaul%27s_Drag_Race_contestants"
    response = requests.get(contestants_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    contestant_table = soup.find('tbody')

    with open(file_name, mode='w') as fh:
        # write header row
        fh.write(file_headers['contestants'] + '\n')
        # get contestant data
        current_season = 'Season 1'
        for table_row in contestant_table.find_all('tr'):
            row_data = table_row.find_all('td')
            # skip header row
            if not row_data:
                continue
            contestant_info = []
            for cell_data in row_data:
                cell_text = cell_data.text.rstrip()
                if 'Season' in cell_data.text:
                    current_season = cell_text
                else:
                    # remove footnotes in brackets
                    bracket_position = cell_text.find('[')
                    if bracket_position != -1:
                        cell_text = cell_text[:bracket_position]
                    contestant_info.append(cell_text)
            contestant_info.append(current_season)
            print(contestant_info)
            fh.write(",".join(contestant_info) + '\n')


def get_string_after_colon(string: str) -> str:
    """
    Removes the portion of the string before the colon, including the colon and whitespace after. Also removes double
    quotes from within string
    :param string: string to process
    :return: processed string
    """
    colon_pos = string.find(':')
    # remove double quotes from within string
    processed_string = string.replace('"', '')
    return processed_string[colon_pos + 1:].strip()


if __name__ == '__main__':
    drag_race_franchise = Franchise("RuPaul's Drag Race", 13,
                                    'https://en.wikipedia.org/wiki/RuPaul%27s_Drag_Race_(season_{})')
    drag_race_franchise.get_season_data()
