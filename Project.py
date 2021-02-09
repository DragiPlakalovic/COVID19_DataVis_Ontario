import csv
import geopandas as gpd
import pandas as pd
from bokeh.io import show, curdoc
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar
from bokeh.models import Slider, HoverTool
import json
from bokeh.palettes import brewer
from bokeh.models import CheckboxButtonGroup, RadioButtonGroup, CustomJS
from bokeh.layouts import widgetbox, row, column

# Names of files needed
covid_map = "ontario_map/Ministry_of_Health_Public_Health_Unit_Boundary.shp"
covid_data = "cases_by_status_and_phu.csv"

# Open .csv file using dictionaries
input_data = csv.DictReader(open(covid_data))

# Open files using GeoPandas and Pandas
data_map_df = gpd.read_file(covid_map)[['OGF_ID', 'PHU_NAME_E', 'geometry']]
covid_data_df = pd.DataFrame.from_dict(input_data)

# Fetch data for the latest date and merge it to the map
latest_covid_data_df = covid_data_df[covid_data_df['FILE_DATE'] == "20200410"]
merged = data_map_df.merge(latest_covid_data_df, left_on="PHU_NAME_E", right_on="PHU_NAME")

#Read data to json.
merged_json = json.loads(merged.to_json())

#Convert to String like object. 
json_data = json.dumps(merged_json)

#Define function that returns json_data for year selected by user.    
def json_data_mapping(date):
    dt = date
    print(str(dt))
    print(covid_data_df['FILE_DATE'] == str(dt))
    c19df_dt = covid_data_df[covid_data_df['FILE_DATE'] == str(dt)]
    merged = data_map_df.merge(latest_covid_data_df, left_on="PHU_NAME_E", right_on="PHU_NAME")
    #merged.fillna('No data', inplace = True)
    merged_json = json.loads(merged.to_json())
    json_data = json.dumps(merged_json)
    return json_data

#Define a sequential multi-hue color palette.
palette = brewer['RdYlGn'][8]

#Add hover tool
hover = HoverTool(tooltips = [ ('Public Health Unit','@PHU_NAME'),('Active Cases No: ', '@ACTIVE_CASES')])

# GeoData source
geosource = GeoJSONDataSource(geojson = json_data)

#Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors. Input nan_color.
color_mapper = LinearColorMapper(palette = palette, low = 0, high = 40, nan_color = '#d9d9d9')

# Function that will generate fill_color dictionary
colour_filling = {'field' :'ACTIVE_CASES', 'transform' : color_mapper}

#Define custom tick labels for color bar.
tick_labels = {'0': '0%', '5': '5%', '10':'10%', '15':'15%', '20':'20%', '25':'25%', '30':'30%','35':'35%', '40': '>40%'}

# Function that will re-draw the map with data category that was selected by the user
def map_redraw(choice):
    fill_dict = {}
    if choice == 0:
        # Draw the map with Active Cases
        fill_dict.update({'field' :'ACTIVE_CASES', 'transform' : color_mapper})
    elif choice == 1:
        # Draw the map with Resolved Cases
        fill_dict.update({'field' :'RESOLVED_CASES', 'transform' : color_mapper})
    else:
        # Draw the map with Deaths
        fill_dict.update({'field' :'DEATHS', 'transform' : color_mapper})
    return fill_dict

#Create color bar. 
color_bar = ColorBar(color_mapper=color_mapper, label_standoff=8,width = 500, height = 20,
                     border_line_color=None,location = (0,0), orientation = 'horizontal', major_label_overrides = tick_labels)

# Draw map
data_map = figure(title="Active COVID cases by Public Health Unit in Ontario", plot_height = 600 , plot_width = 950, toolbar_location = None, tools=[hover], output_backend="webgl")
data_map.patches(source=geosource, line_color = 'black', fill_color = colour_filling, line_width = 0.25, fill_alpha = 1)

# Update the data that is displayed
def json_data_update(attr, old, new):
    geosource.geojson = json_data_mapping(data_slider.value)
    data_map.patches(source=geosource, line_color = 'black', fill_color = colour_filling, line_width = 0.25, fill_alpha = 1)

def update(attr, old, new):
    # Adjust map by using radio buttons
    colour_fillings = map_redraw(new)
    categories = ["Active COVID cases", "Resolved COVID cases", "Deaths due to COVID"]
    data_map.patches(source=geosource, line_color = 'black', fill_color = colour_fillings, line_width = 0.25, fill_alpha = 1)
    data_map.title.text = categories[new] + ' by Public Health Unit in Ontario'

#Specify figure layout.
data_map.add_layout(color_bar, 'below')
button_group = RadioButtonGroup(labels=["Active Cases", "Resolved Cases", "Deaths"], active=0)
button_group.on_change('active', lambda attr, old, new: update(attr, old, new))
# Slider tool for selecting dates
data_slider = Slider(title = 'Date (YYYYMMDD)',start = 20200410, end = 20201224, step = 1, value = 20200410)
data_slider.on_change('value', json_data_update)
# Output final map
project_layout = column(data_map,widgetbox(button_group, data_slider))
curdoc().add_root(project_layout)
