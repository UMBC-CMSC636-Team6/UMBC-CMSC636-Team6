# Rent Prices Across The United States

An interactive visualization designed to help users learn about the differences in housing and rent pricing across the various counties in the United States.

## Running Locally

Make sure you are running in a python environment has the following libraries installed:
- `pandas`
- `numpy`
- `plotly`
- `dash`
- `requests`
- `io`
- `geopandas`

<br>
Run the Team6Dash.py file. If you are using your terminal, enter this command:
```bash
python3 Team6Dash.py
```
Wait until your terminal or console displays a URL in the following format:
<pre>
...
 * Running on all addresses (0.0.0.0)
 * Running on http://xxx.x.x.x:xxxx
...
</pre>
Copy and paste the link into a browser. You will be locally redirected to our Dash site.<br>
<br>
You may stop the program at any time by pressing `Ctrl+C` in your terminal.

## Running Online

To access the visualization via internet, simply visit: https://umbc-cmsc636-team6-7pm7.onrender.com<br>
<br>
(Note: Due to some technical difficulties with using the free version of Render, the website may take an unusually long time to load or return a `502 Bad Gateway` error. If you repeatedly experience either issue with this link, refer to the previous section and try opening the site locally.)

## How to Use

Once you have access to the site, you should now be able to scroll down to, access, and hover over a choropleth map of the median rent. By default, it should display only the state of Maryland's data with no settings configured in either dropdown menu, as shown below.
![Default choropleth map](screenshots/Screenshot_1.png)<br>
<br>
To choose what states you want to see visualized, select the state in the "Select a State" dropdown. You may add as many states as you want to the map in this way, or you can choose to display data for the entire country by clicking the "Select All" checkbox under it. To clear your state selections, simply check and then uncheck "Select All".<br>
<br>
To visualize specific value(s) related to housing costs, open the dropdown menu labeled "Select a data point" and choose what you would like to see. Your options are median rent (in dollars), average neigboring rent (in dollars), average rent per room (in dollars), and relative percentages of the latter two values. We recommend selecting either one or two values at a time, and please note that the "Refresh Map" button will *not* work if no values are selected from this dropdown menu.<br>
<br>
When you have finished setting your preferences on what to display, update the map by clicking the "Refresh Map" button found directly above the dropdown menus. This may take between a few frames and several seconds to apply depending on Render's functionality at that moment.
![Example dropdown menu: AK, CA, and MD](screenshots/Screenshot_2.png)<br>
<br>
Once the choropleth map has been refreshed with your preferences, you can then travel to a specific area on the map as well as view specific data points. Scroll down in the map's region to zoom in, click and drag to move around on the zoomed map, and scroll up to zoom back out. If you want to see the exact data point for a certain county, hover your cursor over that county on the map. This will display the name, state, and value(s) from the dropdown menu for that county.
![Example output: AK, CA, and MD](screenshots/Screenshot_3.png)

## Directory Structure

<pre>
Group6_FinalRelease.zip
|---- data/
|     |---- ACS_5YR_Housing_Estimate_Data_by_County_2352642343660635057.csv
|     |---- ACS_5YR_Housing_Estimate_Data_by_State_-5633158829445399210.csv
|     |---- ACS_5-Year_Housing_Estimate_Data_by_County.csv
|     |---- DD_ACS_5-Year_Housing_Estimate_Data_by_County.csv
|     |---- geojson-counties-fips.json
|     |---- us-states.json
|     |---- county_adjacency2024.txt
|
|---- flask_server
|     |---- assets/
|     |     |---- city.webp
|     |     |---- style.css
|
|     |---- ACS_5YR_Housing_Estimate_Data_by_County_2352642343660635057.csv
|     |---- ACS_5YR_Housing_Estimate_Data_by_State_-5633158829445399210.csv
|     |---- ACS_5-Year_Housing_Estimate_Data_by_County.csv
|     |---- DD_ACS_5-Year_Housing_Estimate_Data_by_County.csv
|     |---- geojson-counties-fips.json
|     |---- us-states.json
|     |---- county_adjacency2024.txt
|     |---- requirements.txt
|     |---- runtime.txt
|     |---- Procfile
|     |---- Team6Dash.py
|
|---- screenshots/
|     |---- Screenshot_1.png
|     |---- Screenshot_2.png
|     |---- Screenshot_3.png
|
|---- README.md
|---- contact_info.txt
</pre>

## Contact Us

If you have any questions, please refer to the file `contact_info.txt`, which contains the name, email address, and GitHub URL of each contributor to this project.
