import requests
import bs4
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import numpy as np
import csv
from collections import OrderedDict
import global_variables


URL_NHL_CZ = ['http://nhl.cz/sezona/player-stats/detailni?stats-menu-section=info&stats-filter-season=',
              '&stats-filter-competition=', '&stats-view-pager-page=']
QUANTITY = dict(poradi=0, jmeno=1, tym=2, P=3, Z=4, G=5, A=6, B=7, pm=8, p=9, m=10, TM=11)


def save_csv_into_dictionary(csv_file):
    """ Open given csv file in format 'season; page id' and save it into ordered dictionary. """

    dictionary = OrderedDict()
    with open(csv_file, newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            dictionary[row[0]] = row[1]
    return dictionary


def load_stats_table(url):
    """ From given url load and parse html table that contains player statistics. """

    req = requests.get(url)
    soup_page = BeautifulSoup(req.text, 'html.parser')
    stats_table = soup_page.table
    global_variables.page_number += 1
    return stats_table


def get_player_stats(table_with_players):
    """ Generator yielding statistics of players from one page, one player by one. """

    for element in table_with_players.tbody:
        if isinstance(element, bs4.element.Tag):
            one_player_stats = element.find_all('td')
            yield one_player_stats
    yield 'generator empty'


def get_base_url_for_each_season():
    """  Return dictionary of base url's for each season in format 'season: url'. This url serves as base for iterating
    through stat pages for given season. """

    seasons_with_page_ids = save_csv_into_dictionary('nhl_cz_page_id_for_each_season.csv')
    url_per_season = OrderedDict()

    for season, page_id in seasons_with_page_ids.items():
        url = URL_NHL_CZ[0] + season[:4] + URL_NHL_CZ[1] + page_id + URL_NHL_CZ[2]
        url_per_season[season] = url

    return url_per_season


def increase_dict_values_for_low_enough_keys(threshold, dictionary):
    """ Increase dictionary values if corresponding keys are lower than threshold
    F.e. with threshold=100 dictionary {125:0, 100:6, 75:15} updates into {125:0, 100:7, 75:16} """

    dictionary = dictionary.update((x, y+1) for x, y in dictionary.items() if threshold >= x)
    return dictionary


def get_players_with_points_per_season(*required_points):
    url_per_season = get_base_url_for_each_season()
    players_with_points_per_season = OrderedDict()

    # iteration through seasons
    for season, base_url in url_per_season.items():
        global_variables.page_number = 1

        required_points = sorted(required_points, reverse=True)
        players_with_required_points = OrderedDict((x, 0) for x in required_points)

        all_stats_from_season_acquired = False

        # iterate through pages with player stats per season (until player with less than required points is found)
        while not all_stats_from_season_acquired:
            # load one page from the season and return generator with players from given page
            url = base_url + str(global_variables.page_number)
            table = load_stats_table(url)
            players_stats_generator = get_player_stats(table)

            # iterate through players on given page
            while True:
                player = next(players_stats_generator)

                if player != 'generator empty':
                    player_points = int(player[QUANTITY['B']].text)
                    if player_points >= required_points[-1]:
                        increase_dict_values_for_low_enough_keys(player_points, players_with_required_points)
                    else:
                        players_with_points_per_season[season] = list(players_with_required_points.values())
                        players_per_season = ' '.join(str(required_points[x]) + ':' + str(y)
                                                      for x, y in enumerate(players_with_points_per_season[season]))
                        print(season + ': ' + players_per_season)
                        all_stats_from_season_acquired = True
                        break
                else:
                    break

    # reverse order of seasons in the dictionary, so it goes chronologically
    players_with_points_per_season = OrderedDict(reversed(list(players_with_points_per_season.items())))
    return players_with_points_per_season


def scatter_plot_players(dict_of_players):
    """ Plot number of players who reached given amount of points per season. """
    seasons = [x[2:4] for x in dict_of_players.keys()]
    plt.plot(seasons, dict_of_players.values())
    plt.show()


def main():
    players_per_season_dictionary = get_players_with_points_per_season(125, 100, 85, 70)
    print(players_per_season_dictionary)
    scatter_plot_players(players_per_season_dictionary)


if __name__ == '__main__':
    main()

