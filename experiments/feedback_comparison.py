 # Libraries
import streamlit as st
import pandas as pd
import numpy as np
import json
import base64

# getting variables from config.json
with open('config/config.json') as f:
    keys = json.load(f)
PATH = keys['path']


# Functions
# better read functions from utils, but not yet working
def add_bg(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"png"};base64,{encoded_string.decode()});
        background-size: cover
    }}
    </style>
    """,
    unsafe_allow_html=True
    )

# merging historical activities with latest activity data
def add_latest_activity(df_hist, df_new, date_column):
    # Fixing dtypes
    df_hist[date_column] = df_hist[date_column].astype(str)
    df_new[date_column] = df_new[date_column].astype(str)
    
    # Df merging of historical feedings and latest feeding
    df = pd.concat([df_hist, df_new], ignore_index=True)
    df[date_column] = pd.to_datetime(df[date_column])
    df[date_column] = df[date_column].dt.strftime('%Y-%m-%d')
    
    return df

# adding a column with the microbial composition based on the feeding temperature
def bacteria_column(df, bac_compos):
    df['bacteria_composition'] = np.where(
        df["temperature"] <= 20,
        bac_compos.loc[
            bac_compos["temperature"] == 20, "dominant_microbes"
        ],
        np.where(
            ((df["temperature"] > 20) & (df["temperature"] <= 25)),
            bac_compos.loc[
                bac_compos["temperature"] == 25, "dominant_microbes"
            ],
            np.where(
                ((df["temperature"] > 25) & (df["temperature"] <= 30)),
                bac_compos.loc[
                    bac_compos["temperature"] == 30, "dominant_microbes"
                ],
                bac_compos.loc[
                    bac_compos["temperature"] == 35, "dominant_microbes"
                ],
            ),
        ),
    )
    return df

# adding two columns for growth rates, one time normalized
def growth_rate_cols(df):
    df['growth_rate'] = (
        df['end_height'] / df['initial_height']
    )

    df['growth_rate_per_hour'] = (
        df['end_height'] 
        / df['initial_height'] 
        / df['feeding_time']
    )
    
    return df


# Loading data
feedings = pd.read_parquet(PATH + 'feedings.parquet')
bacteria_composition = pd.read_parquet(PATH + 'bacteria_composition.parquet')


# streamlit page
st.set_page_config(page_title="Keeprising")
add_bg('bread_loaf.png')  
st.title('Keeprising - Your Feeding')
st.header('How was your last feeding?')


# Adding new feeding data
# user input for feeding
date_today = st.date_input('Feeding date')
temperature_today = st.number_input('Temperature')
feeding_time_today = st.number_input('Feeding duration')
initial_height_today = st.number_input('Intial height')
end_height_today = st.number_input('End height')
bubble_size_today = st.number_input('Bubble size')

# storing latest information in a df
latest_feeding = pd.DataFrame(data={
    'feeding_date':date_today, 
    'temperature':temperature_today,
    'feeding_time':feeding_time_today,
    'initial_height':initial_height_today,
    'end_height':end_height_today,
    'bubble_size':bubble_size_today
}, index=[0])

# merging new feeding to history of feedings
feedings = add_latest_activity(df_hist=feedings, df_new=latest_feeding, date_column='feeding_date')

# saving df
feedings.to_parquet(PATH + 'feedings.parquet')

# application display
st.dataframe(feedings.tail())
st.write("Nice job! Well done!")


# Data processing
feedings_processed = feedings.copy()
# Bacteria composition depending on temperature
feedings_processed = bacteria_column(df=feedings_processed, bac_compos=bacteria_composition)

# Growth rate composition
feedings_processed = growth_rate_cols(df=feedings_processed)


# Storing data
feedings_processed.to_parquet(PATH + 'feedings_processed.parquet')