import json
import os

import pandas as pd
import numpy as np
from pandas.api.types import is_string_dtype, is_numeric_dtype
from dash import Dash, dcc, html, Input, Output, callback, State
import requests
from io import StringIO
import plotly.express as px
import plotly.graph_objects as go
import geopandas

#colors
background_color = "rgba(0, 0, 0, 0)"
text_color = "rgba(255, 255, 255, 1)"


data_point_mapping = {'B25058EST1': 'Median Rent($)', 
                      'RENT_PER_ROOM': 'Median Rent Per Room($)', 
                      'AVG_SURROUNDING_MED_RENT': 'Avg Neighboring Rent($)', 
                      'AVG_SURROUNDING_RENT_PER_ROOM': 'Avg Neighboring Rent Per Room($)', 
                      'REL_SURROUNDING_MED_RENT': 'Relative Rent Percent(%)', 
                      'REL_SURROUNDING_MED_RENT_PER_ROOM': 'Relative Rent Per Room Percent(%)'}
data_point_list = [data_point_mapping[key] for key in data_point_mapping]

#Function to make a map
#mainly to prove that we can use functions to make combining front and back end easier
def get_first_map(dataframe, geojson, data_col):
    # Map from Alpha release for testing purposes
    fig = px.choropleth(dataframe, geojson=geojson, locations='GEOID', color=data_col,
                        color_continuous_scale="BuPu",
                        range_color=(0, dataframe[data_col].max()),
                        scope="usa",
                        labels={data_col: data_col},
                        hover_data={"State": True, "County": True, data_col: True, "GEOID": False}
                        )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, plot_bgcolor=background_color,
    paper_bgcolor=background_color, geo_bgcolor = background_color)
    return fig

def get_colors(xx,yy):
    np_green = np.asarray([0,1,1/4])
    np_orange = np.asarray([1,3/4,0])
    np_blue = np.asarray([0,1/4,1])
    np_pink = np.asarray([1,0,3/4])
    side_norm = np.linalg.norm(np_green - np_blue)
    u = (np_green - np_orange) / side_norm
    v = (np_green - np_blue) / side_norm
    w = np.cross(u, v)
    uvw = np.array([u,v,w]).T
    # print(u)
    print(type(uvw))
    colors = []
    for i in zip(xx.items(),yy.items()):
        x = i[0][1]
        y = i[1][1]
        pick_color = []
        if np.isnan(x) or np.isnan(y):
            pick_color = [255,255,255]
        else:
            pick_color = (((np.dot(uvw, np.atleast_2d(np.hstack(np.asarray([x,y,0]))).T) * side_norm * -1) + np.atleast_2d(np_green).T).T * 255).round().astype(int).tolist()[0]
        colors.append('#%02x%02x%02x' % tuple(pick_color))
    return colors

def set_color_col(dataframe, data_col1, data_col2, segments):
    maximum = dataframe[data_col1].max()
    minimum = dataframe[data_col1].min()
    yy = ((dataframe[data_col1] - minimum) / (maximum - minimum))
    if segments >= 2:
        segments = np.round(segments)
        yy = np.trunc(yy*(segments-0.01))/(segments-1)
    xx = yy * 0
    if data_col2 is not None:
        maximum = dataframe[data_col2].max()
        minimum = dataframe[data_col2].min()
        xx = (dataframe[data_col2] - minimum) / (maximum - minimum)
        if segments >= 2:
            xx = np.trunc(xx*(segments-0.01))/(segments-1)
    dataframe['color'] = get_colors(xx,yy)
    
#Function to make a bivariate map
#inputs:
# dataframe: dataframe containing processed data from county
# geojson: list containing geometry data for counties
# data_col1: Data point representing the x axis on the bivariate legend
# data_col2: Data point representing the y axis on the bivariate legend
#outputs:
# fig: Choropleth map object
def get_bivariate_map(dataframe, geojson, data_col1, data_col2):
    segments = 4 #number of colors per axis. Increasing this significantlly increases map generation time
    #By default, using Jupyter runtime measurements, takes 20-25 seconds for 4 segments (twice that for non simplified map)
    
    set_color_col(dataframe, data_col1, data_col2, segments)
    fig = px.choropleth(dataframe, geojson=geojson, locations='GEOID', color='color',
                        color_discrete_map='identity',
                        scope="usa",
                        hover_data={"State": True, "County": True, data_col1: True, data_col2: True, "color": False, "GEOID": False}
                        )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, 
                      plot_bgcolor=background_color,
                      paper_bgcolor=background_color, 
                      geo_bgcolor = background_color,
                      coloraxis_showscale=False,
                      showlegend=False)
    
    xxx = []
    yyy = []
    for i in range(segments):
        for j in range(segments):
            xxx.append((i/segments) + 0.01)
            yyy.append((j/segments) + 0.01)
    xxx = np.trunc(pd.Series(xxx)*(segments-0.01))/(segments-1)
    yyy = np.trunc(pd.Series(yyy)*(segments-0.01))/(segments-1)
    
    #Full range of legend colors
    legend = get_colors(xxx,yyy)
    
    #Everything below this line is for adding the bivariate color legend. 
    #Originally written by Jan Kühn (https://www.kaggle.com/code/yotkadata/bivariate-choropleth-map-using-plotly)
    
    # Reverse the order of colors
    legend_colors = legend[:]
    legend_colors.reverse()

    # Calculate coordinates for all nine rectangles
    coord = []

    # Adapt height to ratio to get squares
    width = 0.025
    height = 0.100
    
    vert = 0.95 #0 is left, 1 is right
    horiz = 0.5 #0 is bottom, 1 is top
    # Start looping through rows and columns to calculate corners the squares
    for row in range(1, segments+1):
        for col in range(1, segments+1):
            coord.append({
                'x0': round(vert-(col-1)*width, 4),
                'y0': round(horiz-(row-1)*height, 4),
                'x1': round(vert-col*width, 4),
                'y1': round(horiz-row*height, 4)
            })

    # Create shapes (rectangles)
    for i, value in enumerate(coord):
        # Add rectangle
        fig.add_shape(go.layout.Shape(
            type='rect',
            fillcolor=legend_colors[i],
            line=dict(
                color=background_color,
                width=0.05,
            ),
            xref='paper',
            yref='paper',
            xanchor='right',
            yanchor='top',
            x0=coord[i]['x0'],
            y0=coord[i]['y0'],
            x1=coord[i]['x1'],
            y1=coord[i]['y1'],
        ))
    
    # Add text for first variable
    fig.add_annotation(
        xref='paper',
        yref='paper',
        xanchor='left',
        yanchor='top',
        x=coord[(segments**2)-1]['x1'],
        y=coord[(segments**2)-1]['y1'],
        showarrow=False,
        text=data_col1 + ' 🠒',
        font=dict(
            color=text_color,
            size=11,
        ),
        borderpad=0,
    )
    
    # Add text for second variable
    fig.add_annotation(
        xref='paper',
        yref='paper',
        xanchor='right',
        yanchor='bottom',
        x=coord[(segments**2)-1]['x1'],
        y=coord[(segments**2)-1]['y1'],
        showarrow=False,
        text=data_col2 + ' 🠒',
        font=dict(
            color=text_color,
            size=11,
        ),
        textangle=270,
        borderpad=0,
    )
    
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
    df_county['REL_SURROUNDING_MED_RENT'] = ((df_county['B25058EST1'] / df_county['AVG_SURROUNDING_MED_RENT']) * 100) #Normalize the rent of each county wth the average surrounding. Higher = overpriced compare to surroundings

    #Average median rooms per unit of surrounding counties, and average/relative surrounding rent per room
    avg_neighbor_med_rooms = df_adj2.groupby('County GEOID')['B25021EST3'].agg('mean').rename('AVG_SURROUNDING_MED_ROOMS') #average the neighbor median rooms per unit on county geoid
    df_county = pd.merge(df_county, avg_neighbor_med_rooms, left_on='GEOID', right_on='County GEOID') #add new column back to main dataframe
    df_county['AVG_SURROUNDING_RENT_PER_ROOM'] = (df_county['AVG_SURROUNDING_MED_RENT'] / df_county['AVG_SURROUNDING_MED_ROOMS']) #Average surrounding median rent divided by average surrounding median rooms per unit
    df_county['REL_SURROUNDING_MED_RENT_PER_ROOM'] = ((df_county['RENT_PER_ROOM'] / df_county['AVG_SURROUNDING_RENT_PER_ROOM']) * 100) #Normalize the rent per room of each county wth the average surrounding. Higher = overpriced compare to surroundings
    
    
    column_names = data_point_mapping.copy()
    column_names['STUSAB'] = 'State'
    column_names['STATE'] = 'State Name'
    column_names['NAME'] = 'County'

    df_county = df_county.rename(columns=column_names)
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
    df_combined = df_county[df_county['State Name'].isin(list(map(int, id_list)))] # Conversion required for comparison.

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

    data_point = data_point_selection

    if isinstance(data_point_selection, list):
        data_point = data_point_selection[0]

    print(data_point)

    # Unmarshalls json data to dataframe format
    df_county = pd.read_json(StringIO(data["df_county"]), orient="split")
    df_state = pd.read_json(StringIO(data["df_state"]), orient="split")

    # filters by state and updates the map
    filtered_geojson, filtered_df = filter_states(df_county, df_state, data["counties"], data["states"], state_selections)
    if isinstance(data_point_selection, list):
        if len(data_point_selection) > 1:
            fig = get_bivariate_map(filtered_df, filtered_geojson, data_point_selection[0], data_point_selection[1])
            return fig
    
    fig = get_first_map(filtered_df, filtered_geojson, data_point)

    return fig

# Select all states in the dropdown if select_all box is selected, otherwise clear dropdown
@callback(
    Output("state_dropdown", "value"),
    Input('select_all', 'value'),
    State("all_states", "data"),
)
def select_all(select, all_states):
    # Updates dropdown with all states
    if select == ["selected"]:
        return all_states
    # Empty dropdown selection
    else:
        return []

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
        gpd_counties = geopandas.read_file(StringIO(response.text))
    with requests.get("https://raw.githubusercontent.com/UMBC-CMSC636-Team6/UMBC-CMSC636-Team6/refs/heads/main/us-states.json") as response:
        states = json.load(StringIO(response.text))

    #Use geopandas library to simplify the geometry to reduce compile time
    gpd_c = gpd_counties.copy()
    tol = 1000 #tolerance of simplification, reduce to reduce detail, increase to increase detail. https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.simplify.html
    gpd_c["geometry"] = (gpd_c.to_crs(gpd_c.estimate_utm_crs()).simplify(tol).to_crs(gpd_c.crs)) 
    counties = gpd_c.to_geo_dict(drop_id=True)
    for i in counties['features']:
        i['id'] = i['properties']['id']

    # df_county_full = pd.read_csv("./ACS_5YR_Housing_Estimate_Data_by_County_2352642343660635057.csv")
    # df_keys = pd.read_csv("./DD_ACS_5-Year_Housing_Estimate_Data_by_County.csv")
    # df_adj = pd.read_csv("./county_adjacency2024.txt")
    
    df_county = df_county_full[['GEOID', 'STATE', 'STUSAB', 'STATE_NAME', 'NAME','B25002EST1', 'B25002EST2', 'B25058EST1', 'B25032EST13', 'B25021EST3']].copy()
    df_state = df_state_full[['GEOID', 'STUSAB', 'NAME','B25002EST1', 'B25002EST2', 'B25058EST1', 'B25032EST13', 'B25021EST3']].copy()
    df_county = get_transformation_columns(df_county, df_adj)

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
    fig = get_first_map(df_county, counties, data_point_list[0])

    #To update background color please check the assets/style.css file
    app = Dash(__name__)
    #app.css.append_css({'external_url': 'format.css'})
    # The Dashboard
    app.layout = html.Div(
        html.Div(
            className="page-container",
            children=[
                html.Div(
                    className="navbar-container p3",
                    children=[
                        html.Div(
                            className="navbar-name emphasis-text text-align-left",
                            children="Team 6"
                        ),

                        # html.Div(
                        #     className="items-row",
                        #     children=[
                        #         html.Div(
                        #             className="navbar-button",
                        #             children="About"
                        #         ),
                        #         html.Div(
                        #             className="navbar-button",
                        #             children="Vis"
                        #         )
                        #     ]
                        # ),
                    ]
                ),

                html.Div(
                    className="screen-frame background-1 p1",
                    children=[

                        html.Div(className="new-layer image-landing"),
                        html.Div(className="new-layer image-gradient-frame"),

                        html.Div(
                            className="new-layer p2",
                            children=[
                                html.Div(className="spacer"),
                                html.Div(className="spacer"),
                                html.Div(className="spacer"),
                                html.Div(
                                    className="row-container justify-content-flex-end",
                                    children=[
                                        html.Div(
                                            className="about-container",
                                            children=[
                                                html.Div(
                                                    className="text-box big-text text-align-left",
                                                    children=(
                                                        "About"
                                                    )
                                                ),
                                                html.Div(className="h-line-text"),
                                                html.Div(
                                                    className="text-box text-align-left",
                                                    children=(
                                                        "Our goals as Team 6 was to discover the trends and similarities in the provided housing data. We aim to show search, lookup and/or browsing features while being able to compare and identify trends within our data."
                                                    )
                                                ),
                                            ]
                                        )
                                    ]
                                ),
                                html.Div(className="spacer"),
                                
                                html.Div(
                                    className="emphasis-text super-big-text",
                                    children="Rent Prices Across The United States"
                                ),

                                html.Div(
                                    className="body-text",
                                    children="Allison Lee, Chris DeVoe, Gregory Marinakis, Jon Woods, +1 more."
                                )
                            ]
                        )
                    ]
                ),

                html.Div(
                    className="auto-frame page-container background-2",
                    children=[
                        html.Div(className="h-line-spacer"),
                        html.Div(
                            className="row-container",
                            children=[
                                html.Div(
                                    className="guide-container",
                                    children=[
                                        html.Div(
                                            className="text-box big-text text-align-left",
                                            children=(
                                                "How To Use"
                                            )
                                        ),
                                        html.Div(className="h-line-text"),
                                        html.Div(
                                            className="text-box text-align-left",
                                            children=(
                                                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam vel sem ac sem vestibulum ullamcorper eu iaculis arcu. Ut metus diam, tincidunt a congue sed, elementum sed diam. Fusce ligula libero, interdum sit amet urna in, rhoncus sagittis augue. Maecenas et justo at eros ornare porttitor."
                                            )
                                        ),
                                    ]
                                ),
                                html.Div(
                                    className="controls-container",
                                    children=[
                                        html.Button(
                                            id = 'ref_button',
                                            n_clicks = 0,
                                            className="button-style1 half-width",
                                            children=(
                                                "Refresh Map."
                                            )
                                        ),
                                        
                                        # Add dropdown to page
                                        html.Div(
                                            className="text-box",
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
                                                        ),
                                                        # Select all box
                                                        dcc.Checklist(
                                                            id="select_all",
                                                            options=[{"label": "Select All", "value": "selected"}]
                                                        )
                                                    ]
                                                )
                                            ]
                                        ),
                                        html.Div(
                                            className="text-box",
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
                                                            multi=True
                                                        )
                                                    ]
                                                )
                                            ]
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
                        # Store list of all states for select all box
                        dcc.Store(
                            id="all_states",
                            data=state_list
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
                        ),
                        html.Div(className="h-line-spacer")
                    ]
                ),

                html.Div(
                    className="auto-frame background-1",
                    children=[
                        html.Div(
                            className="text-box",
                            children=(
                                "Contact: WIP"
                            )
                        ),
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
