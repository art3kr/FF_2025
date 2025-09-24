from bs4 import BeautifulSoup, Comment
import pandas as pd
import requests
from functools import reduce
import pickle
import glob
import os
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# To do
# include Bye weeks from schedule?
# New source for weekly salaries to scrape (FantasyPros?)


'''schemas'''
player_table_SCHEMA = [
'name',
'team',
'position',
'fpoints_ppr',
'games',
'player_url',
# 'fpoints_half_per_game'
]

player_weekly_fantasy_SCHEMA = [
'name',
'team',
'opponent',
'date',
'year',
'week',
'position',
'fpoints_ppr'
]

kicker_table_SCHEMA = [
'name',
'team',
'position',
'player_url',
]

kicker_weekly_fantasy_SCHEMA = [
'name',
'team',
'year',
'week',
'position',
'xpa',
'xpm',
'fga',
'fgm',
'fg_distances',
'fpoints'
]

schedule_SCHEMA = [
    'year',
    'week',
    'team_1',
    'team_2',
    'date',
    'time',
    'location',
    'boxscore_url',
]

def find_start_index(year, week):
    '''find the starting index from the max memoized file in /player_data'''

    path = os.getcwd() + f'/data/player_data/{year}/week{week}'
    file_list = glob.glob(path+'/*')
    
    if len(file_list) == 0:
        return 0
    index_list = [int(i.split('_')[-1]) for i in file_list]
    return max(index_list)

def saveList(data, filename):
    open_file = open(filename, 'wb')
    pickle.dump(data, open_file)
    open_file.close()

def loadList(file):
    open_file = open(file, "rb")
    loaded_list = pickle.load(open_file)
    open_file.close()
    return loaded_list

def get_all_players_table(year):
	'''function to get the table of all players fantasy points, games played, etc. from pro football reference

	input: year [int]
	output: pandas dataframe
	'''

	'''send request, get html table of players'''
	base_url = f'https://www.pro-football-reference.com/years/{year}/fantasy.htm'
	r = requests.get(base_url, verify=False)
	soup = BeautifulSoup(r.content, 'html.parser')
	players_table_html = soup.find_all('table')[0]

	'''create lists'''
	names = []
	player_urls = []
	teams = []
	positions = []
	fpoints_ppr = []
	games = []

	'''iterate through html table of players'''
	for index, row in enumerate(players_table_html.find_all('tr')[2:]):

		try:
			'''get name, team, player url, position, fpoints and games played'''
			dat = row.find('td', attrs={'data-stat': 'player'})
			name = dat.a.get_text()
			player_url = dat.a.get('href')
			team = row.find('td', attrs={'data-stat': 'team'}).get_text()
			# team = row.find('td', attrs={'data-stat': 'team'}).a.get('title')
			position = row.find('td', attrs={'data-stat': 'fantasy_pos'}).get_text()
			fpoint_ppr = float(row.find('td', attrs={'data-stat': 'draftkings_points'}).get_text())
			game = int(row.find('td', attrs={'data-stat': 'g'}).get_text())


			'''append to lists'''
			names.append(name)
			player_urls.append(player_url)
			teams.append(team)
			positions.append(position)
			fpoints_ppr.append(fpoint_ppr)
			games.append(game)


		except: 
			pass

	'''create dataframe from lists'''
	players_df = pd.DataFrame(
		list(zip(names,teams,positions,fpoints_ppr,games,player_urls)),
		columns=player_table_SCHEMA)

	'''creating points per game stat'''
	players_df['fpoints_ppr_per_game'] = players_df['fpoints_ppr'] / players_df['games']

	return players_df


def get_points_for_each_player(year, current_week):
    '''function to get the fantasy points for each player for all weeks from pro-football-reference

	input: year [int], week [int]
	output: None
	'''

    '''load all players df from csv'''
    players_df = pd.read_csv(f'data/player_data/{year}/{year}_players_df.csv')

    '''send request, get html table of players'''
    base_url = 'https://www.pro-football-reference.com'

    players_list = players_df['name'].tolist()
    player_urls_list = players_df['player_url'].tolist()

    '''create list for f points'''
    names = []
    teams = []
    opponents = []
    dates = []
    years = []
    weeks = []
    positions = []
    fpoints_ppr = []

    # get start index from memoized files (if this script has already been run, otherwise index is 0)
    start_index = find_start_index(year, current_week)
    start_time = time.time()

	
    '''iterate through all players in the players_df'''
    for i in range(start_index,len(players_list)):

        '''create lists for each players'''
        teams_player = []
        opponents_player = []
        dates_player = []
        years_player = []
        games = []
        positions_player = []
        fpoints_player_ppr = []

        player = players_list[i]
        url = base_url + player_urls_list[i][:-4] + '/fantasy/2024/'

        print(player, url, i)

        # if i % 20 == 0 or i == start_index:
        #     s = requests.Session()

        r = requests.get(url,
                         verify=False,
                    # headers = {'User-agent': 'Weekly Fantasy Bot'}
                    )
        print(r)
        print(r.headers)
        soup = BeautifulSoup(r.content, 'html.parser')
        player_name = soup.find('h1').get_text()
        print(player_name)

        try:

            player_fantasy_table_html = soup.find('table', id="player_fantasy").find('tbody')
            # print(player_fantasy_table_html)

            '''iterate through html table of fantasy stats for player'''
            for index, row in enumerate(player_fantasy_table_html.find_all('tr')):

                try:
                    
                    team = row.find('td', attrs={'data-stat': 'team'}).get_text()
                    opponent = row.find('td', attrs={'data-stat': 'opp'}).get_text()
                    date = row.find('td', attrs={'data-stat': 'game_date'}).get_text()
                    game = int(row.find('td', attrs={'data-stat': 'game_num'}).get_text())
                    position = row.find('td', attrs={'data-stat': 'starter_pos'}).get_text()
                    fpoint_ppr = float(row.find('td', attrs={'data-stat': 'draftkings_points'}).get_text())

                    teams_player.append(team)
                    opponents_player.append(opponent)
                    dates_player.append(date)
                    games.append(game)
                    positions_player.append(position)
                    fpoints_player_ppr.append(fpoint_ppr)
                    years_player.append(year)
                except:
                    pass

            # print(games)
            # print(positions_player)
            # print(fpoints_player_ppr)

            '''append attributes to list'''
            names.append([player_name]*len(games))
            teams.append(teams_player)
            opponents.append(opponents_player)
            dates.append(dates_player)
            weeks.append(games)
            positions.append(positions_player)
            fpoints_ppr.append(fpoints_player_ppr)
            years.append(years_player)

        except:

            '''save list as pickle'''
            end_index = i
            saveList([names, teams, opponents, dates, years, weeks, positions, fpoints_ppr], f'data/player_data/{year}/week{current_week}/week{current_week}_player_data_{end_index}')

        time.sleep(4)
        num_requests = start_index - i
        elapsed_time = abs(time.time() - start_time/60)
        requests_per_min = num_requests/elapsed_time #This yields small negative number, need to fix
        # while requests_per_min > 20:
        #     print(requests_per_min)
        #     time.sleep(5)
        #     elapsed_time = (time.time() - start_time)/60
        #     requests_per_min = num_requests/elapsed_time  

        if i % 20 == 0:
            end_index = i+1
            saveList([names, teams, opponents, dates, years, weeks, positions, fpoints_ppr], f'data/player_data/{year}/week{current_week}/week{current_week}_player_data_{end_index}')

        # if i == start_index + 4:
        #     break #debug
        

    '''save list as pickle'''
    end_index = i + 1
    saveList([names, teams, opponents, dates, years, weeks, positions, fpoints_ppr], f'data/player_data/{year}/week{current_week}/week{current_week}_player_data_{end_index}')

    return

def combine_pickles(year, week):

    '''function to get the combine all the pickles from our scrape

	input: year [int], week [int]
	output: pandas dataframe
	'''
    path = os.getcwd()
    file_list = glob.glob(path+f'/data/player_data/{year}/week{week}/*')
    file_list = [file for file in file_list if not file.endswith(".csv")]
    file_list = [os.path.basename(i) for i in file_list]
    file_list = sorted(file_list, key=lambda x: int(x.split('_')[-1])) #sort list

    names = []
    teams = []
    opponents = []
    dates = []
    years = []
    weeks = []
    positions = []
    fpoints_ppr = []

    for file in file_list:
        current_pickle = loadList(f'data/player_data/{year}/week{week}/{file}')
        names += current_pickle[0]
        teams += current_pickle[1]
        opponents += current_pickle[2]
        dates += current_pickle[3]
        years += current_pickle[4]
        weeks += current_pickle[5]
        positions += current_pickle[6]
        fpoints_ppr += current_pickle[7]
        # print(fpoints_ppr)

    '''Flatten lists'''
    names = reduce(lambda x,y: x+y, names)
    teams = reduce(lambda x,y: x+y, teams)
    opponents = reduce(lambda x,y: x+y, opponents)
    dates = reduce(lambda x,y: x+y, dates)
    years = reduce(lambda x,y: x+y, years)
    weeks = reduce(lambda x,y: x+y, weeks)
    positions = reduce(lambda x,y: x+y, positions)
    fpoints_ppr = reduce(lambda x,y: x+y, fpoints_ppr)

    '''remove linebreak character from names'''
    names = map(lambda s: s.strip(), names)

    '''create dataframe from lists'''
    players_weekly_points_df = pd.DataFrame(
    list(zip(names,teams,opponents,dates,years,weeks,positions,fpoints_ppr)),
    columns=player_weekly_fantasy_SCHEMA)

    # '''remove duplicates'''
    players_weekly_points_df = players_weekly_points_df.drop_duplicates(subset=['name','team','opponent','date','year','week','position','fpoints_ppr'])

    return players_weekly_points_df

def get_defenses_scoring_table(year, week):
    '''function to get defensive scoring from FantasyPros for each week

    input: week [int]
    output: pandas dataframe'''

    base_url = "https://www.fantasypros.com/nfl/stats/dst.php?range=week&week="

    r = requests.get(base_url+str(week), verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')
    defenses_table_html = soup.find_all('table')[0]
    # print(defenses_table_html)

    '''create lists'''
    names = []
    teams = []
    opponents = []
    dates = []
    weeks = []
    positions = []
    fpoints_ppr = []
    years = []

    for index, row in enumerate(defenses_table_html.find_all('tr')):
        '''skip thead'''
        if index == 0:
            continue

        tds = row.findChildren('td')
        name = tds[1].get_text()
        team = name[-4:-1].replace("(","")
        opponent = ''
        date = ''
        name = name[:-6]
        week = str(week)
        position = 'DST'
        fpoint_ppr = tds[-2].get_text()

        '''append attributes to list'''
        names.append(name)
        teams.append(team)
        opponents.append(opponent)
        dates.append(date)
        years.append(year)
        weeks.append(week)
        positions.append(position)
        fpoints_ppr.append(fpoint_ppr)
    
    '''create dataframe from lists'''
    defenses_df = pd.DataFrame(
        list(zip(names,teams,opponents, dates, years, weeks, positions, fpoints_ppr)),
        columns=player_weekly_fantasy_SCHEMA)
    
    return defenses_df

    
def get_all_kickers_table(year):
    '''function to get the table of all kickers, games played, etc. from pro football reference

	input: year [int]
	output: pandas dataframe
	'''

    '''send request, get html table of kickers'''
    base_url = f'https://www.pro-football-reference.com/years/{year}/kicking.htm'
    r = requests.get(base_url, verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')
    kickers_table_html = soup.find_all('table')[0]

    '''create lists'''
    names = []
    kicker_urls = []
    teams = []
    positions = []

    '''iterate through html table of players'''
    for index, row in enumerate(kickers_table_html.find_all('tr')[2:]):

        try:
            '''get name, team, player url, position, fpoints and games played'''
            dat = row.find('td', attrs={'data-stat': 'player'})
            name = dat.a.get_text()
            kicker_url = dat.a.get('href')
            team = row.find('td', attrs={'data-stat': 'team'}).a.get('title')
            position = row.find('td', attrs={'data-stat': 'pos'}).get_text()


            '''append to lists'''
            names.append(name)
            kicker_urls.append(kicker_url)
            teams.append(team)
            positions.append(position)


        except: 
            pass

    '''create dataframe from lists'''
    kickers_df = pd.DataFrame(
        list(zip(names,teams,positions,kicker_urls)),
        columns=kicker_table_SCHEMA)
    
    return kickers_df


def get_all_games_played_table(year=2025):
     
    '''function to get the table of all games scheduled from pro football reference

	input: year [int]
	output: pandas dataframe
	'''

    '''send request, get html table of game schedule'''
    base_url = f'https://www.pro-football-reference.com/years/{str(year)}/games.htm'
    r = requests.get(base_url, verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')
    schedule_table_html = soup.find_all('table')[0]

    '''create lists'''
    years = []
    weeks = []
    team_1s = []
    team_2s = []
    dates = []
    times = []
    locations = []
    boxscore_urls = []

    '''iterate through html table of games'''
    for index, row in enumerate(schedule_table_html.find_all('tr')[1:]):

        try: 
            '''get teams and weeks'''
            week = int(row.find('th', attrs={'data-stat': 'week_num'}).get_text())
            team_1 = row.find('td', attrs={'data-stat': 'winner'}).get_text()
            team_2 = row.find('td', attrs={'data-stat': 'loser'}).get_text()
            date = row.find('td', attrs={'data-stat': 'game_date'}).get_text()
            time = row.find('td', attrs={'data-stat': 'gametime'}).get_text()
            location = row.find('td', attrs={'data-stat': 'game_location'}).get_text()
            boxscore_element = row.find('td', attrs={'data-stat': 'boxscore_word'})
            boxscore_url = boxscore_element.a.get('href')

            '''location is not just @, but the city'''
            if location == "@":
                location = team_2[:team_2.rindex(" ")]
            else:
                location = team_1[:team_1.rindex(" ")]

            '''append to lists'''
            years.append(year)
            weeks.append(week)
            team_1s.append(team_1)
            team_2s.append(team_2)
            dates.append(date)
            times.append(time)
            locations.append(location)
            boxscore_urls.append(boxscore_url)

        except:
            pass

    '''create dataframe from lists'''
    schedule_df = pd.DataFrame(
        list(zip(years,weeks,team_1s,team_2s,dates,times,locations,boxscore_urls)),
        columns=schedule_SCHEMA)

    return schedule_df

def get_kicking_scoring_data_from_boxscores(year, first_week=1, last_week=18):
     
    '''function to get the kicking scoring data for each kicker for all weeks from pro-football-reference

	input: year [int], week [int]
	output: None
	'''

    '''load schedule df from csv'''
    schedule = pd.read_csv(f'data/schedules/{year}_schedule_df.csv')
    schedule = schedule[(schedule['week'] >= first_week) & (schedule['week'] <= last_week)]
    
    '''send request, get html table of players'''
    base_url = 'https://www.pro-football-reference.com'

    games_urls_list = schedule['boxscore_url'].tolist()
    weeks_list = schedule['week'].tolist()

    '''create lists'''
    players = []
    teams = []
    years = []
    weeks = []
    positions = []
    xpas = []
    xpms = []
    fgas = []
    fgms = []
    fg_distances = []


    '''iterate through all games in the schedule_df'''
    for i in range(len(schedule)):

        week = weeks_list[i]
        print(week)

        '''get html soup'''
        r = requests.get(base_url + games_urls_list[i], verify=False)
        soup = BeautifulSoup(r.content, 'lxml')
        soup2 = BeautifulSoup("\n".join(soup.find_all(string=Comment)), "lxml")

        '''get kicking table'''
        kicking_table = soup2.find('table', id="kicking").find('tbody')

        '''create lists for each game'''
        game_players = []
        game_teams = []
        game_years = []
        game_weeks = []
        game_position = []
        game_xpas = []
        game_xpms = []
        game_fgas = []
        game_fgms = []
        game_fg_distances_dict = {}

        '''1. Start with kicking table: iterate through html table of kicking stats for each game'''
        for index, row in enumerate(kicking_table.find_all('tr')):
            xpa_elem = row.find('td', attrs={'data-stat': 'xpa'})
            fga_elem = row.find('td', attrs={'data-stat': 'fga'})

            '''if there is a kicker'''
            if (xpa_elem is not None and xpa_elem.get_text() != "") or (fga_elem is not None and fga_elem.get_text() != ""): 
                name = row.find('th', attrs={'data-stat': 'player'}).get_text()
                team = row.find('td', attrs={'data-stat': 'team'}).get_text()
                position = 'K'
                xpm = row.find('td', attrs={'data-stat': 'xpm'}).get_text()
                xpa = xpa_elem.get_text()
                fgm = row.find('td', attrs={'data-stat': 'fgm'}).get_text()
                fga = row.find('td', attrs={'data-stat': 'fga'}).get_text()

                print(name) #debug 

                '''append attributes to list'''
                game_players.append(name)
                game_teams.append(team)
                game_weeks.append(week)
                game_position.append(position)
                game_xpas.append(xpa)
                game_xpms.append(xpm)
                game_fgas.append(fga)
                game_fgms.append(fgm)
                game_years.append(year)
        
        '''get scoring table'''
        scoring_table = soup.find('table', id="scoring").find('tbody')

        '''2. Go through scoring table: iterate through html table of scoring stats for each game to find made fg distances'''
        for index, row in enumerate(scoring_table.find_all('tr')):
            description = row.find('td', attrs={'data-stat': 'description'}).get_text()  

            '''get fg distances'''
            if "field goal" in description and "blocked" not in description and "return" not in description: 
                test = description[:description.rindex("yard")].strip()
                fg_distance = test[test.rindex(" "):].strip()
                kicker_name = test[:test.rindex(" ")].strip()

                if kicker_name not in game_fg_distances_dict.keys():
                    game_fg_distances_dict[kicker_name] = []
                game_fg_distances_dict[kicker_name].append(fg_distance)
        
        
        '''dealing with fg distances dict to list'''
        game_fg_distances_list = [0] * len(game_players)
        for player in game_fg_distances_dict.keys():
            list_index = game_players.index(player)
            game_fg_distances_list[list_index] = game_fg_distances_dict[player]

        '''append lists to lists'''
        players.append(game_players)
        teams.append(game_teams)
        weeks.append(game_weeks)
        positions.append(game_position)
        xpas.append(game_xpas)
        xpms.append(game_xpms)
        fgas.append(game_fgas)
        fgms.append(game_fgms)
        fg_distances.append(game_fg_distances_list)
        years.append(game_years)

        if i % 5 == 0:
            end_index = i+1
            saveList([players, teams, years, weeks, positions, xpas, xpms, fgas, fgms, fg_distances], f'data/kicker_data/{year}/week{week}_kicker/week{week}_kicker_data_{end_index}')
        
        time.sleep(2)
        
    '''save list as pickle'''
    end_index = i + 1
    saveList([players, teams, years, weeks, positions, xpas, xpms, fgas, fgms, fg_distances], f'data/kicker_data/{year}/week{week}_kicker/week{week}_kicker_data_{end_index}')

    return    
     
def combine_pickles_kickers(year, week):

    '''function to get the combine all the pickles for kickers from our scrape

	input: year [int], week [int]
	output: pandas dataframe
	'''
    path = os.getcwd()
    file_list = glob.glob(path+f'/data/kicker_data/{year}/week{week}_kicker/*')
    file_list = [file for file in file_list if not file.endswith(".csv")]
    file_list = [os.path.basename(i) for i in file_list]
    file_list = sorted(file_list, key=lambda x: int(x.split('_')[-1])) #sort list


    '''condition if there are not files (like no week 18 in years 2010-2020)'''
    if not file_list:
        return

    names = []
    teams = []
    years = []
    weeks = []
    positions = []
    xpas = []
    xpms = []
    fgas = []
    fgms = []
    fg_distances = []


    for file in file_list:
        current_pickle = loadList(f'data/kicker_data/{year}/week{week}_kicker/{file}')
        names += current_pickle[0]
        teams += current_pickle[1]
        years += current_pickle[2]
        weeks += current_pickle[3]
        positions += current_pickle[4]
        xpas += current_pickle[5]
        xpms += current_pickle[6]
        fgas += current_pickle[7]
        fgms += current_pickle[8]
        fg_distances += current_pickle[9]

    '''Flatten lists'''
    names = reduce(lambda x,y: x+y, names)
    teams = reduce(lambda x,y: x+y, teams)
    years = reduce(lambda x,y: x+y, years)
    weeks = reduce(lambda x,y: x+y, weeks)
    positions = reduce(lambda x,y: x+y, positions)
    xpas = reduce(lambda x,y: x+y, xpas)
    xpms = reduce(lambda x,y: x+y, xpms)
    fgas = reduce(lambda x,y: x+y, fgas)
    fgms = reduce(lambda x,y: x+y, fgms)
    fg_distances = reduce(lambda x,y: x+y, fg_distances)

    '''replace blanks with 0s'''
    xpas[:] = ['0' if x=='' else x for x in xpas]
    xpms[:] = ['0' if x=='' else x for x in xpms]
    fgas[:] = ['0' if x=='' else x for x in fgas]
    fgms[:] = ['0' if x=='' else x for x in fgms]

    '''remove linebreak character from names'''
    names = map(lambda s: s.strip(), names)

    '''fpoints calculation'''
    fpoints = score_kickers(xpas,xpms,fgas,fgms,fg_distances)

    '''create dataframe from lists'''
    kickers_weekly_points_df = pd.DataFrame(
    list(zip(names,teams,years,weeks,positions,xpas,xpms,fgas,fgms,fg_distances,fpoints)),
    columns=kicker_weekly_fantasy_SCHEMA)

    '''remove duplicates'''
    kickers_weekly_points_df = kickers_weekly_points_df.drop_duplicates(subset=['name','team','year','week','position','xpa'])

    return kickers_weekly_points_df

def score_kickers(xpas,xpms,fgas,fgms,fg_distances):

    '''take all kicker data and return a list with the kicker scores
    input: xpas,xpms,fgas,fgms [list], fg_distances [list][list]
    ouptput: fpoints [list]'''
    
    fpoints = []

    for index in range(len(xpas)):
        score = 0.0
        
        '''xps'''
        if xpms[index] != "":
            score += float(xpms[index])
            score -= (float(xpas[index]) - float(xpms[index]))

        '''fgs'''
        if fg_distances[index] != 0:
            for distance in fg_distances[index]:
                if int(distance) <= 30:
                    score += 3.0
                else:
                    score += float(distance)/10

        try:
            score -= (float(fgas[index]) - float(fgms[index]))
        except:
            pass

        fpoints.append(score)
    
    return fpoints


def combine_all_kicker_data(year):
    '''function to get the combine all the csvs for kickers from our scrapes and put into one giant csv for all weeks

	input: year [int]
	output: pandas dataframe
	'''

    dfs_list = []
    weeks_list = list(range(1,19))

    '''iterate through weeks 1-18'''
    for week in weeks_list:
        path = os.getcwd() + f"/data/kicker_data/{year}/week{str(week)}_kicker/"
        file_list = glob.glob(path + "/*.csv")
        for file in file_list:
            if f'week{week}_all_kickers_points.csv' in file:
                df = pd.read_csv(file)
                dfs_list.append(df)

    '''concat all dfs, create empty columns and TOTAL column'''
    final_df = pd.concat([df for df in dfs_list])

    return final_df

def combine_all_years_kicker_data():
    '''function to get kicker data total files for all years that are present
    input: None
    output: pandas Dataframe
    '''

    dfs_list = []
    path = os.getcwd()

    paths_list = glob.glob(path+f'/data/kicker_data/*')
    for path in paths_list:
        file_list = glob.glob(path+'/*.csv')
        for file in file_list:
            if 'all_kicker_data' in file:
                df = pd.read_csv(file)
                dfs_list.append(df)


    '''concat all dfs'''
    final_df = pd.concat([df for df in dfs_list])

    return final_df

if __name__ == "__main__":
    year = 2025
    week = 4
	
    # 1. get all players first
    # players = get_all_players_table(year)
    # players.to_csv(f'data/player_data/{year}/{year}_players_df.csv', index=False)
     
    # 2. get fantasy points for each player for each week they played
    for week in range(1,week):
        print(f"Getting data for week {week}")
        players_weekly_points_df = get_points_for_each_player(year,week)

    # 2a. (optional) check pickle object
    # player_data_list = loadList(f'data/player_data/{year}/week{week}/week{week}_player_data_508')
    # print(player_data_list)

    # 3. combine all pickles into one object
    # weekly_points_df = combine_pickles(year, week)
    # print(weekly_points_df)

    # 4. get defensive scoring
    # defenses_df = get_defenses_scoring_table(year, week)
    # print(defenses_df)

    # 5. combine all players and defensive scoring into one dataframe˜
    # weekly_points_and_defenses_df = pd.concat([weekly_points_df,defenses_df])
    # print(weekly_points_and_defenses_df)
    # weekly_points_and_defenses_df.to_csv(f'data/player_data/{year}/week{week}/week{week}_all_players_points.csv',index=False)

    # 6. get kickers table
    # kickers = get_all_kickers_table(year)
    # print(kickers)
    # kickers.to_csv(f'data/kicker_data/{year}/{year}_kickers_df.csv', index=False)

    # 7. get all games played table (schedule)
    # for year in range(2025,2026):
    #     schedule_df = get_all_games_played_table(year)
    #     schedule_df.to_csv(f'data/schedules/{year}_schedule_df.csv', index=False)
    #     time.sleep(3)

    #8. scrape kicking data from each game on the schedule
    # get_kicking_scoring_data_from_boxscores(year, week, week)

    # 8a. (optional) check kicker pickle object
    # kicker_data_list = loadList(f'data/kicker_data/{year}/week{week}_kicker/week{week}_kicker_data_14')
    # print(kicker_data_list)-

    #9. and #10. combine all kicker pickles into one object, and score kickers
    # weekly_kicker_points_df = combine_pickles_kickers(year, week)
    # print(weekly_kicker_points_df)
    # weekly_kicker_points_df.to_csv(f'data/kicker_data/{year}/week{week}_kicker/week{week}_all_kickers_points.csv',index=False)

    #11. combine all kicker data into one giant kicker file for all weeks
    # all_kicker_data_df = combine_all_kicker_data(year)
    # print(all_kicker_data_df)
    # all_kicker_data_df.to_csv(f'data/kicker_data/{year}/{year}_all_kicker_data.csv',index=False)

    #12. Combine all years game_info files into one (2010-2024)
    # all_years_kicker_data_df = combine_all_years_kicker_data()
    # all_years_kicker_data_df.to_csv('data/kicker_data/all_years_kicker_data.csv', index=False)

	