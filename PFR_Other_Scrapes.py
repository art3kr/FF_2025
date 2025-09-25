import pandas as pd
import pickle
import requests
from functools import reduce
from bs4 import BeautifulSoup, Comment
import time
import os
import glob
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# To DO:
# Get weather data predictions for upcoming games
# Odds API for vegas line and over/under
# Consider reorganizing where I put weekly weather predictions and odds data
# Get punter data? 
    # Historical
# use old 2021 code for points allowed by each team to each position - use this for rankings/heatmap

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

if __name__ == "__main__":
    year = 2025
    week = 4

    #step 0: create directories
    # for year in (2025, 2025):
    #     create_directories(year)

    # 1.: scrape game info, save as pickles
    # for year in range(2025,2026):
    #     for week in range(1,4):
    #         get_game_info_data_from_boxscores(year, week, week)
    #         time.sleep(2)

    # 1a: check pickle
    # year = 2025 #debug
    # week = 3 #debug
    # game_info_list = loadList(f'data/game_data/{year}/week{week}_game_data/week{week}_game_data_16')
    # print(game_info_list)

    # 2. combine all pickles into one object
    # for year in range(2025, 2026):
    #     for week in range(1,4):
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

