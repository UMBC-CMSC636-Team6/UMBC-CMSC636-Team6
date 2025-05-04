# Rent Prices Across The United States

An interactive visualization system designed to help non-experts learn about the differences in housing and rent pricing across the various counties of the United States.

## Running Locally

First, open the file `Team6Dash.py` in a Python environment. Make sure the environment has the following libraries installed, which are required to run the product:
- `pandas`
- `numpy`
- `plotly`
- `dash`
- `requests`
- `io`
- `geopandas`

Next, clone this repository in your Linux/Unix terminal to download all of its files:
```bash
git clone -b live git@github.com:UMBC-CMSC636-Team6/UMBC-CMSC636-Team6
```
The "live" branch is the current live verson of our repository.<br>
<br>
Once the repository is downloaded, run the Python code. If you are using your terminal, enter this command:
```bash
python3 Team6Dash.py
```
Finally, wait until your terminal or console displays a URL in the following format:
<pre>
...
 * Running on all addresses (0.0.0.0)
 * Running on http://xxx.x.x.x:xxxx
...
</pre>
Copy and paste that link into any browser, and you will be locally redirected to our Dash site.

## Running Online

To access the visualization via internet, visit https://umbc-cmsc636-team6-7pm7.onrender.com<br>
(Note: Due to some technical difficulties with using the free version of Render, the website may take an unusually long time to load or return a `502 Bad Gateway` error. If you repeatedly experience either issue with this link, refer to the previous section and try opening the site locally.)

## How to Use

(placeholder)

## Directory Structure

<pre>
Group6_FinalRelease.zip
|---- assets/
|     |---- city.webp
|     |---- style.css
|
|---- screenshots/
|     |---- Screenshot_1.png
|     |---- Screenshot_2.png
|     |---- Screenshot_3.png
|
|---- ACS_5YR_Housing_Estimate_Data_by_County_2352642343660635057.csv
|---- ACS_5YR_Housing_Estimate_Data_by_State_-5633158829445399210.csv
|---- DD_ACS_5-Year_Housing_Estimate_Data_by_County.csv
|---- Team6Dash.py
|
|---- Alpha.ipynb
|---- Phase1_ExtraCredit.ipynb
|---- transformation_artifacts.ipynb
|
|---- county_adjacency2024.txt
|---- geojson-counties-fips.json
|---- us-states.json
|
|---- README.md
|---- contact_info.txt
</pre>

## Contact
If you have any questions, please refer to the file `contact_info.txt`, which contains the name, email address, and GitHub URL of each contributor to this project.
