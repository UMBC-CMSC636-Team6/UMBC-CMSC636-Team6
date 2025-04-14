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

def main():
    #gets data
    data = requests.get("https://raw.githubusercontent.com/allisol1/UMBC-CMSC631-Team6/refs/heads/main/ACS_5YR_Housing_Estimate_Data_by_County_2352642343660635057.csv")
    df_h_full = pd.read_csv(StringIO(data.text))
    data = requests.get("https://raw.githubusercontent.com/allisol1/UMBC-CMSC636-Team6/refs/heads/main/DD_ACS_5-Year_Housing_Estimate_Data_by_County.csv")
    df_keys = pd.read_csv(StringIO(data.text))
    data = requests.get("https://raw.githubusercontent.com/allisol1/UMBC-CMSC636-Team6/refs/heads/main/county_adjacency2024.txt")
    df_adj = pd.read_csv(StringIO(data.text), sep='|')

    # df_h_full = pd.read_csv("./ACS_5YR_Housing_Estimate_Data_by_County_2352642343660635057.csv")
    # df_keys = pd.read_csv("./DD_ACS_5-Year_Housing_Estimate_Data_by_County.csv")
    # df_adj = pd.read_csv("./county_adjacency2024.txt")

    state_geojson_full = geopandas.read_file("ACS_5YR_Housing_Estimate_Data_by_State_1435040831713560726.geojson")
    county_geojson_full = geopandas.read_file("ACS_5YR_Housing_Estimate_Data_by_County_318069920734049109.geojson")

    state_geojson = state_geojson_full[['GEOID', 'STUSAB', 'NAME','B25002EST1', 'B25002EST2', 'B25058EST1', 'B25032EST13', 'geometry']].copy()
    county_geojson = county_geojson_full[['GEOID', 'STUSAB', 'STATE_NAME', 'NAME','B25002EST1', 'B25002EST2', 'B25058EST1', 'B25032EST13', 'geometry']].copy()

    with requests.get("https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json") as response:
        counties = json.load(StringIO(response.text))
    # fig.show()

    #gets map
    fig = get_first_map(county_geojson, counties)

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
        app.run_server(debug=True)

main()