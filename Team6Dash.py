import json

import pandas as pd
from dash import Dash, dcc, html
import requests
from io import StringIO
import plotly.express as px
import geopandas

#colors
background_color = '#000000'
text_color = '#FFFFFF'

#Function to make a map
#mainly to prove that we can use functions to make combining front and back end easier
def get_first_map(county_geojson, counties):
    # Map from Alpha release for testing purposes
    fig = px.choropleth(county_geojson, geojson=counties, locations='GEOID', color='B25058EST1',
                        color_continuous_scale="BuPu",
                        range_color=(0, county_geojson['B25058EST1'].max()),
                        scope="usa",
                        labels={'B25058EST1': 'Median Rent'},
                        hover_data={"STATE_NAME": True, "NAME": True, "B25058EST1": True, "GEOID": False}
                        )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, plot_bgcolor=background_color,
    paper_bgcolor=background_color, geo_bgcolor = background_color)
    return fig

def get_transformation_columns(df_county, df_adj):
    
    #Percent of renters relative to total occupied housing units
    df_county['PCT_RENTER'] = (df_county['B25032EST13'] / df_county['B25002EST2']) * 100
    
    #Median rent in a county normalized by the average of the median rent in surrounding counties
    df_adj2 = pd.merge(df_adj, df_county[['GEOID', 'B25058EST1']], left_on = ['Neighbor GEOID'], right_on = ['GEOID'], how = 'inner') #join median rent on neightbor geoid
    avg_neighbor_med_rent = df_adj2.groupby('County GEOID')['B25058EST1'].agg('mean').rename('AVG_SURROUNDING_MED_RENT') #average the neighbor median rent on county geoid
    df_county = pd.merge(df_county, avg_neighbor_med_rent, left_on='GEOID', right_on='County GEOID') #add new column back to main dataframe
    df_county['REL_SURROUNDING_MED_RENT'] = (df_county['B25058EST1'] / df_county['AVG_SURROUNDING_MED_RENT']) * 100 #Normalize the rent of each county wth the average surrounding. Higher = overpriced compare to surroundings

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
    county_features = [i['properties']['STATE'] in id_list for i in counties['features']]
    state_features = [i['id'] in id_list for i in states['features']]
    combined_geojson['features'] = county_features + state_features
    
    #set the GEOID of the states = id in states geojson features
    # df_combined = pd.concat([df_state.loc[~df_state['STUSAB'].isin(id_list)], df_county.loc[df_county['STUSAB'].isin(id_list)]])
    df_combined = df_county.loc[df_county['STUSAB'].isin(id_list)] #for now, don't show any data for states not in focus
    return (combined_geojson, df_combined)

def main():
    #gets data
    data = requests.get("https://raw.githubusercontent.com/allisol1/UMBC-CMSC631-Team6/refs/heads/main/ACS_5YR_Housing_Estimate_Data_by_County_2352642343660635057.csv")
    df_county_full = pd.read_csv(StringIO(data.text))
    data = requests.get("https://raw.githubusercontent.com/allisol1/UMBC-CMSC631-Team6/refs/heads/main/ACS_5YR_Housing_Estimate_Data_by_State_-5633158829445399210.csv")
    df_state_full = pd.read_csv(StringIO(data.text))
    data = requests.get("https://raw.githubusercontent.com/allisol1/UMBC-CMSC636-Team6/refs/heads/main/DD_ACS_5-Year_Housing_Estimate_Data_by_County.csv")
    df_keys = pd.read_csv(StringIO(data.text))
    data = requests.get("https://raw.githubusercontent.com/allisol1/UMBC-CMSC636-Team6/refs/heads/main/county_adjacency2024.txt")
    df_adj = pd.read_csv(StringIO(data.text), sep='|')

    # df_county_full = pd.read_csv("./ACS_5YR_Housing_Estimate_Data_by_County_2352642343660635057.csv")
    # df_keys = pd.read_csv("./DD_ACS_5-Year_Housing_Estimate_Data_by_County.csv")
    # df_adj = pd.read_csv("./county_adjacency2024.txt")
    
    df_county = df_county_full[['GEOID', 'STATE', 'STUSAB', 'STATE_NAME', 'NAME','B25002EST1', 'B25002EST2', 'B25058EST1', 'B25032EST13']].copy()
    df_state = df_county_full[['GEOID', 'STUSAB', 'NAME','B25002EST1', 'B25002EST2', 'B25058EST1', 'B25032EST13']].copy()
    get_transformation_columns(df_county, df_adj)
    
    
    with requests.get("https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json") as response:
        counties = json.load(StringIO(response.text))
    with requests.get("https://raw.githubusercontent.com/PublicaMundi/MappingAPI/refs/heads/master/data/geojson/us-states.json") as response:
        states = json.load(StringIO(response.text))
        
    # fig.show()

    #gets map
    fig = get_first_map(df_county, counties)

    #To update background color please check the assets/style.css file
    app = Dash(__name__)
    #app.css.append_css({'external_url': 'format.css'})

    # The Dashboard
    app.layout = html.Div(style={'backgroundColor': background_color},
        children=[
            # Title
            #Need to figure out how to properly design this so that we can
            #make it look nicer
            html.H1(children="Team 6 Rent Analytics\n\n", className="header-title", style={'textAlign': 'center', 'color': text_color}),
            html.P(
                # The text and paragraphs
                children=(
                    "Analyze the behavior of TEST"
                ),
                className="header-description", style={'color': text_color}
            ),
            # The map runs here we can put multiple and keep using the HTML style code to keep adding more
            dcc.Graph(figure=fig),
            html.P(children=(
                    "Figure 1: This is a map"
                ),
                className="header-description",style={'color': text_color}),

        ]
    )

    if __name__ == "__main__":
        # app.run(debug=True)
        app.server.run(debug=True)

main()