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

# pd.set_option('display.max_columns', 500)

def getData(country_name, state_name, type_name, cohort_name, day_count_value):
    cov19.Load()

    last_date = cov19.all_date[(cov19.all_date['Country/Region'] == country_name) & (cov19.all_date['Province/State'] == state_name)]['date'].max()

    if type_name == 'Statistics' and state_name == 'All':
        # ranked_countries = cov19.all_date[(cov19.all_date['Province/State'] == 'All') & ~(cov19.all_date['Country/Region'] == 'World') & (cov19.all_date['date'] == last_date)] if country_name == 'World' else cov19.all_date[(cov19.all_date['Province/State'] == state_name) & (cov19.all_date['Country/Region'] == country_name) & (cov19.all_date['date'] == last_date)]
        ranked_countries = cov19.all_date[(cov19.all_date['Province/State'] == 'All') & ~(cov19.all_date['Country/Region'] == 'World') & (cov19.all_date['date'] == last_date)] if country_name == 'World' else cov19.all_date[(cov19.all_date['Country/Region'] == country_name) & (cov19.all_date['date'] == last_date)]
        ranked_countries = ranked_countries.sort_values(by=['confirmed', 'active'], ascending=False)
        df = ranked_countries[['Country/Region', 'confirmed', 'confirmed_change', 'active', 'active_change', 'death', 'death_change']].copy(deep=True) if country_name == 'World' else ranked_countries[['Province/State', 'confirmed', 'confirmed_change', 'active', 'active_change', 'death', 'death_change']].copy(deep=True) 

        df[['confirmed', 'confirmed_change', 'active', 'active_change', 'death', 'death_change']] = df[['confirmed', 'confirmed_change', 'active', 'active_change', 'death', 'death_change']].apply(pd.to_numeric)
        df['recovered'] = round(100 * (df['confirmed'] - df['active'] - df['death']) / df['confirmed'], 2)

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


        def daysCalcCountryTest(x):
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

        def daysCalcStateTest(x):
            __df = cov19.all_date[(cov19.all_date['Country/Region'] == country_name) & (cov19.all_date['Province/State'] == x)]
            if __df.empty:
                return 0
            else:
                confirmed_data = __df[__df['confirmed'] > 0]['confirmed']
                n = len(confirmed_data) - 1
                if n > 2:
                    return round(confirmed_data.iloc[n] * confirmed_data.iloc[n] / confirmed_data.iloc[n - 1], 0)
        
        # df['Days Infected'] = df['Country/Region'].apply(lambda x: (datetime.datetime.now() - cov19.first_infection[start_idx][(cov19.first_infection[start_idx]['Country/Region'] == x) & (cov19.first_infection[start_idx]['Province/State'] == 'All')]['infection'].iloc[0]).days) if country_name == 'World' else df['Province/State'].apply(lambda x: (datetime.datetime.now() - cov19.first_infection[start_idx][((cov19.first_infection[start_idx]['Country/Region'] == country_name) & (cov19.first_infection[start_idx]['Province/State'] == x))]['infection'].iloc[0]).days)
        df['Days Infected'] = df['Country/Region'].apply(lambda x: daysCalcCountry(1, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(1, x))

        # df['Days 100'] = df['Country/Region'].apply(lambda x: daysCalcCountry(100, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(100, x))
        # df['Days 200'] = df['Country/Region'].apply(lambda x: daysCalcCountry(200, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(200, x))
        # df['Days 300'] = df['Country/Region'].apply(lambda x: daysCalcCountry(300, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(300, x))
        # df['Days 500'] = df['Country/Region'].apply(lambda x: daysCalcCountry(500, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(500, x))
        # df['Days 750'] = df['Country/Region'].apply(lambda x: daysCalcCountry(750, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(750, x))
        # df['Days 1000'] = df['Country/Region'].apply(lambda x: daysCalcCountry(1000, x)) if country_name == 'World' else df['Province/State'].apply(lambda x: daysCalcState(1000, x))

        df['Confirmed t+1'] = df['Country/Region'].apply(daysCalcCountryTest) if country_name == 'World' else df['Province/State'].apply(daysCalcStateTest)
        
        df = df.rename(columns={'confirmed': 'Confirmed', 'confirmed_change': 'Confirmed Chg' , 'active': 'Active', 'active_change': 'Active Chg', 'death': 'Dead', 'death_change': 'Dead Chg', 'recovered': 'Recovered %'})
        
        return df
                    
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
        df['Day Count'] = df['Day Count'].apply(lambda x: str(x.days))

        return df

    else:
        df = cov19.all_date[(cov19.all_date['Country/Region'] == country_name) & (cov19.all_date['Province/State'] == state_name)]
        df = df[['date', 'confirmed', 'confirmed_change', 'active', 'recovered', 'death']]

        return df

def getJson(country_name, state_name, type_name, cohort_name, _day_count_value):

    day_count_value = int(_day_count_value)
    df = getData(country_name, state_name, type_name, cohort_name, day_count_value)
    df = df.applymap(lambda x: str(x) if isinstance(x, datetime.datetime) else str(x))
    return df.T.to_dict().values()

def getAllData():
    cov19.Load()
    df = cov19.all_date
    df = df.applymap(lambda x: str(x) if isinstance(x, datetime.datetime) else str(x))
    df = df[['date', 'Country/Region', 'Province/State', 'confirmed', 'confirmed_change', 'active', 'active_change', 'recovered', 'recovered_change', 'death', 'death_change']]
    return df.T.to_dict().values()


def getAllDataFromX():
    cov19.Load()
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
                            html.H3(id='title', children='Covid 19 @ ' + last_date.strftime("%Y-%m-%d")),
                            html.Div(id='link_id', children=[ 
                                
                            ]),
                            # html.Div( ])
                        ],
                    ),

                    html.Div(
                        className='row',
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
                    ]),

                    html.Br(),
                    html.Div(
                        style=dict(width='98.5%', display='none'),
                        id='subcontrols_div',
                        className='row',
                        children=[
                            html.Div(
                                className='six columns',
                                children= [
                                    dcc.Dropdown(
                                        id='subcontrol_1',
                                        clearable=False,
                                        options=[{'label': ttype, 'value': ttype} for ttype in ['Confirmed', 'Active', 'Dead']],
                                        value = 'Confirmed'
                                    )
                                ],
                            ),

                            html.Div(
                                className='six columns',
                                children= [
                                    dcc.Dropdown(
                                        id='subcontrol_2',
                                        clearable=False,
                                        options=[{'label': ttype, 'value': ttype} for ttype in [1, 100, 200, 300, 500, 750, 1000]],
                                        value = 1
                                    )
                                ],
                            ),
                        ]
                    ),

                    html.Div(
                        style=dict(width='98.5%', display='none'),
                        # style=dict(width='98.5%'), 
                        id='select_charts_div',
                        className='row',
                        children=[
                            html.Br(),
                            html.Div(
                                # className='ten columns',
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
                            ),

                            html.Div(
                                className='two columns',
                                style=dict(width='98.5%', display='none'),
                                children=[
                                    dcc.RadioItems(
                                        id='linear_log_control',
                                        options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                                        value='Linear',
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ]
                            )

                            
                        ]
                    ),

                    html.Br(),

                    html.Div(
                        style=dict(width='98%'),
                        className='row',
                        id='output_div',
                        children=[]
                    )
                ]
            )

            @app.callback(
                [
                    Output('subcontrols_div', 'style'),
                    Output('subcontrol_1', 'options'),
                    Output('subcontrol_1', 'value'),
                    Output('subcontrol_2', 'options'),
                    Output('subcontrol_2', 'value')
                ],
                [
                    Input('types', 'value'),
                    Input('data_types', 'value')
                ]
            )
            def set_subcontrols(ttype, data_type):
                if ttype == 'Day count':
                    return [
                        # dict(width='98.5%'), 
                        # dict(width='99.5%'), 
                        dict(width='100%'), 
                        [{'label': ttype, 'value': ttype} for ttype in ['Confirmed', 'Active', 'Dead']], 
                        'Confirmed',
                        [{'label': ttype, 'value': ttype} for ttype in [1, 100, 200, 300, 500, 750, 1000]],
                        1
                    ]
                elif ttype == 'Statistics' and data_type == 'Chart':
                    return [
                        # dict(width='98.5%'), 
                        # dict(width='99.5%'), 
                        dict(width='100%'), 
                        [{'label': ttype, 'value': ttype} for ttype in ['Confirmed', 'Active', 'Dead', 'Days Infected']], 
                        'Confirmed',
                        [{'label': ttype, 'value': ttype} for ttype in ['Confirmed', 'Active', 'Dead', 'Days Infected']], 
                        'Days Infected'
                    ]
                else:
                    return [
                        dict(width='98.5%', display='none'),
                        [{'label': ttype, 'value': ttype} for ttype in ['Confirmed', 'Active', 'Dead']], 
                        'Confirmed',
                        [{'label': ttype, 'value': ttype} for ttype in [1, 100, 200, 300, 500, 750, 1000]],
                        1
                    ]

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
                [
                    Output('data_types', 'options'),
                    Output('data_types', 'value')

                ],
                [
                    Input('types', 'value')
                ]
            )
            def set_types(types_name):
                # if types_name == 'Timeseries' or types_name == 'Day count':
                lst = ['Table', 'Chart']
                return [ {'label': element, 'value': element} for element in lst ], lst[0]

                # else:
                #     lst = ['Table']
                #     return [ {'label': element, 'value': element} for element in lst ], lst[0]


            @app.callback(
                [
                    Output('select_charts_div', 'style'),
                    Output('selected_charts', 'options'),
                    Output('selected_charts', 'value'),
                ],
                [
                    Input('countries', 'value'),
                    Input('states', 'value'),
                    Input('types', 'value'),
                    Input('subcontrol_1', 'value'),
                    Input('subcontrol_2', 'value'),
                    Input('data_types', 'value'),
                ]
            )
            def set_output(country_name, state_name, type_name, cohort_name, day_count_value, data_type):

                if type_name == 'Day count' and data_type == 'Chart':
                    df = getData(country_name, state_name, type_name, cohort_name, day_count_value)
                    cols = [ val for val in df.columns if not val == 'Day Count']

                    return [
                        dict(width='98.5%'),
                        [{'label': val, 'value': val} for val in cols],
                        [cols[i] for i in range(0, 10)]
                    ]
                elif type_name == 'Timeseries' and data_type == 'Chart':
                    df = getData(country_name, state_name, type_name, cohort_name, day_count_value)


                    cols = [ val for val in df.columns if not val == 'date']

                    return [
                        dict(width='98.5%'),
                        [{'label': val, 'value': val} for val in cols],
                        [cols[0]]
                    ]

                elif type_name == 'Statistics' and data_type == 'Chart':
                    df = getData(country_name, state_name, type_name, cohort_name, day_count_value)


                    cols = [ val for val in df['Country/Region'] if not val == 'Day Count']

                    return [
                        dict(width='98.5%'),
                        [{'label': val, 'value': val} for val in cols],
                        
                        [cols[i] for i in range(0, 20)]
                    ]
                else:
                    return [
                        dict(width='98.5%', display='none'),
                        [],
                        []
                    ]
                

            @app.callback(
                [
                    Output('output_div', 'children'),
                    Output('link_id', 'children')
                ],
                [
                    Input('countries', 'value'),
                    Input('states', 'value'),
                    Input('types', 'value'),
                    Input('subcontrol_1', 'value'),
                    Input('subcontrol_2', 'value'),
                    Input('data_types', 'value'),
                    Input('selected_charts', 'value'),
                    Input('linear_log_control', 'value'),
                ]
            )
            def set_output(country_name, state_name, type_name, cohort_name, day_count_value, data_type, selected_charts, linear_log_control):

                link = [
                    html.A('Download JSON Dataset in table below', href='http://coflows.quant.app/m/getwb?workbook=c68ca7c8-c9b6-4ded-b25a-2867f10a150a&id=covid19.py&name=getJson&p[0]=' + country_name + '&p[1]=' + state_name + '&p[2]=' + type_name + '&p[3]=' + cohort_name + '&p[4]=' + str(day_count_value), target="_blank"),
                    html.Br(),
                    html.A('Download JSON All Timeseries', href='http://coflows.quant.app/m/getwb?workbook=c68ca7c8-c9b6-4ded-b25a-2867f10a150a&id=covid19.py&name=getAllData', target="_blank"),
                    html.Br(),
                    html.A('Download JSON All Timeseries From X', href='http://coflows.quant.app/m/getwb?workbook=c68ca7c8-c9b6-4ded-b25a-2867f10a150a&id=covid19.py&name=getAllDataFromX', target="_blank")
                ]

                df = getData(country_name, state_name, type_name, cohort_name, day_count_value)
                

                if data_type == 'Chart':
                    xaxis_type = 'Linear'
                    yaxis_type = linear_log_control

                    x_axis = {}
                    y_axis = {}
                    charts = []

                    if type_name == 'Timeseries' and len(selected_charts) > 0:
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
                                        # line=dict(color='#576D22', width=4)
                                    ))

                        return [
                            html.Div(
                                children=[
                                    html.Br(),

                                    dcc.Graph(
                                        # id='smile',
                                        figure = dict(
                                            data = charts,
                                            layout = dict(
                                                xaxis={
                                                    # 'title': 'Delta',
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
                                    )
                                ]
                            ), 
                            link
                        ]
                    elif 'Day Count' in df:

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
                                        # line=dict(color='#576D22', width=4)
                                    ))

                        return [
                            html.Div(
                                children=[
                                    
                                    html.Br(),
                                    dcc.Graph(
                                        # id='smile',
                                        figure = dict(
                                            data = charts,
                                            layout = dict(
                                                xaxis={
                                                    # 'title': 'Delta',
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
                                    )
                                ]
                            ), 
                            link
                        ]

                    else:

                        cohort_name
                        # y_axis = df['Active']
                        # x_axis = df['Days Infected']

                        # x_axis = df[cohort_name]
                        # y_axis = df[day_count_value]
                        
                        


                        for val in selected_charts:
                            y_axis = df[df['Country/Region'] == val][cohort_name]
                            x_axis = df[df['Country/Region'] == val][day_count_value]
                            charts.append(dict(
                                    name=val,
                                    x = x_axis,
                                    y = y_axis,
                                    text=df[df['Country/Region'] == val]['Country/Region'],
                                    mode='markers+text',
                                    # line=dict(color='#576D22', width=4)
                                    marker={
                                        'size': 20,
                                        'opacity': 0.5,
                                        'line': {'width': 0.5, 'color': 'white'}
                                    }

                                ))

                        
                        y_axis = df[~(df['Country/Region'].isin(selected_charts))][cohort_name]
                        x_axis = df[~(df['Country/Region'].isin(selected_charts))][day_count_value]
                        charts.append(dict(
                                name='others',
                                x = x_axis,
                                y = y_axis,
                                text=df[~(df['Country/Region'].isin(selected_charts))]['Country/Region'],
                                mode='markers',
                                # line=dict(color='#576D22', width=4)
                                marker={
                                    'size': 10,
                                    'opacity': 0.5,
                                    'line': {'width': 0.5, 'color': 'white'}
                                }

                            ))

                        x_axis = df[day_count_value]

                        return [
                            html.Div(
                                children=[
                                    
                                    html.Br(),
                                    dcc.Graph(
                                        # id='smile',
                                        figure = dict(
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
                                    )
                                ]
                            ), 
                            link
                        ]
                else:
                    return [
                        html.Div(
                            dash_table.DataTable(
                                id='table',
                                columns=[{"name": i, "id": i} for i in df.columns],
                                sort_action="native",
                                sort_mode="single",
                                data=df.to_dict('records'),
                            )
                        ), 
                        link
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
