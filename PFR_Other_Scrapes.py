import pandas as pd
import pickle
import requests
from functools import reduce
from bs4 import BeautifulSoup, Comment
import time
import os
import glob
import urllib3
import random
import ssl
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# To DO:
# Get weather data predictions for upcoming games
# Odds API for vegas line and over/under
# Consider reorganizing where I put weekly weather predictions and odds data
# Get punter data? 
    # Historical
# use old 2021 code for points allowed by each team to each position - use this for rankings/heatmap

'''request headers'''
user_agent_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
    ]

headers = {
    'User-Agent': random.choice(user_agent_list),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
    }

game_info_SCHEMA = [
    'boxscore_url',
    'won_toss',
    'won_OT_toss',
    'roof',
    'surface',
    'duration',
    'weather',
    'attendance',
    'vegas_line',
    'over_under',
]

def saveList(data, filename):
    open_file = open(filename, 'wb')
    pickle.dump(data, open_file)
    open_file.close()

def loadList(file):
    open_file = open(file, "rb")
    loaded_list = pickle.load(open_file)
    open_file.close()
    return loaded_list

def create_directories(year):
    '''function to create directories for game_data, kicker_data and player_data
    input: year [int]
    output: None
    '''
    path = os.getcwd()

    '''game data directory for year'''
    if not os.path.exists(path + f'/data/game_data/{year}'):
        os.makedirs(path + f'/data/game_data/{year}')
        for week in range(1,19):
            os.makedirs(path + f'/data/game_data/{year}/week{week}_game_data')

    '''kicker data directory for year'''
    if not os.path.exists(path + f'/data/kicker_data/{year}'):
        os.makedirs(path + f'/data/kicker_data/{year}')
        for week in range(1,19):
            os.makedirs(path + f'/data/kicker_data/{year}/week{week}_kicker')

    '''player data directory for year'''
    if not os.path.exists(path + f'/data/player_data/{year}'):
        os.makedirs(path + f'/data/player_data/{year}')
        for week in range(1,19):
            os.makedirs(path + f'/data/player_data/{year}/week{week}')


def get_game_info_data_from_boxscores(year, first_week=1, last_week=18):
     
    '''function to get the kicking weather data for each game for all weeks from pro-football-reference

	input: week [int]
	output: None
	'''

    '''load schedule df from csv'''
    schedule = pd.read_csv(f'data/schedules/{year}_schedule_df.csv')
    schedule = schedule[(schedule['week'] >= first_week) & (schedule['week'] <= last_week)]
    
    '''send request, get html table of players'''
    base_url = 'https://www.pro-football-reference.com'

    games_urls_list = schedule['boxscore_url'].tolist()
    weeks_list = schedule['week'].tolist()

    '''create row list'''
    rows = []

    '''iterate through all games in the schedule_df'''
    for i in range(len(schedule)):

        week = weeks_list[i]
        print(week)

        '''get html soup'''
        r = requests.get(base_url + games_urls_list[i], verify=False)
        soup = BeautifulSoup(r.content, 'lxml')
        soup2 = BeautifulSoup("\n".join(soup.find_all(string=Comment)), "lxml")

        # print(r.headers) #debug

        '''get game info table'''
        game_info_table = soup2.find('table', id="game_info")

        # print(game_info_table)

        '''Scrape each row from game info table'''
        titles = [cell.get_text() for row in game_info_table.find_all('tr') for cell in row.find_all('th')]
        values = [cell.get_text() for row in game_info_table.find_all('tr') for cell in row.find_all('td')]

        titles_to_find = ['Won Toss', 'Won OT Toss', 'Roof','Surface','Duration','Weather','Attendance','Vegas Line','Over/Under']

        print(games_urls_list[i])

        '''check if each title is in the list, if it is append corresponding value'''
        row = []
        row.append(games_urls_list[i])
        for title in titles_to_find:
            if title in titles:
                row.append(values[titles.index(title)+1])
            else:
                row.append('')

        rows.append(row)
        
        time.sleep(2)

        if i % 5 == 0:
            '''save as pickle'''
            end_index = i+1
            saveList(rows, f'data/game_data/{year}/week{week}_game_data/week{week}_game_data_{end_index}')
            
    '''save as pickle'''
    try:
        end_index = i+1
        saveList(rows, f'data/game_data/{year}/week{week}_game_data/week{week}_game_data_{end_index}')
    except:
        pass

    return

def combine_game_info_pickles(year, week):

    '''function to get the combine all the pickles from our scrape

	input: None
	output: pandas dataframe
	'''
    path = os.getcwd()
    file_list = glob.glob(path+f'/data/game_data/{year}/week{week}_game_data/*')
    file_list = [file for file in file_list if not file.endswith(".csv")]
    file_list = [os.path.basename(i) for i in file_list]
    file_list = sorted(file_list, key=lambda x: int(x.split('_')[-1])) #sort list

    '''condition if there are not files (like no week 18 in years 2010-2020)'''
    if not file_list:
        return

    rows = []

    for file in file_list:
        current_pickle_list = loadList(f'data/game_data/{year}/week{week}_game_data/{file}')
        rows.append(current_pickle_list)

    '''Flatten list'''
    rows = reduce(lambda x,y: x+y, rows)

    '''create dataframe from lists'''
    game_info_df = pd.DataFrame(rows,columns=game_info_SCHEMA)

    '''remove duplicates'''
    game_info_df = game_info_df.drop_duplicates(subset=['boxscore_url'])

    '''break out weather data'''
    game_info_df[['temp','humidity','wind']] = game_info_df['weather'].str.split(',', n=2, expand=True).fillna('')
    game_info_df = game_info_df.drop(['weather'], axis=1)

    return game_info_df

def combine_all_game_data(year):
    '''function to get the combine all the csvs for game_data from our scrapes and put into one giant csv for all weeks

	input: year [int]
	output: pandas dataframe
	'''

    dfs_list = []
    weeks_list = list(range(1,19))

    '''iterate through weeks 1-18'''
    for week in weeks_list:
        path = os.getcwd() + f"/data/game_data/{year}/week{str(week)}_game_data/"
        file_list = glob.glob(path + "/*.csv")
        for file in file_list:
            if f'week{week}_game_data.csv' in file:
                df = pd.read_csv(file)
                dfs_list.append(df)

    '''concat all dfs'''
    final_df = pd.concat([df for df in dfs_list])

    return final_df

def combine_all_years_game_data():
    '''function to get game data total files for all years that are present
    input: None
    output: pandas Dataframe
    '''

    dfs_list = []
    path = os.getcwd()

    paths_list = glob.glob(path+f'/data/game_data/*')
    for path in paths_list:
        file_list = glob.glob(path+'/*.csv')
        for file in file_list:
            if 'all_game_data' in file:
                df = pd.read_csv(file)
                dfs_list.append(df)


    '''concat all dfs'''
    final_df = pd.concat([df for df in dfs_list])

    return final_df

def get_weekly_weather_data(year,week):
    '''function to get weather predictions for games of a certain week
    input: week [int]
    output: pandas Dataframe'''

    base_url = f'https://www.nflweather.com/week/{year}/week-{week}'

    '''get html soup'''
    r = requests.get(base_url)
    soup = BeautifulSoup(r.content, 'lxml')
    soup2 = BeautifulSoup("\n".join(soup.find_all(string=Comment)), "lxml")
    # print(soup)
    # print(soup2)

    '''get game info table'''
    team_names = soup2.find_all('span', {'class':'ms-1'})
    print(team_names)

    classes = [value
           for element in soup.find_all(class_=True)
           for value in element["class"]]
    
    print(classes)

def get_points_allowed(year):
    '''function to get the table of teams and their points allowed at each position from pro football reference

    input: none
    output: pandas dataframe
    '''

    '''send request, get html table of teams and points'''
    base_url = f'https://www.pro-football-reference.com/years/{year}/fantasy-points-against-'

    positions = ['QB','RB','WR','TE']
    position_dfs = []

    '''iterate through position tables'''
    for position in positions:

        r = requests.get(base_url + position + '.htm')
        soup = BeautifulSoup(r.content, 'html.parser')
        points_allowed_table_html = soup.find_all('table')[0]

        '''create lists'''
        teams = []
        points_allowed_half = []

        '''iterate through html table of players'''
        for index, row in enumerate(points_allowed_table_html.find_all('tr')[2:]):

            try:
                '''get team and points allowed'''
                team = row.find('th', attrs={'data-stat': 'team'}).get_text()
                point_allowed_half = float(row.find('td', attrs={'data-stat': 'fanduel_points_per_game'}).get_text())

                '''append to lists'''
                teams.append(team)
                points_allowed_half.append(point_allowed_half)

            except:
                pass

        '''create dataframe from lists'''
        points_allowed_df = pd.DataFrame(
            list(zip(teams,points_allowed_half)),
            columns=['team','{}_points_allowed_half'.format(position)])

        '''append dataframe to list of position dfs'''
        position_dfs.append(points_allowed_df)

    '''concat all position points allowed dfs'''
    points_allowed_df = reduce(lambda left,right: pd.merge(left,right,on=['team'],how='outer'),position_dfs)

    return points_allowed_df

def get_espn_team_stats(year):
    '''function to get team stats from ESPN including scoring and 4th/1st down data

    input: year [int]
    output: pandas dataframe
    '''

    categories = {'offense total':'',
                  'offense passing':'/_/stat/passing',
                  'offense rushing':'/_/stat/rushing',
                  'offense receiving':'/_/stat/receiving',
                  'offense downs':'/_/stat/downs',
                  'defense':'/_/view/defense',
                  'defense passing':'/_/view/defense/stat/passing',
                  'defense rushing':'/_/view/defense/stat/rushing',
                  'defense receiving':'/_/view/defense/stat/receiving',
                  'defense downs':'/_/view/defense/stat/downs',
                  'ST returning':'/_/view/special',
                  'ST kicking':'/_/view/special/stat/kicking',
                  'ST punting':'/_/view/special/stat/punting',
                  'turnover':'/_/view/turnovers'
    }

    '''send request, get html table of teams and points'''
    base_url = f'https://www.espn.com/nfl/stats/team'

    final_df = pd.DataFrame()

    for category, tail_url in categories.items():
        print(f"Getting {category}...")
        url = base_url + tail_url

        # Randomize UA for each request
        headers['User-Agent'] = random.choice(user_agent_list)

        try:
            r = requests.get(url, headers=headers, verify=False)
            
            if r.status_code != 200:
                print(f"Failed to retrieve {category}: Status {r.status_code}")
                continue

            # Pandas read_html is much easier for ESPN than BS4
            # ESPN usually splits tables: [0] is Team Names, [1] is Data
            dfs = pd.read_html(r.content, header=0)

            # print(dfs)

            if not dfs:
                print(f"No tables found for {category}")
                continue

            # Merge the Team Name table with the Stats table
            # usually dfs[0] is 32 rows of team names, dfs[1] is 32 rows of stats
            if len(dfs) >= 2:
                df_team = dfs[0]
                df_stats = dfs[1]
                current_df = pd.concat([df_team, df_stats], axis=1)
            else:
                current_df = dfs[0]

            # Merge into final DataFrame
            if final_df.empty:
                final_df = current_df
            else:
                # Merge on Team Name
                # Note: ESPN Team names might slightly differ from PFR (e.g. "Arizona" vs "Arizona Cardinals")
                # You may need a mapping function later, but this merges the ESPN data together.
                if 'team_name' in current_df.columns and 'team_name' in final_df.columns:
                    final_df = pd.merge(final_df, current_df, on='team_name', how='outer')
            
            # Sleep to be polite and avoid rate limits
            time.sleep(random.uniform(1.5, 3.0))

        except Exception as e:
            print(f"Error processing {category}: {e}")

        break


    return final_df


if __name__ == "__main__":
    year = 2025
    week = 11

    #step 0: create directories
    # for year in (2025, 2025):
    #     create_directories(year)

    # 1.: scrape game info, save as pickles
    # for year in range(2025,2026):
    #     for week in range(week,week+1):
    #         get_game_info_data_from_boxscores(year, week, week)
    #         time.sleep(2)

    # 1a: check pickle
    # year = 2025 #debug
    # week = 8 #debug
    # game_info_list = loadList(f'data/game_data/{year}/week{week}_game_data/week{week}_game_data_13')
    # print(game_info_list)

    # 2. combine all pickles into one object
    # for year in range(2025, 2026):
    #     for week in range(week,week+1):
    #         print(year, week)
    #         game_info_df = combine_game_info_pickles(year, week)
    #         # print(game_info_df)

    #         #3. combine game_info with schedule
    #         schedule_df = pd.read_csv(f'data/schedules/{year}_schedule_df.csv')
    #         final_df = pd.merge(schedule_df,game_info_df,on=['boxscore_url'],how='inner')
    #         print(final_df)
    #         final_df.to_csv(f'data/game_data/{year}/week{week}_game_data/week{week}_game_data.csv', index=False)

    #4. Combine all game_info files of one year into one
    # for year in range(2025,2026):
    #     all_game_data_df = combine_all_game_data(year)
    #     print(all_game_data_df)
    #     all_game_data_df.to_csv(f'data/game_data/{year}/{year}_all_game_data.csv',index=False)

    #5. Combine all years game_info files into one (2010-2025)
    # all_years_game_data_df = combine_all_years_game_data()
    # all_years_game_data_df.to_csv('data/game_data/all_years_game_data.csv', index=False)


    #6. Weekly weather data - work in progress to get weather predictions for upcoming games
    # get_weekly_weather_data(year,week)

    #7 Get points allowed by each team to each position
    # points_allowed_df = get_points_allowed(year)
    # print(points_allowed_df)
    # points_allowed_df.to_csv(f'data/team_data/{year}/{year}_fantasy_points_allowed.csv',index=False)

    #8 Get team scoring and 4th/1st down data from ESPN
    team_stats_df = get_espn_team_stats(year)
    print(team_stats_df)
    print(team_stats_df.columns)

