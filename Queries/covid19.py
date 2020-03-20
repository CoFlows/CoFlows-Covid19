import numpy as np
import pandas as pd

import dash
import dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

import pathlib

import requests
from flask import request
import time
import threading

import logging

import json
import datetime
from datetime import datetime as dt
import time
import math

import covid19.data as cov19

# pd.set_option('display.max_columns', 500)


dash_init = True
__assetsFolder = '/app/mnt/Files/assets'

def run(port, path):

    global dash_init, __assetsFolder
    if dash_init:
        dash_init = False

        def inner():

            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
 
            # shutdown existing dash 
            try:
                requests.get(url = 'http://localhost:' + str(port) + path + 'shutdown')
                time.sleep(5)
                # print('done waiting...')
            except:
                pass

            app = dash.Dash(
               __name__, 
               meta_tags=[{"name": "viewport", "content": "width=device-width"}], 
               url_base_pathname = path,
               assets_folder=__assetsFolder
            )

            app.url_base_pathname = path

            cov19.Load()


            # world_population_url = 'http://api.worldbank.org/v2/en/indicator/SP.POP.TOTL?downloadformat=csv'
            world_population_url = '/app/mnt/Files/populations.csv'
            world_population_pd = pd.read_csv(world_population_url)
            print(world_population_pd)

            

            country_region_list = [cty[0] for cty in cov19.all_date[['Country/Region']].drop_duplicates().values.tolist()]
            country_region_list.sort()
            # country_region_list.insert(0, 'World')
            province_state_pd = cov19.all_date[['Country/Region', 'Province/State']].drop_duplicates()
            print('------------------------')
            print(world_population_pd[world_population_pd['Country'].isin(country_region_list)])


            country_name = 'World'

            last_date = cov19.all_date[(cov19.all_date['Country/Region'] == country_name) & (cov19.all_date['Province/State'] == 'All')]['date'].max()

            app.layout = html.Div(
                className='row',
                children=[
                    dcc.Location(id='url', refresh=False),
                    html.Div(
                        id='title_div',
                        children= [
                            html.H3(id='title', children='Covid 19'),
                        ],
                    ),

                    html.Div(
                        className='four columns',
                        children= [
                            dcc.Dropdown(
                                id='countries',
                                clearable=False,
                                options=[
                                    {'label': country, 'value': country} for country in country_region_list
                                ],
                                value = country_name
                            )
                        ],
                    ),

                    html.Div(
                        className='four columns',
                        id='states_div',
                        children= [
                            dcc.Dropdown(
                                id='states',
                                clearable=False,
                                options=[
                                ],
                                value = ''
                            )
                        ],
                    ),

                    html.Div(
                        className='four columns',
                        id='type_div',
                        children= [
                            dcc.Dropdown(
                                id='types',
                                clearable=False,
                                options=[],
                                value = ''
                            )
                        ],
                    ),
                    html.Br(),

                    html.Div(
                        style=dict(width='98.5%', display='none'),
                        id='subcontrols_div',
                        children=[
                            html.Div(
                                className='six columns',
                                # id='states_div',
                                children= [
                                    dcc.Dropdown(
                                        id='cohort',
                                        clearable=False,
                                        options=[{'label': ttype, 'value': ttype} for ttype in ['Confirmed', 'Active', 'Dead']],
                                        value = 'Confirmed'
                                    )
                                ],
                            ),

                            html.Div(
                                className='six columns',
                                # id='type_div',
                                children= [
                                    dcc.Dropdown(
                                        id='day_count',
                                        clearable=False,
                                        options=[{'label': ttype, 'value': ttype} for ttype in [1, 100, 200, 300, 500, 750, 1000]],
                                        value = 1
                                    )
                                ],
                            ),
                        ]
                    ),
                    
                    html.Div(
                        style=dict(width='98%'),
                        id='table_div',
                        children=[]
                    )
                ]
            )

            @app.callback(
                Output('subcontrols_div', 'style'),
                [
                    Input('types', 'value')
                ]
            )
            def set_subcontrols(ttype):
                if ttype == 'Day count':
                    return dict(width='98.5%')
                else:
                    return dict(width='98.5%', display='none')

            @app.callback(
                [
                    Output('states', 'options'),
                    Output('states', 'value')

                ],
                [
                    Input('countries', 'value')
                ]
            )
            def set_states(country_name):
                lst = ['All'] if country_name == 'World' else province_state_pd[province_state_pd['Country/Region'] == country_name]['Province/State'].values.tolist()
                lst.sort()
                return [ {'label': country, 'value': country} for country in lst ], 'All'


            @app.callback(
                [
                    Output('types', 'options'),
                    Output('types', 'value')

                ],
                [
                    Input('countries', 'value'),
                    Input('states', 'value')
                ]
            )
            def set_types(country_name, state_name):
                if country_name == 'World':
                    lst = ['Statistics', 'Timeseries', 'Day count']
                    return [ {'label': element, 'value': element} for element in lst ], lst[0]
                
                elif state_name == 'All':
                    lst = ['Statistics', 'Timeseries']
                    return [ {'label': element, 'value': element} for element in lst ], lst[0]

                else:
                    lst = ['Timeseries']
                    return [ {'label': element, 'value': element} for element in lst ], lst[0]
                

            @app.callback(
                Output('table_div', 'children'),
                [
                    Input('countries', 'value'),
                    Input('states', 'value'),
                    Input('types', 'value'),
                    Input('cohort', 'value'),
                    Input('day_count', 'value'),
                ]
            )
            def set_table(country_name, state_name, type_name, cohort_name, day_count_value):

                if type_name == 'Statistics' and state_name == 'All':
                    # ranked_countries = cov19.all_date[(cov19.all_date['Province/State'] == 'All') & ~(cov19.all_date['Country/Region'] == 'World') & (cov19.all_date['date'] == last_date)] if country_name == 'World' else cov19.all_date[(cov19.all_date['Province/State'] == state_name) & (cov19.all_date['Country/Region'] == country_name) & (cov19.all_date['date'] == last_date)]
                    ranked_countries = cov19.all_date[(cov19.all_date['Province/State'] == 'All') & ~(cov19.all_date['Country/Region'] == 'World') & (cov19.all_date['date'] == last_date)] if country_name == 'World' else cov19.all_date[(cov19.all_date['Country/Region'] == country_name) & (cov19.all_date['date'] == last_date)]
                    ranked_countries = ranked_countries.sort_values(by=['confirmed', 'active'], ascending=False)
                    df = ranked_countries[['Country/Region', 'confirmed', 'confirmed_change', 'active', 'active_change', 'death', 'death_change']].copy(deep=True) if country_name == 'World' else ranked_countries[['Province/State', 'confirmed', 'confirmed_change', 'active', 'active_change', 'death', 'death_change']].copy(deep=True) 

                    df[['confirmed', 'confirmed_change', 'active', 'active_change', 'death', 'death_change']] = df[['confirmed', 'confirmed_change', 'active', 'active_change', 'death', 'death_change']].apply(pd.to_numeric)
                    df['recovered'] = round(100 * (df['confirmed'] - df['active'] - df['death']) / df['confirmed'], 2)
                    
                    start_idx = 1
                    df['Days Infected'] = df['Country/Region'].apply(lambda x: (datetime.datetime.now() - cov19.first_infection[start_idx][(cov19.first_infection[start_idx]['Country/Region'] == x) & (cov19.first_infection[start_idx]['Province/State'] == 'All')]['infection'].iloc[0]).days) if country_name == 'World' else df['Province/State'].apply(lambda x: (datetime.datetime.now() - cov19.first_infection[start_idx][(cov19.first_infection[start_idx]['Province/State'] == x)]['infection'].iloc[0]).days)

                    df = df.rename(columns={'confirmed': 'Confirmed', 'confirmed_change': 'Confirmed Chg' , 'active': 'Active', 'active_change': 'Active Chg', 'death': 'Dead', 'death_change': 'Dead Chg', 'recovered': 'Recovered %'})
                    


                    
                    return html.Div(
                                    dash_table.DataTable(
                                        id='table',
                                        columns=[{"name": i, "id": i} for i in df.columns],
                                        sort_action="native",
                                        sort_mode="single",
                                        data=df.to_dict('records'),
                                    )
                                )
                elif type_name == 'Day count':
                    df = cov19.all_from_0_confirmed[day_count_value]
                    if cohort_name == 'Active':
                        df = cov19.all_from_0_active[day_count_value]
                    if cohort_name == 'Dead':
                        df = cov19.all_from_0_death[day_count_value]
                        
                    
                    df = df[[col for col in df.columns if '/' not in col]]

                    ranked_countries = cov19.all_date[(cov19.all_date['Province/State'] == 'All') & ~(cov19.all_date['Country/Region'] == 'World') & (cov19.all_date['date'] == last_date)]
                    if cohort_name == 'Confirmed':
                        ranked_countries = ranked_countries.sort_values(by=['confirmed'], ascending=False)
                        ranked_countries = ranked_countries[ranked_countries['confirmed'] > day_count_value]
                    if cohort_name == 'Active':
                        ranked_countries = ranked_countries.sort_values(by=['active'], ascending=False)
                        ranked_countries = ranked_countries[ranked_countries['active'] > day_count_value]
                    if cohort_name == 'Dead':
                        ranked_countries = ranked_countries.sort_values(by=['death'], ascending=False)
                        ranked_countries = ranked_countries[ranked_countries['death'] > day_count_value]

                    df = df[ranked_countries['Country/Region']]
                    df = df.reset_index()
                    df['Day Count'] = df['Day Count'].apply(lambda x: str(x.days) + ' days')

                    return html.Div(
                                    dash_table.DataTable(
                                        id='table',
                                        columns=[{"name": i, "id": i} for i in df.columns],
                                        data=df.to_dict('records'),
                                    )
                                )

                else:
                    df = cov19.all_date[(cov19.all_date['Country/Region'] == country_name) & (cov19.all_date['Province/State'] == state_name)]
                    df = df[['date', 'confirmed', 'confirmed_change', 'active', 'recovered', 'death']]
                    
                    return html.Div(
                                    dash_table.DataTable(
                                        id='table',
                                        columns=[{"name": i, "id": i} for i in df.columns],
                                        data=df.to_dict('records'),
                                    )
                                )


            # necessary to shutdown server incase the code change
            @app.server.route(path + 'shutdown', methods=['GET'])
            def shutdown():
                # print('DASH stopping')
                try:
                    global __union_change, __union_change_0, __union_change_0_confirmed, __union_change_0_active, __union_change_0_death, __union_change_0_recovered, __first_infection, __first_death, __first_recovered, __first_dates
                    del __union_change, __union_change_0, __union_change_0_confirmed, __union_change_0_active, __union_change_0_death, __union_change_0_recovered, __first_infection, __first_death, __first_recovered, __first_dates
                except Exception as e: 
                    pass

                func = request.environ.get('werkzeug.server.shutdown')
                if func is None:
                    raise RuntimeError('Not running with the Werkzeug Server')
                func()

            return app.run_server(port=port, debug=False, threaded=True)

        
        server = threading.Thread(target = inner)
        server.start()

        daemon = threading.Thread(target = cacheDaemon)
        daemon.start()


if __name__ == '__main__': 
   run(8080, '/charts/dash/')