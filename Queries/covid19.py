'''
 * The MIT License (MIT)
 * Copyright (c) Arturo Rodriguez All rights reserved.
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 * The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 '''

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

import scipy.optimize as spo

import covid19.data as cov19

# Get the data processes by the Pipeline and wrangle to fit the visual needs
def getData(country_name, state_name, type_name, cohort_name, day_count_value):

    cov19.Load(False)

    if type_name == 'Statistics' and state_name == 'All':

        ranked_countries = (cov19.all_date[(cov19.all_date['Province/State'] == 'All') & ~(cov19.all_date['Country/Region'] == 'World')] if country_name == 'World' else cov19.all_date[(cov19.all_date['Country/Region'] == country_name)]).copy(deep=True)

        _ranked_countries = ranked_countries.groupby(['Country/Region']) if country_name == 'World' else ranked_countries.groupby(['Province/State'])
        _ranked_countries = _ranked_countries.agg({
            'confirmed': 'last', 
            'confirmed_change': 'last', 
            'recovered': 'last', 
            'recovered_change': 'last', 
            'active': 'last', 
            'active_change': 'last', 
            'death': 'last', 
            'death_change': 'last', 
            'growth': 'last', 
            'growth_5day': 'last',
            'Continent': 'last'
        }).reset_index()
 
        _ranked_countries = _ranked_countries.sort_values(by=['confirmed'], ascending=False)
        df = _ranked_countries[['Continent', 'Country/Region', 'confirmed', 'confirmed_change', 'recovered', 'recovered_change', 'active', 'active_change', 'death', 'death_change', 'growth', 'growth_5day']].copy(deep=True) if country_name == 'World' else _ranked_countries[['Province/State', 'confirmed', 'confirmed_change', 'recovered', 'recovered_change', 'active', 'active_change', 'death', 'death_change', 'growth', 'growth_5day']].copy(deep=True) 
        df[['confirmed', 'confirmed_change', 'death', 'death_change', 'growth', 'growth_5day']] = df[['confirmed', 'confirmed_change', 'death', 'death_change', 'growth', 'growth_5day']].apply(pd.to_numeric)

        def daysCalcCountry(start_idx, x):
            __df = cov19.first_infection[start_idx][(cov19.first_infection[start_idx]['Country/Region'] == x) & (cov19.first_infection[start_idx]['Province/State'] == 'All')]['infection']
            if __df.empty:
                return 0
            else:
                return (datetime.datetime.now() - __df.iloc[0]).days

        def daysCalcState(start_idx, x):
            __df = cov19.first_infection[start_idx][((cov19.first_infection[start_idx]['Country/Region'] == country_name) & (cov19.first_infection[start_idx]['Province/State'] == x))]['infection']
            if __df.empty:
                return 0
            else:
                return (datetime.datetime.now() - __df.iloc[0]).days
 

        def daysCalcCountryProjection(x):
            __df = cov19.all_date[(cov19.all_date['Country/Region'] == x) & (cov19.all_date['Province/State'] == 'All')]
            if __df.empty:
                return 0
            else:
                confirmed_data = __df[__df['confirmed'] > 0]['confirmed']
                n = len(confirmed_data) - 1
                if n > 2:
                    return round(confirmed_data.iloc[n] * confirmed_data.iloc[n] / confirmed_data.iloc[n - 1], 0)
                elif n == -1:
                    return 0
                else:
                    return confirmed_data.iloc[n]

        def daysCalcStateProjection(x):
            __df = cov19.all_date[(cov19.all_date['Country/Region'] == country_name) & (cov19.all_date['Province/State'] == x)]
            if __df.empty:
                return 0
            else: 
                confirmed_data = __df[__df['confirmed'] > 0]['confirmed']
                n = len(confirmed_data) - 1
                if n > 2:
                    return round(confirmed_data.iloc[n] * confirmed_data.iloc[n] / confirmed_data.iloc[n - 1], 0)

        df['Days Infected'] = df['Country/Region'].apply(lambda x: daysCalcCountry(1, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(1, x))

        # df['Days 100'] = df['Country/Region'].apply(lambda x: daysCalcCountry(100, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(100, x))
        # df['Days 200'] = df['Country/Region'].apply(lambda x: daysCalcCountry(200, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(200, x))
        # df['Days 300'] = df['Country/Region'].apply(lambda x: daysCalcCountry(300, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(300, x))
        # df['Days 500'] = df['Country/Region'].apply(lambda x: daysCalcCountry(500, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(500, x))
        # df['Days 750'] = df['Country/Region'].apply(lambda x: daysCalcCountry(750, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(750, x))
        # df['Days 1000'] = df['Country/Region'].apply(lambda x: daysCalcCountry(1000, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(1000, x))

        df['Confirmed t+1'] = df['Country/Region'].apply(daysCalcCountryProjection) if country_name == 'World' else df['Province/State'].apply(daysCalcStateProjection)        
        df = df.rename(columns={'confirmed': 'Confirmed', 'confirmed_change': 'Confirmed Chg', 'recovered': 'Recovered', 'recovered_change': 'Recovered Chg', 'active': 'Active', 'active_change': 'Active Chg' , 'death': 'Dead', 'death_change': 'Dead Chg', 'growth': 'Growth Rate', 'growth_5day': 'Growth 5 Day' })
 
        return df

    elif type_name == 'Day count':
        df = cov19.all_from_0_confirmed[day_count_value]
        if cohort_name == 'Growth Rate':
            df = cov19.all_from_0_growth[day_count_value]
        if cohort_name == 'Dead':
            df = cov19.all_from_0_death[day_count_value]
        if cohort_name == 'Active':
            df = cov19.all_from_0_active[day_count_value]
        if cohort_name == 'Recovered':
            df = cov19.all_from_0_recovered[day_count_value]

        df = df[[col for col in df.columns if '/' not in col]] if country_name == 'World' else df[[col for col in df.columns if (country_name + ' /') in col]]

        ranked_countries = (cov19.all_date[(cov19.all_date['Province/State'] == 'All') & ~(cov19.all_date['Country/Region'] == 'World')] if country_name == 'World' else cov19.all_date[(cov19.all_date['Country/Region'] == country_name)]).copy(deep=True)

        _ranked_countries = ranked_countries.groupby(['Country/Region']) if country_name == 'World' else ranked_countries.groupby(['Province/State'])

        if country_name == 'World':
            _ranked_countries = _ranked_countries.agg({
                'confirmed': 'last', 
                'confirmed_change': 'last', 
                'recovered': 'last', 
                'recovered_change': 'last', 
                'active': 'last', 
                'active_change': 'last', 
                'death': 'last', 
                'death_change': 'last', 
                'growth': 'last', 
                'growth_5day': 'last',
                'Continent': 'last',
            }).reset_index()
        else:
            _ranked_countries = _ranked_countries.agg({
                'confirmed': 'last', 
                'confirmed_change': 'last', 
                'recovered': 'last', 
                'recovered_change': 'last', 
                'active': 'last', 
                'active_change': 'last', 
                'death': 'last', 
                'death_change': 'last', 
                'growth': 'last', 
                'growth_5day': 'last',
                'Continent': 'last',
                'Country/Region': 'last',
            }).reset_index()
 
        ranked_countries = _ranked_countries.sort_values(by=['confirmed'], ascending=False)
        if not country_name == 'World':
            ranked_countries = ranked_countries[~(ranked_countries['Province/State'] == 'All')]

        if cohort_name == 'Confirmed':
            ranked_countries = ranked_countries.sort_values(by=['confirmed'], ascending=False)
            ranked_countries = ranked_countries[ranked_countries['confirmed'] > day_count_value]
        if cohort_name == 'Active':
            ranked_countries = ranked_countries.sort_values(by=['active'], ascending=False)
            ranked_countries = ranked_countries[ranked_countries['active'] > day_count_value]
        if cohort_name == 'Recovered':
            ranked_countries = ranked_countries.sort_values(by=['recovered'], ascending=False)
            ranked_countries = ranked_countries[ranked_countries['recovered'] > day_count_value]
        if cohort_name == 'Dead':
            ranked_countries = ranked_countries.sort_values(by=['death'], ascending=False)
            ranked_countries = ranked_countries[ranked_countries['death'] > day_count_value]
        if cohort_name == 'Growth Rate':
            ranked_countries = ranked_countries.sort_values(by=['growth'], ascending=False)
            ranked_countries = ranked_countries[ranked_countries['growth'] > day_count_value]

        df = df[ranked_countries['Country/Region']]  if country_name == 'World' else df[ranked_countries['Country/Region'] + ' / ' + ranked_countries['Province/State']]
        
        if not country_name == 'World':
            for col in df.columns:
                if ' / ' in col:
                    df = df.rename(columns={col : col.replace(country_name + ' / ', '')})
        df = df.reset_index()
        df['Day Count'] = df['Day Count'].apply(lambda x: str(x.days))
  
        return df
    
    else:
        df = cov19.all_date[(cov19.all_date['Country/Region'] == country_name) & (cov19.all_date['Province/State'] == state_name)]
        df = df[['date', 'confirmed', 'confirmed_change', 'active', 'active_change', 'recovered', 'recovered_change', 'death', 'growth', 'growth_5day']]
 
        return df  

# Transform the retrieved data to a JSON format for the WebAPI
def getJson(country_name, state_name, type_name, cohort_name, _day_count_value):

    day_count_value = int(_day_count_value)
    df = getData(country_name, state_name, type_name, cohort_name, day_count_value)
    df = df.applymap(lambda x: str(x) if isinstance(x, datetime.datetime) else str(x))
    return df.T.to_dict().values()
 
# Get All Timeseries data
def getAllData():
    cov19.Load(False)
    df = cov19.all_date
    df = df.applymap(lambda x: str(x) if isinstance(x, datetime.datetime) else str(x))
    df = df[['date', 'Continent', 'Country/Region', 'Province/State', 'confirmed', 'confirmed_change', 'active', 'active_change', 'recovered', 'recovered_change', 'death', 'death_change', 'growth', 'growth_5day']]
    return df.T.to_dict().values() 

# Get All Timeseries reindexed from the nth day of infection
def getAllDataFromX():
    cov19.Load(False)
    df_0 = cov19.all_from_0

    df = pd.DataFrame()

    for key in df_0:
        _df = df_0[key].copy(deep=True)
        _df['Day Count'] = _df['Day Count'].apply(lambda x: str(x.days))
        _df['testIndex'] = _df['Country/Region'] + _df['Province/State'] + _df['Day Count'].apply(lambda x: str(x)) + str(key)
        _df['Start'] = key
        _df = _df.set_index(['testIndex'])
        df = df.append(_df)
    
    df = df.applymap(lambda x: str(x) if isinstance(x, datetime.datetime) else str(x))
    return df.T.to_dict().values()


# Plotly/Dash code as required by CoFlows
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

            cov19.Load(False)


            # world_population_url = 'http://api.worldbank.org/v2/en/indicator/SP.POP.TOTL?downloadformat=csv'
            world_population_url = '/app/mnt/Files/populations.csv'
            world_population_pd = pd.read_csv(world_population_url)
            print(world_population_pd)

            

            country_region_list = [cty[0] for cty in cov19.all_date[['Country/Region']].drop_duplicates().values.tolist()]
            country_region_list.sort()
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
                            html.H3(id='title', children='COVID-19 Analysis on CoFlows'),
                            html.H4(children='Last Update: ' + last_date.strftime("%Y-%m-%d")),
                            html.Div(id='link_id', children=[ 
                                
                            ]),
                        ],
                    ),

                    html.Div(
                        className='row',
                        style=dict(width='98.5%'),
                        children=[

                            html.Div(
                                className='three columns',
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
                                className='three columns',
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
                                className='three columns',
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
                            
                            html.Div(
                                className='three columns',
                                id='data_type_div',
                                children= [
                                    dcc.Dropdown(
                                        id='data_types',
                                        clearable=False,
                                        options=[
                                            {'label': country, 'value': country} for country in ['Table', 'Chart']
                                        ],
                                        value = 'Table'
                                    )
                                ],
                            )
                        ]
                    ),

                    html.Div(
                        style=dict(width='98.5%', display='none'),
                        id='select_charts_div',
                        className='row',
                        children=[
                            html.Br(),
                            html.Div(
                                className='twelve columns',
                                children=[
                                    dcc.Dropdown(
                                        id='selected_charts',
                                        multi=True,
                                        clearable=False,
                                        options=[],
                                        value=[]
                                    )
                                ]
                            )
                        ]
                    ),

                    # Simple table
                    html.Div(
                        style=dict(width='98.5%', display='none'),
                        className='row',
                        id='table_output_div',
                        children=[
                            html.Br(),
                            dash_table.DataTable(
                                id='table',
                                columns=[],
                                sort_action="native",
                                sort_mode="single",
                                data=[],
                            )
                        ]
                    ),

                    # Simple timeseries chart
                    html.Div(
                        style=dict(width='98.5%', display='none'),
                        className='row',
                        id='timeseries_chart_output_div',
                        children=[
                            html.Br(),
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        className='ten columns',
                                        children=[
                                            dcc.Dropdown(
                                                id='timeseries_chart_selected',
                                                multi=True,
                                                clearable=False,
                                                options=[],
                                                value=[]
                                            )
                                        ]
                                    ),
                                    html.Div(
                                        className='two columns',
                                        children=[
                                            dcc.Dropdown(
                                                id='timeseries_linear_log_control',
                                                multi=False,
                                                clearable=False,
                                                options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                                                value='Linear'
                                            )
                                        ]
                                    )
                                    
                                ]
                            ),
                            html.Br(),
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        className='twelve columns',
                                        children=[
                                            dcc.Graph(
                                                id='timeseries_chart_output',
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    ),

                    # Day count chart
                    html.Div(
                        style=dict(width='98.5%', display='none'),
                        className='row',
                        id='daycount_chart_output_div',
                        children=[
                            html.Br(),
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        className='six columns',
                                        children= [
                                            dcc.Dropdown(
                                                id='daycount_chart_output_control_1',
                                                clearable=False,
                                                options=[{'label': ttype, 'value': ttype} for ttype in ['Confirmed', 'Active', 'Recovered', 'Dead', 'Growth Rate']],
                                                value = 'Confirmed'
                                            )
                                        ],
                                    ),

                                    html.Div(
                                        className='six columns',
                                        children= [
                                            dcc.Dropdown(
                                                id='daycount_chart_output_control_2',
                                                clearable=False,
                                                # options=[{'label': ttype, 'value': ttype} for ttype in [1, 100, 200, 300, 500, 750, 1000]],
                                                options=[{'label': ttype, 'value': ttype} for ttype in [1, 100, 1000]],
                                                # options=[{'label': ttype, 'value': ttype} for ttype in [1]],
                                                value = 1
                                            )
                                        ],
                                    )
                                ]
                            ),
                            html.Br(),
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        className='ten columns',
                                        children=[
                                            dcc.Dropdown(
                                                id='daycount_chart_selected',
                                                multi=True,
                                                clearable=False,
                                                options=[],
                                                value=[]
                                            )
                                        ]
                                    ),
                                    html.Div(
                                        className='two columns',
                                        children=[
                                            dcc.Dropdown(
                                                id='daycount_linear_log_control',
                                                multi=False,
                                                clearable=False,
                                                options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                                                value='Linear'
                                            )
                                        ]
                                    )
                                ]
                            ),
                            html.Br(),
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        className='twelve columns',
                                        children=[
                                            dcc.Graph(
                                                id='daycount_chart_output',
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    ),


                    # Statistics chart
                    html.Div(
                        style=dict(width='98.5%', display='none'),
                        className='row',
                        id='statistics_chart_output_div',
                        children=[
                            html.Br(),
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        className='six columns',
                                        children= [
                                            dcc.Dropdown(
                                                id='statistics_chart_output_control_1',
                                                clearable=False,
                                                options=[{'label': ttype, 'value': ttype} for ttype in ['Confirmed', 'Active', 'Recovered', 'Dead', 'Growth Rate', 'Growth 5 Day', 'Days Infected']],
                                                value = 'Confirmed'
                                            )
                                        ],
                                    ), 

                                    html.Div(
                                        className='six columns',
                                        children= [
                                            dcc.Dropdown(
                                                id='statistics_chart_output_control_2',
                                                clearable=False,
                                                options=[{'label': ttype, 'value': ttype} for ttype in ['Confirmed', 'Active', 'Recovered', 'Dead', 'Growth Rate', 'Growth 5 Day', 'Days Infected']],
                                                value = 'Days Infected'
                                            )
                                        ],
                                    )
                                ]
                            ),
                            html.Br(),
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        className='twelve columns',
                                        children=[
                                            dcc.Dropdown(
                                                id='statistics_chart_selected',
                                                multi=True,
                                                clearable=False,
                                                options=[],
                                                value=[]
                                            )
                                        ]
                                    )
                                ]
                            ),
                            html.Br(),
                            html.Div(
                                className='row',
                                children=[
                                    html.Div(
                                        className='twelve columns',
                                        children=[
                                            dcc.Graph(
                                                id='statistics_chart_output',
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )

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
                    lst = ['Statistics', 'Timeseries', 'Day count']
                    return [ {'label': element, 'value': element} for element in lst ], lst[0]

                else:
                    lst = ['Timeseries']
                    return [ {'label': element, 'value': element} for element in lst ], lst[0]

            @app.callback(
                [
                    Output('data_types', 'options'),
                    Output('data_types', 'value')

                ],
                [
                    Input('types', 'value')
                ]
            )
            def set_data_types(types_name):
                lst = ['Table', 'Chart']
                return [ {'label': element, 'value': element} for element in lst ], lst[0]

            @app.callback(
                Output('link_id', 'children'),
                [
                    Input('countries', 'value'),
                    Input('states', 'value'),
                    Input('types', 'value'),
                    Input('daycount_chart_output_control_1', 'value'),
                    Input('daycount_chart_output_control_2', 'value'),
                    Input('statistics_chart_output_control_1', 'value'),
                    Input('statistics_chart_output_control_2', 'value'),
                    
                ]
            )
            def set_links(country_name, state_name, type_name, cohort_name1, day_count_value1, cohort_name2, day_count_value2):

                link = [
                    html.A('Download JSON Dataset in table below', href='https://app.coflows.com/m/getwb?workbook=c68ca7c8-c9b6-4ded-b25a-2867f10a150a&id=covid19.py&name=getJson&p[0]=' + country_name + '&p[1]=' + state_name + '&p[2]=' + type_name + '&p[3]=' + cohort_name1 + '&p[4]=' + str(day_count_value1), target="_blank") if type_name == 'Day count' else html.A('Download JSON Dataset in table below', href='https://app.coflows.com/m/getwb?workbook=c68ca7c8-c9b6-4ded-b25a-2867f10a150a&id=covid19.py&name=getJson&p[0]=' + country_name + '&p[1]=' + state_name + '&p[2]=' + type_name + '&p[3]=' + cohort_name2 + '&p[4]=' + str(day_count_value2 if isinstance(day_count_value2, int) else 1), target="_blank"),
                    html.Br(),
                    html.A('Download JSON All Timeseries', href='https://app.coflows.com/m/getwb?workbook=c68ca7c8-c9b6-4ded-b25a-2867f10a150a&id=covid19.py&name=getAllData', target="_blank"),
                    html.Br(),
                    html.A('Download JSON All Timeseries From X', href='https://app.coflows.com/m/getwb?workbook=c68ca7c8-c9b6-4ded-b25a-2867f10a150a&id=covid19.py&name=getAllDataFromX', target="_blank")
                ]
                return link

            @app.callback(
                [
                    Output('table_output_div', 'style'),
                    Output('table', 'columns'),
                    Output('table', 'data'),
                ],
                [
                    Input('countries', 'value'),
                    Input('states', 'value'),
                    Input('types', 'value'),
                    Input('data_types', 'value'),
                ]
            )
            def set_table(country_name, state_name, type_name, data_type):

                
                if data_type == 'Table':
                    df = getData(country_name, state_name, type_name, '', 1)
                
                    return [
                        dict(width='98.5%'),
                        [{"name": i, "id": i} for i in df.columns],
                        df.to_dict('records')
                    ]
                else:
                    return [
                        dict(width='98.5%', display='none'),
                        [],
                        []
                    ]
                

                
            @app.callback(
                [
                    Output('timeseries_chart_output_div', 'style'),
                    Output('timeseries_chart_output', 'figure'),
                ],
                [
                    Input('countries', 'value'),
                    Input('states', 'value'),
                    Input('types', 'value'),
                    Input('data_types', 'value'),
                    Input('timeseries_chart_selected', 'value'),
                    Input('timeseries_linear_log_control', 'value'),
                ]
            )
            def set_timeseris_chart(country_name, state_name, type_name, data_type, selected_charts, linear_log_control):
                if data_type == 'Chart':
                    
                    xaxis_type = 'Linear'
                    yaxis_type = linear_log_control

                    x_axis = {}
                    y_axis = {}
                    charts = []

                    if type_name == 'Timeseries' and len(selected_charts) > 0:
                        df = getData(country_name, state_name, type_name, '', 1)
                
                        x_axis = df['date']
                        y_axis = df[selected_charts]
                        
                        for col in selected_charts:

                            if not col == 'Day Count':

                                y_axis = df[col]

                                charts.append(dict(
                                        name=col,
                                        x = x_axis,
                                        y = y_axis,
                                        mode='lines',
                                    ))

                        return [
                            dict(width='98.5%'),
                            dict(
                                data = charts,
                                layout = dict(
                                    xaxis={
                                        'zeroline': False,
                                        'tickmode': 'array',
                                        'tickvals': x_axis,
                                    },
                                    yaxis={
                                        'title': 'Title',
                                        'type': 'linear' if yaxis_type == 'Linear' else 'log',
                                        
                                    },
                                    margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
                                    hovermode='closest',
                                    height=800,
                                    legend = dict(
                                        orientation = 'h'
                                    )
                                )
                            )
                        ]
            
                return [
                    dict(width='98.5%', display='none'),
                    dict()
                ]

            @app.callback(
                [
                    Output('timeseries_chart_selected', 'options'),
                    Output('timeseries_chart_selected', 'value'),
                ],
                [
                    Input('countries', 'value'),
                    Input('states', 'value'),
                    Input('types', 'value'),
                    Input('data_types', 'value'),
                ]
            )
            def set_timeseris_chart_select(country_name, state_name, type_name, data_type):

                if type_name == 'Timeseries' and data_type == 'Chart':
                    df = getData(country_name, state_name, type_name, '', 1)
                    cols = [ val for val in df.columns if not val == 'date']

                    return [
                        [{'label': val, 'value': val} for val in cols],
                        [cols[0]]
                    ]

                else:
                    return [
                        [],
                        []
                    ]

            @app.callback(
                [
                    Output('daycount_chart_output_div', 'style'),
                    Output('daycount_chart_output', 'figure'),
                ],
                [
                    Input('countries', 'value'),
                    Input('states', 'value'),
                    Input('types', 'value'),
                    Input('daycount_chart_output_control_1', 'value'),
                    Input('daycount_chart_output_control_2', 'value'),
                    Input('data_types', 'value'),
                    Input('daycount_chart_selected', 'value'),
                    Input('daycount_linear_log_control', 'value'),
                ]
            )
            def set_daycount_output_chart(country_name, state_name, type_name, cohort_name, day_count_value, data_type, selected_charts, linear_log_control):

                if data_type == 'Chart':
                    xaxis_type = 'Linear'
                    yaxis_type = linear_log_control

                    x_axis = {}
                    y_axis = {}
                    charts = []

                    if type_name == 'Day count' and len(selected_charts) > 0:

                        df = getData(country_name, state_name, type_name, cohort_name, day_count_value)

                        if 'Day Count' in df:

                            x_axis = df['Day Count']

                            df = df[selected_charts]
                            

                            for col in df.columns:

                                if not col == 'Day Count':

                                    y_axis = df[col]

                                    charts.append(dict(
                                            name=col,
                                            x = x_axis,
                                            y = y_axis,
                                            mode='lines',
                                        ))

                            return [
                                dict(width='98.5%'),
                                dict(
                                    data = charts,
                                    layout = dict(
                                        xaxis={
                                            'zeroline': False,
                                            'tickmode': 'array',
                                            'tickvals': x_axis,
                                        },
                                        yaxis={
                                            'title': 'Title',
                                            'type': 'linear' if yaxis_type == 'Linear' else 'log',
                                            
                                        },
                                        margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
                                        hovermode='closest',
                                        height=800,
                                        legend = dict(
                                            orientation = 'h'
                                        )
                                    )
                                )
                            ]
                return [
                    dict(width='98.5%', display='none'),
                    dict()
                ]

            @app.callback(
                [
                    Output('daycount_chart_selected', 'options'),
                    Output('daycount_chart_selected', 'value'),
                ],
                [
                    Input('countries', 'value'),
                    Input('states', 'value'),
                    Input('types', 'value'),
                    Input('daycount_chart_output_control_1', 'value'),
                    Input('daycount_chart_output_control_2', 'value'),
                    Input('data_types', 'value'),
                ]
            )
            def set_daycount_chart_select(country_name, state_name, type_name, cohort_name, day_count_value, data_type):

                if type_name == 'Day count' and data_type == 'Chart':
                    df = getData(country_name, state_name, type_name, cohort_name, day_count_value)
                    cols = [ val for val in df.columns if not val == 'Day Count']

                    return [
                        [{'label': val, 'value': val} for val in cols],
                        [cols[i] for i in range(0, 10)] if len(cols) >= 10 else cols
                    ]

                else:
                    return [
                        [],
                        []
                    ]

            @app.callback(
                [
                    Output('statistics_chart_output_div', 'style'),
                    Output('statistics_chart_output', 'figure'),
                ],
                [
                    Input('countries', 'value'),
                    Input('states', 'value'),
                    Input('types', 'value'),
                    Input('statistics_chart_output_control_1', 'value'),
                    Input('statistics_chart_output_control_2', 'value'),
                    Input('data_types', 'value'),
                    Input('statistics_chart_selected', 'value')
                ]
            )
            def set_statistics_output_chart(country_name, state_name, type_name, cohort_name, day_count_value, data_type, selected_charts):

                if data_type == 'Chart':
                    xaxis_type = 'Linear'
                    yaxis_type = 'log'

                    x_axis = {}
                    y_axis = {}
                    charts = []

                    if type_name == 'Statistics' and len(selected_charts) > 0:
                        df = getData(country_name, state_name, type_name, cohort_name, day_count_value)

                        region_type = 'Country/Region' if 'Country/Region' in df else 'Province/State'

                        for val in selected_charts:
                            y_axis = df[df[region_type] == val][cohort_name]
                            x_axis = df[df[region_type] == val][day_count_value]
                            charts.append(dict(
                                    name=val,
                                    x = x_axis,
                                    y = y_axis,
                                    text=df[df[region_type] == val][region_type],
                                    mode='markers+text',
                                    marker={
                                        'size': 20,
                                        'opacity': 0.5,
                                        'line': {'width': 0.5, 'color': 'white'}
                                    }

                                ))

                        
                        y_axis = df[~(df[region_type].isin(selected_charts))][cohort_name]
                        x_axis = df[~(df[region_type].isin(selected_charts))][day_count_value]
                        charts.append(dict(
                                name='others',
                                x = x_axis,
                                y = y_axis,
                                text=df[~(df[region_type].isin(selected_charts))][region_type],
                                mode='markers',
                                marker={
                                    'size': 10,
                                    'opacity': 0.5,
                                    'line': {'width': 0.5, 'color': 'white'}
                                }

                            ))

                        x_axis = df[day_count_value]
 
                        return [
                            dict(width='98.5%'),
                            dict(
                                data = charts,
                                layout = dict(
                                    xaxis={
                                        'title': day_count_value,
                                        'zeroline': False,
                                        'tickmode': 'array',
                                        'tickvals': x_axis,
                                        'type': 'linear' if day_count_value == 'Day Count' else 'log'
                                    },
                                    yaxis={
                                        'title': cohort_name,
                                        'type': 'linear' if cohort_name == 'Day Count' else 'log'
                                        
                                    },
                                    margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
                                    hovermode='closest',
                                    height=800,
                                    legend = dict(
                                        orientation = 'h'
                                    )
                                )
                            )
                        ]
                return [
                    dict(width='98.5%', display='none'),
                    dict()
                ]

            @app.callback(
                [
                    Output('statistics_chart_selected', 'options'),
                    Output('statistics_chart_selected', 'value'),
                ],
                [
                    Input('countries', 'value'),
                    Input('states', 'value'),
                    Input('types', 'value'),
                    Input('statistics_chart_output_control_1', 'value'),
                    Input('statistics_chart_output_control_2', 'value'),
                    Input('data_types', 'value'),
                ]
            )
            def set_statistics_chart_select(country_name, state_name, type_name, cohort_name, day_count_value, data_type):

                if type_name == 'Statistics' and data_type == 'Chart':
                    df = getData(country_name, state_name, type_name, cohort_name, day_count_value)

                    cols = [ val for val in df['Country/Region'] if not val == 'Day Count'] if 'Country/Region' in df else [ val for val in df['Province/State'] if not val == 'Day Count']

                    return [
                        [{'label': val, 'value': val} for val in cols],
                        [cols[i] for i in range(0, 10)] if 'Country/Region' in df else cols
                    ]

                else:
                    return [
                        [],
                        []
                    ]



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

  
    run(8080, '/charts/dash/') 
 



