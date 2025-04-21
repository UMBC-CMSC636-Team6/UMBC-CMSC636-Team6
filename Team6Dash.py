import json
import os

import pandas as pd
from pandas.api.types import is_string_dtype, is_numeric_dtype
from dash import Dash, dcc, html, Input, Output, callback, State
import requests
from io import StringIO
import plotly.express as px
import geopandas

#colors
background_color = "rgba(0, 0, 0, 0)"
text_color = 'rgba(255, 255, 255, 0)'


data_point_mapping = {'B25058EST1': 'Median Rent', 
                      'RENT_PER_ROOM': 'Rent Per Room', 
                      'AVG_SURROUNDING_MED_RENT': 'Avg Neighbor Rent', 
                      'AVG_SURROUNDING_RENT_PER_ROOM': 'Avg Neighbor Rent Per Room', 
                      'REL_SURROUNDING_MED_RENT': 'Relative Rent Percent', 
                      'REL_SURROUNDING_MED_RENT_PER_ROOM': 'Relative Rent Per Room Percent', 
                      'STUSAB': 'State', 
                      'NAME': 'County'}
data_point_list = [data_point_mapping[key] for key in data_point_mapping]

#Function to make a map
#mainly to prove that we can use functions to make combining front and back end easier
def get_first_map(dataframe, geojson, data_col):
    # Map from Alpha release for testing purposes
    column_names = data_point_mapping.copy()
    column_names['STUSAB'] = 'State'
    column_names['STATE'] = 'State Name'
    column_names['NAME'] = 'County'

    dataframe = dataframe.rename(columns=column_names)
    data_col_renamed = column_names[data_col]
    fig = px.choropleth(dataframe, geojson=geojson, locations='GEOID', color=data_col_renamed,
                        color_continuous_scale="BuPu",
                        range_color=(0, dataframe[data_col_renamed].max()),
                        scope="usa",
                        labels={data_col_renamed: data_col_renamed},
                        hover_data={column_names["STUSAB"]: True, column_names["NAME"]: True, data_col_renamed: True, "GEOID": False}
                        )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, plot_bgcolor=background_color,
    paper_bgcolor=background_color, geo_bgcolor = background_color)
    return fig

#inputs:
# df_county: dataframe containing data read from census data by county
# df_adj: dataframe containing counties listing all adjacent counties
#outputs:
# df_county: dataframe contianing original data columns and new data columns
def get_transformation_columns(df_county, df_adj):
    
    #Percent of renters relative to total occupied housing units
    df_county['PCT_RENTER'] = (df_county['B25032EST13'] / df_county['B25002EST2']) * 100
    
    #Median rent divided by median rooms per unit
    df_county['RENT_PER_ROOM'] = (df_county['B25058EST1'] / df_county['B25021EST3'])
    
    #Median rent in a county normalized by the average of the median rent in surrounding counties
    df_adj2 = pd.merge(df_adj, df_county[['GEOID', 'B25058EST1', 'B25021EST3']], left_on = ['Neighbor GEOID'], right_on = ['GEOID'], how = 'inner') #join median rent on neightbor geoid
    avg_neighbor_med_rent = df_adj2.groupby('County GEOID')['B25058EST1'].agg('mean').rename('AVG_SURROUNDING_MED_RENT') #average the neighbor median rent on county geoid
    df_county = pd.merge(df_county, avg_neighbor_med_rent, left_on='GEOID', right_on='County GEOID') #add new column back to main dataframe
    df_county['REL_SURROUNDING_MED_RENT'] = ((df_county['B25058EST1'] / df_county['AVG_SURROUNDING_MED_RENT']) * 100) - 100 #Normalize the rent of each county wth the average surrounding. Higher = overpriced compare to surroundings
    
    #Average median rooms per unit of surrounding counties, and average/relative surrounding rent per room
    avg_neighbor_med_rooms = df_adj2.groupby('County GEOID')['B25021EST3'].agg('mean').rename('AVG_SURROUNDING_MED_ROOMS') #average the neighbor median rooms per unit on county geoid
    df_county = pd.merge(df_county, avg_neighbor_med_rooms, left_on='GEOID', right_on='County GEOID') #add new column back to main dataframe
    df_county['AVG_SURROUNDING_RENT_PER_ROOM'] = (df_county['AVG_SURROUNDING_MED_RENT'] / df_county['AVG_SURROUNDING_MED_ROOMS']) #Average surrounding median rent divided by average surrounding median rooms per unit
    df_county['REL_SURROUNDING_MED_RENT_PER_ROOM'] = ((df_county['RENT_PER_ROOM'] / df_county['AVG_SURROUNDING_RENT_PER_ROOM']) * 100) - 100 #Normalize the rent per room of each county wth the average surrounding. Higher = overpriced compare to surroundings
    return df_county

#inputs:
# counties: every county's geojson. id should correspond to GEOID in df_county
# states: every states' geojson. id should correspond to GEOID in df_state
# df_county: full dataframe containing all datapoints by county
# df_state: full dataframe containing all datapoints by state
# filter_list: list of states whose counties should be included. All states not in this list will use only the state data. Should be the full name of the state
#returns: 
# combined_geojson: geojson of included counties and excluded state geojsons
def filter_states(df_county, df_state, counties, states, filter_list):
    #change filter list to list the geojson id of the states instead of names
    state_name_ids = {}
    for i in states['features']:
        state_name_ids[i['properties']['name']] = i['id']

    id_list = [state_name_ids[i] for i in filter_list]
    
    #Combine the geojson data of the included counties and excluded states
    combined_geojson = {"type":"FeatureCollection"}
    county_features = [i for i in counties['features'] if i['properties']['STATE'] in id_list]
    state_features = [i for i in states['features'] if f"{int(i['id']):02d}" in id_list] # Some IDs are 1-digit only. Force it into a 2-digit format.
    df_county['GEOID'] = df_county['GEOID'].apply(lambda x: f"{x:05d}") # States with IDs with leading 0s also have GEO_IDs with leading 0s. Reformat GEOID to 5 digits
    combined_geojson['features'] = county_features + state_features

    #set the GEOID of the states = id in states geojson features
    # df_combined = pd.concat([df_state.loc[~df_state['STUSAB'].isin(id_list)], df_county.loc[df_county['STUSAB'].isin(id_list)]])
    # df_combined = df_county.loc[df_county['STATE'].isin(id_list)] #for now, don't show any data for states not in focus
    
    print(id_list)
    # print(df_county)
    # print(is_string_dtype(df_county['STATE'])) # False
    # print(is_numeric_dtype(df_county['STATE'])) # True
    df_combined = df_county[df_county['STATE'].isin(list(map(int, id_list)))] # Conversion required for comparison.

    return (combined_geojson, df_combined)

# https://dash.plotly.com/clientside-callbacks
# Updates the map every time a new input from the dropdown is selected
# Stored data in all_data is [df_county, df_state, counties, states]
@callback(
    Output("map_fig", "figure"),
    Input('ref_button', 'n_clicks'),
    State("all_data", "data"),
    State("state_dropdown", "value"),
    State("data_point_dropdown", "value")
)
def update_all_data(n_clicks, data, state_selections, data_point_selection):

    #print(n_clicks)

    # Unmarshalls json data to dataframe format
    df_county = pd.read_json(StringIO(data["df_county"]), orient="split")
    df_state = pd.read_json(StringIO(data["df_state"]), orient="split")

    # filters by state and updates the map
    filtered_geojson, filtered_df = filter_states(df_county, df_state, data["counties"], data["states"], state_selections)
    fig = get_first_map(filtered_df, filtered_geojson, 'B25058EST1')

    return fig

def main():
    #gets data
    data = requests.get("https://raw.githubusercontent.com/UMBC-CMSC636-Team6/UMBC-CMSC636-Team6/refs/heads/main/ACS_5YR_Housing_Estimate_Data_by_County_2352642343660635057.csv")
    df_county_full = pd.read_csv(StringIO(data.text), dtype={'GEOID': str, 'STATE': str, 'COUNTY': str})
    data = requests.get("https://raw.githubusercontent.com/UMBC-CMSC636-Team6/UMBC-CMSC636-Team6/refs/heads/main/ACS_5YR_Housing_Estimate_Data_by_State_-5633158829445399210.csv")
    df_state_full = pd.read_csv(StringIO(data.text), dtype={'GEOID': str})
    # data = requests.get("https://raw.githubusercontent.com/UMBC-CMSC636-Team6/UMBC-CMSC636-Team6/refs/heads/main/DD_ACS_5-Year_Housing_Estimate_Data_by_County.csv")
    # df_keys = pd.read_csv(StringIO(data.text))
    data = requests.get("https://raw.githubusercontent.com/UMBC-CMSC636-Team6/UMBC-CMSC636-Team6/refs/heads/main/county_adjacency2024.txt")
    df_adj = pd.read_csv(StringIO(data.text), sep='|', dtype={'County GEOID': str, 'Neighbor GEOID': str})
    with requests.get("https://raw.githubusercontent.com/UMBC-CMSC636-Team6/UMBC-CMSC636-Team6/refs/heads/main/geojson-counties-fips.json") as response:
        counties = json.load(StringIO(response.text))
    with requests.get("https://raw.githubusercontent.com/UMBC-CMSC636-Team6/UMBC-CMSC636-Team6/refs/heads/main/us-states.json") as response:
        states = json.load(StringIO(response.text))

    # df_county_full = pd.read_csv("./ACS_5YR_Housing_Estimate_Data_by_County_2352642343660635057.csv")
    # df_keys = pd.read_csv("./DD_ACS_5-Year_Housing_Estimate_Data_by_County.csv")
    # df_adj = pd.read_csv("./county_adjacency2024.txt")
    
    df_county = df_county_full[['GEOID', 'STATE', 'STUSAB', 'STATE_NAME', 'NAME','B25002EST1', 'B25002EST2', 'B25058EST1', 'B25032EST13', 'B25021EST3']].copy()
    df_state = df_state_full[['GEOID', 'STUSAB', 'NAME','B25002EST1', 'B25002EST2', 'B25058EST1', 'B25032EST13', 'B25021EST3']].copy()
    get_transformation_columns(df_county, df_adj)

    # Gets sorted list of states from dataframe to use in dropdown
    state_list = df_county["STATE_NAME"].tolist()
    state_list = list(set(state_list))
    state_list = sorted(state_list)

    # Data to be stored in dash between callbacks
    # Marshalls dataframes into json format to be stored in dash
    callback_data = {
        "df_county": df_county.to_json(orient="split"),
        "df_state": df_state.to_json(orient="split"),
        "counties": counties,
        "states": states,
    }

    state_list = df_county["STATE_NAME"].tolist()
    state_list = list(set(state_list))
    state_list = sorted(state_list)
    
    

    # Get initial map figure to load in so the page doesnt load in a random graph for a split second
    fig = get_first_map(df_county, counties, 'B25058EST1')

    #To update background color please check the assets/style.css file
    app = Dash(__name__)
    #app.css.append_css({'external_url': 'format.css'})
    # The Dashboard
    app.layout = html.Div(
        html.Div(
            className="page-background",
            children=[
                html.Div(
                    className="page-container",
                    children=[
                        html.Div(
                            className="items-row",
                            children=[
                                html.Div(
                                    className="text-box super-big-text half-width text-align-left",
                                    children="Rent Analytics"
                                ),
                                html.Div(
                                    children=[
                                        html.Div(
                                            className="text-align-left",
                                            children="Team 6 Developers:"
                                        ),
                                        html.Div(
                                            className="text-align-left",
                                            children="Allison Lee, Chris DeVoe, Gregory Marinakis, Jon Woods, +1 more."
                                        )
                                    ]
                                )
                            ]
                        ),
                        html.Div(className="spacer"),
                        html.Button(
                            id = 'ref_button',
                            n_clicks = 0,
                            className="button-style1",
                            children=(
                                "Refresh Map."
                            )
                        ),
                        html.Div(className="h-line"),
                        html.Div(
                            className="text-box-2 half-width text-align-left",
                            children=(
                                "Our goals as Team 6 was to discover the trends and similarities in the provided housing data. We aim to show search, lookup and/or browsing features while being able to compare and identify trends within our data."
                            )
                        ),
                        # Add dropdown to page
                        html.Div(
                            className="text-box-1 half-width",
                            children=[
                                html.Div(
                                    children=[
                                        html.P("Select a state:"),
                                        dcc.Dropdown(
                                            className="black-text",
                                            id="state_dropdown",
                                            options=state_list,
                                            value=["Maryland"],
                                            placeholder="Select a state",
                                            multi=True
                                        )
                                    ]
                                )
                            ]
                        ),
                        html.Div(
                            className="text-box-1 half-width",
                            children=[
                                html.Div(
                                    children=[
                                        html.P("Select a data point:"),
                                        dcc.Dropdown(
                                            className="black-text",
                                            id="data_point_dropdown",
                                            options=data_point_list,
                                            value=[data_point_list[0]],
                                            placeholder="Select a data point",
                                            multi=False
                                        )
                                    ]
                                )
                            ]
                        ),
                        # Store data between callbacks
                        dcc.Store(
                            id="all_data",
                            data=callback_data
                        ),
                        # The map runs here we can put multiple and keep using the HTML style code to keep adding more
                        dcc.Graph(
                            id="map_fig",
                            className="max-width",
                            figure=fig
                        ),
                        html.P(
                            children=(
                                "Figure 1: The map above shows the selected data point of the states and counties within the United States."
                            )
                        )
                    ]
                )
            ]
        )
    )
    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 8050))
        # app.run(debug=True)
        app.server.run(debug=True, host='0.0.0.0', port = port)

main()