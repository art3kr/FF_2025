import pandas as pd
import os
import glob

# Take kicker data
pd.read_csv('data/kicker_data/all_years_kicker_data.csv')


# Take game data
pd.read_csv('data/game_data/all_years_game_data.csv')


# offensive efficiancy?  How does ability to get into the red zone (% of drives that results in red zone or average field position after drive), affect kicker score. FG and XP percentage matters too

# How does percentage of drives that end in FGs or Touchdowns affect kicker score.  We want to pick kickers on offenses who aren't amazing at actually getting touchdowns, just good at getting close enough to kick field goals