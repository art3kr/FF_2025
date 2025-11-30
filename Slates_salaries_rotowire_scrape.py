import requests
from bs4 import BeautifulSoup
import pandas as pd
import pickle
import datetime

##Run this on Tuesday every week 
# Function to check if a given slate ID is for a 'Thu-Mon Classic' contest.
def is_thu_mon_classic_slate(slate_id):
    """Check if a given slate ID is for a 'Thu-Mon Classic' contest."""
    base_url = "https://www.rotowire.com/daily/nfl/dfs-opportunities.php?site=DraftKings&slateID="
    response = requests.get(base_url + str(slate_id), verify=False)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        secondary_title = soup.find('div', class_='page-title__secondary')
        
        # Debugging info
        if secondary_title:
            print(f"Slate ID {slate_id} - Secondary Title Found: '{secondary_title.text.strip()}'")
        
        # Look for 'Thu-Mon' and 'Classic contest' in the title
        if secondary_title and 'Thu-Mon' in secondary_title.text and 'Classic contest' in secondary_title.text:
            return True
    return False

##Function to fetch data for the given slate ID.
def get_slate_data(slate_id):
    """Fetch data for the given slate ID."""
    api_url = f'https://www.rotowire.com/daily/tables/value-report-nfl.php?siteID=2&slateID={slate_id}&projSource=RotoWire&oshipSource=RotoWire'
    response = requests.get(api_url, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data for slate ID {slate_id}")
        return None
    

    
## Function to append new data with the correct week number to historical CSV.
def append_data_to_csv(data, filename='All_rotowire_salary.csv'):
    """Append new data with the next week number to the historical CSV file."""
    # Load the historical data to determine the latest week number
    try:
        historical_df = pd.read_csv(filename)
        max_week = historical_df['week'].max()  # Get the latest week number
        next_week = max_week + 1 if pd.notnull(max_week) else 1
    except FileNotFoundError:
        # If the file doesn't exist, start with week 1
        next_week = 1

    # Convert new data to DataFrame and add the week column
    df = pd.DataFrame(data)
    df['week'] = next_week

    # Append the new data to the historical data and save
    combined_df = pd.concat([historical_df, df], ignore_index=True) if 'historical_df' in locals() else df
    combined_df.to_csv(filename, index=False)
    print(f"Data for week {next_week} appended to {filename}")

      # Save latest week data separately
    save_latest_salary_data(df, next_week)


# Function to save the latest week's data in a separate CSV file.
def save_latest_salary_data(df, week):
    """Save the latest salary data in a separate CSV with the week number."""
    filename = f'Week{week}_salaries_rotowire.csv'
    df.to_csv(filename, index=False)
    print(f"Latest salary data for week {week} saved to {filename}")


##Function to find the latest valid 'Thu-Mon Classic' slate.
def find_latest_slate(start_slate=8950):
    """Find the latest 'Thu-Mon Classic' slate ID by iterating backward from a known recent range."""
    current_slate_id = start_slate
    while current_slate_id > 8941:  # Lower bound for iteration to avoid infinite loop
        if is_thu_mon_classic_slate(current_slate_id):
            print(f"Latest 'Thu-Mon Classic' slate found: {current_slate_id}")
            return current_slate_id
        current_slate_id -= 1  # Move backward in slate IDs by 1
    print("No valid 'Thu-Mon Classic' slate found within the range.")
    return None



## Main function to execute the process.
if __name__ == "__main__":

    week = 13
    # Find the latest valid 'Thu-Mon Classic' slate
    # latest_slate_id = find_latest_slate()

    latest_slate_id = 9194  # Manually set for week 13
    
    # Fetch and append data for the latest slate if found
    if latest_slate_id:
        data = get_slate_data(latest_slate_id)
        if data:
            # append_data_to_csv(data)
            df = pd.DataFrame(data)
            df['week'] = week
            save_latest_salary_data(df, week)
    else:
        print("No valid 'Thu-Mon Classic' slate found.")
