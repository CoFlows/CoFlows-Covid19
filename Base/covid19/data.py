import numpy as np
import pandas as pd
import datetime

import threading

from requests import get as get
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse
import re

all_date = None
all_from_0 = None
all_from_0_confirmed = None
all_from_0_growth = None
all_from_0_death = None
all_from_0_recovered = None
all_from_0_active = None
first_infection = {}
first_death = {}
first_recovered = {}
first_dates = {}

__lock_loading = threading.Lock()



def Load():
    # pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)

    __lock_loading.acquire()

    global all_date, all_from_0, all_from_0_confirmed, all_from_0_growth, all_from_0_active, all_from_0_death, all_from_0_recovered, first_infection, first_death, first_recovered, first_dates

    if all_date is not None:
        __lock_loading.release()
        return

    print('Covid19 Loading data starting @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

    todays_date = datetime.datetime.today().replace(minute=0, hour=0, second=0, microsecond=0)
    print('Covid19 todays: ' + str(todays_date))

    # Load latest data from https://ncov2019.live/data
    print('Covid19 Load data from ncov2019.live')
    covid_live_url = 'https://ncov2019.live/data'
    html_soup = BeautifulSoup(get(covid_live_url).text, 'html.parser')
    live_tables = ['sortable_table_Global', 'sortable_table_China', 'sortable_table_Canada', 'sortable_table_Australia']
    latest_pd = pd.DataFrame(columns=['Name', 'confirmed', 'confirmed_chg', 'confirmed_chg_pct', 'death', 'death_chg', 'death_chg_pct', 'recovered', 'serious'])

    for table_name in live_tables:
        
        table = html_soup.find(id=table_name)
        table_rows = table.find_all('tr')
        res = []
        for tr in table_rows:
            td = tr.find_all('td')
            row = [re.sub('[^A-Za-z0-9]\W+', '', d.text.strip()).replace(',', '') for d in td]
            if row:
                res.append(row)
        _df = pd.DataFrame(res, columns=['Name', 'confirmed', 'confirmed_chg', 'confirmed_chg_pct', 'death', 'death_chg', 'death_chg_pct', 'recovered', 'serious'])
        latest_pd = latest_pd.append(_df)
    latest_pd['Name'] = latest_pd.apply(lambda row: 'Australian Capital Territory' if row['Name'] == 'CanberraACT)' else row['Name'] , axis=1)
    latest_pd[['confirmed', 'confirmed_chg', 'confirmed_chg_pct', 'death', 'death_chg', 'death_chg_pct', 'recovered', 'serious']] = latest_pd[['confirmed', 'confirmed_chg', 'confirmed_chg_pct', 'death', 'death_chg', 'death_chg_pct', 'recovered', 'serious']].apply(pd.to_numeric).fillna(0)
    
    print(latest_pd)

    # Load data from ULKLC
    print('Covid19 Load data from ULKLC...')
    ulklc_url = 'https://raw.githubusercontent.com/ulklc/covid19-timeseries/master/countryReport/raw/rawReport.csv'
    ulklc_pd = pd.read_csv(ulklc_url)
    ulklc_pd = ulklc_pd.rename(columns={'day': 'date', 'countryName': 'Country/Region', 'region': 'Continent', 'lat': 'Lat', 'lon': 'Long'})
    ulklc_pd[['date']] = ulklc_pd[['date']].apply(pd.to_datetime)

    ulklc_pd['Province/State'] = 'All'
    ulklc_pd = ulklc_pd[['date', 'Continent', 'Province/State', 'Country/Region', 'confirmed', 'recovered', 'death']]

    
    print('Covid19 merge ncov2019.live with ulklc...')
    lastest_name_list = [cty[0] for cty in latest_pd[['Name']].drop_duplicates().values.tolist()]
    ulklc_pd_last_index = ulklc_pd.last_valid_index()
    for name in lastest_name_list:
        last_ulklc_row_pd = ulklc_pd[(ulklc_pd['Country/Region'] == name) & (ulklc_pd['Province/State'] == 'All')]
        if not last_ulklc_row_pd.empty:
            last_date = last_ulklc_row_pd['date'].max()
            continent_name = last_ulklc_row_pd['Continent'][last_ulklc_row_pd.last_valid_index()]
            
            last_rows_pd = latest_pd[latest_pd['Name'] == name]

            new_confirmed_value = last_rows_pd['confirmed'][last_rows_pd.last_valid_index()]
            new_recovered_value = last_rows_pd['recovered'][last_rows_pd.last_valid_index()]
            new_death_value = last_rows_pd['death'][last_rows_pd.last_valid_index()]

            lastest_ulklc_pd = ulklc_pd[(ulklc_pd['Country/Region'] == name) & (ulklc_pd['date'] == last_date)]

            latest_confirmed_value = lastest_ulklc_pd['confirmed'][lastest_ulklc_pd.last_valid_index()]
            latest_recovered_value = lastest_ulklc_pd['recovered'][lastest_ulklc_pd.last_valid_index()]
            latest_death_value = lastest_ulklc_pd['death'][lastest_ulklc_pd.last_valid_index()]
            
            if (latest_confirmed_value >= new_confirmed_value) or (latest_recovered_value >= new_recovered_value) or (latest_death_value >= new_death_value):
                new_confirmed_value = max(latest_confirmed_value, new_confirmed_value)
                new_recovered_value = max(latest_recovered_value, new_recovered_value)
                new_death_value = max(latest_death_value, new_death_value)

                if last_date == todays_date:
                    ulklc_pd.loc[(ulklc_pd['Country/Region'] == name) & (ulklc_pd['date'] == last_date), 'confirmed'] = new_confirmed_value
                    ulklc_pd.loc[(ulklc_pd['Country/Region'] == name) & (ulklc_pd['date'] == last_date), 'recovered'] = new_recovered_value
                    ulklc_pd.loc[(ulklc_pd['Country/Region'] == name) & (ulklc_pd['date'] == last_date), 'death'] = new_death_value

                else:
                    ulklc_pd_last_index = ulklc_pd_last_index + 1
                    ulklc_pd.loc[ulklc_pd_last_index] = [todays_date, continent_name, 'All', name, new_confirmed_value, new_recovered_value, new_death_value]

    # Load data from John Hopkins University
    print('Covid19 Load data from John Hopkins University...')
    jhu_covid19_confirmed_url = 'https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    jhu_covid19_recovered_url = 'https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'
    jhu_covid19_death_url = 'https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'

    jhu_covid19_confirmed_pd = pd.read_csv(jhu_covid19_confirmed_url)
    jhu_covid19_recovered_pd = pd.read_csv(jhu_covid19_recovered_url)
    jhu_covid19_death_pd = pd.read_csv(jhu_covid19_death_url)

    def cleanPD(dirty_pd):
        clean_pd = dirty_pd.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'])
        clean_pd[['date']] = clean_pd[['variable']].apply(pd.to_datetime)
        clean_pd.drop(columns=['variable', 'Lat', 'Long'], inplace=True)
        clean_pd.reindex(['Province/State', 'Country/Region'])
        return clean_pd

    def unitePD(confirmed, recovered, death):
        confirmed_clean = cleanPD(confirmed)
        confirmed_clean.rename(columns={'value':'confirmed'}, inplace=True)

        recovered_clean = cleanPD(recovered)
        recovered_clean.rename(columns={'value':'recovered'}, inplace=True)
        
        death_clean = cleanPD(death)
        death_clean.rename(columns={'value':'death'}, inplace=True)
        
        union = confirmed_clean.merge(recovered_clean, how='left').merge(death_clean, how='left')

        union = union[['date', 'Province/State', 'Country/Region', 'confirmed', 'recovered', 'death']]
        return union

    print('Covid19 process JHU...')
    jhu_union = unitePD(jhu_covid19_confirmed_pd, jhu_covid19_recovered_pd, jhu_covid19_death_pd)

    union_agg = jhu_union[['Province/State', 'Country/Region']].drop_duplicates().groupby(['Country/Region']).agg({ 'Country/Region': 'count'})
    union_agg = union_agg[union_agg['Country/Region'] > 1]
    union_agg = union_agg.rename(columns={'Country/Region' : 'count'}).reset_index()
    union_agg = list(union_agg['Country/Region'])
    jhu_union = jhu_union[jhu_union['Country/Region'].isin(union_agg)]

    jhu_union.loc[:,'Province/State'] = jhu_union.apply(lambda row: 'Main' if str(row['Province/State']) == 'nan' else str(row['Province/State']), axis=1)
    # union_.loc[:,'recovered'] = 0
    continents = ulklc_pd[['Country/Region', 'Continent']].drop_duplicates()
    jhu_union = jhu_union.merge(continents, left_on=['Country/Region'], right_on=['Country/Region'], how='left')

    print('Covid19 merge ncov2019.live with JHU...')
    union_pd_last_index = jhu_union.last_valid_index()
    for name in lastest_name_list:
        # last_date_pd = union_[union_['Province/State'] == name]['date']
        last_union_rows_pd = jhu_union[jhu_union['Province/State'] == name]
        
        if not last_union_rows_pd.empty:
            last_date = last_union_rows_pd['date'].max()
            continent_name = last_union_rows_pd['Continent'][last_union_rows_pd.first_valid_index()]
            country_name = last_union_rows_pd['Country/Region'][last_union_rows_pd.first_valid_index()]

            last_rows_pd = latest_pd[latest_pd['Name'] == name]
            if not last_rows_pd.empty:

                
                lastest_jhu_union_pd = jhu_union[(jhu_union['Province/State'] == name) & (jhu_union['date'] == last_date)]

                latest_confirmed_value = lastest_jhu_union_pd['confirmed'][lastest_jhu_union_pd.last_valid_index()]
                latest_recovered_value = lastest_jhu_union_pd['recovered'][lastest_jhu_union_pd.last_valid_index()]
                latest_death_value = lastest_jhu_union_pd['death'][lastest_jhu_union_pd.last_valid_index()]

                new_confirmed_value = last_rows_pd['confirmed'][last_rows_pd.last_valid_index()]
                new_recovered_value = last_rows_pd['recovered'][last_rows_pd.last_valid_index()]
                new_death_value = last_rows_pd['death'][last_rows_pd.last_valid_index()]

                # if not(latest_confirmed_value == new_confirmed_value) or not(latest_recovered_value == new_recovered_value) or not(latest_death_value == new_death_value):
                if (latest_confirmed_value >= new_confirmed_value) or (latest_recovered_value >= new_recovered_value) or (latest_death_value >= new_death_value):
                    new_confirmed_value = max(latest_confirmed_value, new_confirmed_value)
                    new_recovered_value = max(latest_recovered_value, new_recovered_value)
                    new_death_value = max(latest_death_value, new_death_value)

                    if last_date == todays_date:

                        jhu_union.loc[(jhu_union['Province/State'] == name) & (jhu_union['date'] == last_date), 'confirmed'] = new_confirmed_value
                        jhu_union.loc[(jhu_union['Province/State'] == name) & (jhu_union['date'] == last_date), 'recovered'] = new_recovered_value
                        jhu_union.loc[(jhu_union['Province/State'] == name) & (jhu_union['date'] == last_date), 'death'] = new_death_value

                    else:
                        union_pd_last_index = union_pd_last_index + 1
                        jhu_union.loc[union_pd_last_index] = [todays_date, name, country_name, new_confirmed_value, new_recovered_value, new_death_value, continent_name]
                    
    union = ulklc_pd.append(jhu_union, sort=True)

    # print('Covid19 merge ncov2019.live with JHU... APPEND DONE')

    def transform_change(union_pd, country_region, province_state):

        res_pd = union_pd.loc[(union_pd['Country/Region'] == str(country_region)) & (union_pd['Province/State'] == str(province_state))].copy(deep = True)

        res_pd.loc[:, 'confirmed_change'] = res_pd.loc[:, 'confirmed'].diff(1).fillna(0)
        res_pd.loc[:, 'death_change'] = res_pd.loc[:, 'death'].diff(1).fillna(0)
        res_pd.loc[:, 'recovered_change'] = res_pd.loc[:, 'recovered'].diff(1).fillna(0)

        res_pd.loc[:, 'active'] = res_pd.loc[:, 'confirmed'] - res_pd.loc[:, 'recovered'] - res_pd.loc[:, 'death']
        res_pd.loc[:, 'active_change'] = res_pd.loc[:, 'active'].diff(1).fillna(0)

        # Take Hong Kong out from China
        # res_pd.loc[:, 'Country/Region'] = res_pd.apply(lambda row: row['Province/State'] if str(row['Province/State']) == 'Hong Kong' else row['Country/Region'], axis=1)
        return res_pd

    union_change = pd.DataFrame()
    countries_provinces_pd = union[['Country/Region', 'Province/State']].drop_duplicates()
    for index, row in countries_provinces_pd.iterrows():
        country = str(row['Country/Region'])
        state = str(row['Province/State'])
        transform_pd = transform_change(union, country, state)

        if union_change.empty:
            union_change = transform_pd
        else:
            union_change = union_change.append(transform_pd)

    countries_pd = union[['Country/Region']].drop_duplicates()
    # union_change_aggregated = union_change[~(union_change['Province/State'] == 'All')].groupby(['date', 'Country/Region']).agg(
    #     {
    #         'Province/State': 'first',
    #         'confirmed': 'sum',
    #         # "recovered": "sum",
    #         'death': 'sum',
    #         # "active": "sum",

    #         'confirmed_change': 'sum',
    #         # "recovered_change": "sum",
    #         'death_change': 'sum',
    #         # "active_change": "sum"
    #     }).reset_index()

    # union_change_aggregated = union_change_aggregated[union_change_aggregated['Province/State'] > 1]
    # union_change_aggregated['Province/State'] = 'All' # union_change_aggregated['Country/Region']

    union_change_world_aggregated = union_change[(union_change['Province/State'] == 'All')].groupby(['date']).agg(
        {
            'Country/Region': lambda x: 'World',
            'Province/State': lambda x: 'All',
            'confirmed': "sum",
            "recovered": 'sum',
            'death': 'sum',
            "active": "sum",

            'confirmed_change': 'sum',
            "recovered_change": "sum",
            'death_change': 'sum',
            "active_change": "sum"
        }).reset_index()

    union_change = union_change.append(union_change_world_aggregated, sort=True)    
    union_change = union_change.reset_index()

    countries_provinces_pd = union_change[['Country/Region', 'Province/State']].drop_duplicates()

    __union_change = pd.DataFrame()
    for index, row in countries_provinces_pd.iterrows():
        country_region = row['Country/Region']
        province_state = row['Province/State']

        res_pd = union_change.loc[(union_change['Country/Region'] == str(country_region)) & (union_change['Province/State'] == str(province_state))].copy(deep = True)
        # print(str(country_region) + ' ' + str(province_state))
        # print(res_pd)
        res_pd.loc[:, 'growth'] = ((res_pd.loc[:, 'confirmed'] / res_pd.loc[:, 'confirmed'].shift(1) - 1).fillna(0) * 100.0).apply(lambda x: round(x, 2))
        res_pd.loc[:, 'growth_5day'] = res_pd.loc[:, 'growth'].rolling(window=5).mean().fillna(0).apply(lambda x: round(x, 2))

        __union_change = __union_change.append(res_pd, sort=True)

    union_change = __union_change
    
    starting_dates = [1, 100, 1000]
    # starting_dates = [1, 100, 200, 300, 500, 750, 1000]
    starting_dates = [1]
    union_change_0 = {}
    union_change_0_confirmed = {}
    union_change_0_growth = {}
    union_change_0_death = {}
    union_change_0_recovered = {}
    union_change_0_active = {}
    
    
    for start_idx in starting_dates:
        _union_change_0 = pd.DataFrame()
        _union_change_0_confirmed = pd.DataFrame()
        _union_change_0_growth = pd.DataFrame()
        _union_change_0_death = pd.DataFrame()
        _union_change_0_recovered = pd.DataFrame()
        _union_change_0_active = pd.DataFrame()
    

        print('Covid19 computing first ' + str(start_idx) + ' dates @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

        first_infection[start_idx] = union_change[union_change['confirmed'] >= start_idx][['date', 'Country/Region', 'Province/State']].groupby(['Country/Region', 'Province/State']).min().reset_index().rename(columns={'date':'infection'})
        first_death[start_idx] = union_change[union_change['death'] >= start_idx][['date', 'Country/Region', 'Province/State']].groupby(['Country/Region', 'Province/State']).min().reset_index().rename(columns={'date':'death'})
        first_dates[start_idx] = first_infection[start_idx].merge(first_death[start_idx], how='left')

        print('         Covid19 computing first merge @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

        for index, row in countries_provinces_pd.iterrows():
            country_region = str(row['Country/Region'])
            province_state = str(row['Province/State'])

            province_state = country_region if province_state == 'nan' else province_state
            first_date_pd = first_infection[start_idx][(first_infection[start_idx]['Country/Region'] == country_region) & (first_infection[start_idx]['Province/State'] == province_state)]['infection']
            
            if not first_date_pd.empty:
                first_date = first_date_pd.iloc[0]
                data_0 = union_change[(union_change['Country/Region'] == country_region) & (union_change['Province/State'] == province_state)]
                
                data_0 = data_0[data_0['date'] >= first_date]
                data_0['Day Count'] = data_0['date'] - first_date

                data_0 = data_0.set_index(['Day Count'])
                data_0['Day Count'] = data_0['date'] - first_date

                if _union_change_0.empty:
                    _union_change_0 = data_0
                else:
                    _union_change_0 = _union_change_0.append(data_0, sort=True)

        print('         Covid19 computing first confirmed @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

        for index, row in countries_provinces_pd.iterrows():
            country_region = str(row['Country/Region'])
            province_state = str(row['Province/State'])
            
            province_state = country_region if province_state == 'nan' else province_state
            name = country_region if province_state == 'All' else country_region + ' / ' + province_state
            pd_0 = _union_change_0[(_union_change_0['Country/Region'] == country_region) & (_union_change_0['Province/State'] == province_state)][['Province/State', 'confirmed']].rename(columns={'confirmed': name }).drop(columns=['Province/State'])
            pd_0 = pd_0.loc[~pd_0.index.duplicated(keep='first')]
            if _union_change_0_confirmed.empty:
                _union_change_0_confirmed = pd_0
            else:
                _union_change_0_confirmed = _union_change_0_confirmed.merge(pd_0, how='outer', left_index=True, right_index=True)

        print('         Covid19 computing first Growth @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

        for index, row in countries_provinces_pd.iterrows():
            country_region = str(row['Country/Region'])
            province_state = str(row['Province/State'])
            
            province_state = country_region if province_state == 'nan' else province_state
            name = country_region if province_state == 'All' else country_region + ' / ' + province_state

            pd_0 = _union_change_0[(_union_change_0['Country/Region'] == country_region) & (_union_change_0['Province/State'] == province_state)][['Province/State', 'growth']].rename(columns={'growth': name }).drop(columns=['Province/State'])
            pd_0 = pd_0.loc[~pd_0.index.duplicated(keep='first')]
            if _union_change_0_growth.empty:
                _union_change_0_growth = pd_0
            else:
                _union_change_0_growth = _union_change_0_growth.merge(pd_0, how='outer', left_index=True, right_index=True)

        print('         Covid19 computing first death @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

        
        for index, row in countries_provinces_pd.iterrows():
            country_region = str(row['Country/Region'])
            province_state = str(row['Province/State'])
            province_state = country_region if province_state == 'nan' else province_state
            name = country_region if province_state == 'All' else country_region + ' / ' + province_state
            pd_0 = _union_change_0[(_union_change_0['Country/Region'] == country_region) & (_union_change_0['Province/State'] == province_state)][['Province/State', 'death']].rename(columns={'death': name }).drop(columns=['Province/State'])
            pd_0 = pd_0.loc[~pd_0.index.duplicated(keep='first')]
            
            if _union_change_0_death.empty:
                _union_change_0_death = pd_0
            else:
                _union_change_0_death = _union_change_0_death.merge(pd_0, how='outer', left_index=True, right_index=True)

        print('         Covid19 computing first recovered @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

        for index, row in countries_provinces_pd.iterrows():
            country_region = str(row['Country/Region'])
            province_state = str(row['Province/State'])
            province_state = country_region if province_state == 'nan' else province_state
            name = country_region if province_state == 'All' else country_region + ' / ' + province_state
            pd_0 = _union_change_0[(_union_change_0['Country/Region'] == country_region) & (_union_change_0['Province/State'] == province_state)][['Province/State', 'recovered']].rename(columns={'recovered': name }).drop(columns=['Province/State'])
            pd_0 = pd_0.loc[~pd_0.index.duplicated(keep='first')]
            
            if _union_change_0_death.empty:
                _union_change_0_recovered = pd_0
            else:
                _union_change_0_recovered = _union_change_0_recovered.merge(pd_0, how='outer', left_index=True, right_index=True)

        print('         Covid19 computing first active @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

        for index, row in countries_provinces_pd.iterrows():
            country_region = str(row['Country/Region'])
            province_state = str(row['Province/State'])
            province_state = country_region if province_state == 'nan' else province_state
            name = country_region if province_state == 'All' else country_region + ' / ' + province_state
            pd_0 = _union_change_0[(_union_change_0['Country/Region'] == country_region) & (_union_change_0['Province/State'] == province_state)][['Province/State', 'active']].rename(columns={'active': name }).drop(columns=['Province/State'])
            pd_0 = pd_0.loc[~pd_0.index.duplicated(keep='first')]
            
            if _union_change_0_active.empty:
                _union_change_0_active = pd_0
            else:
                _union_change_0_active = _union_change_0_active.merge(pd_0, how='outer', left_index=True, right_index=True)

        union_change_0[start_idx] = _union_change_0
        union_change_0_confirmed[start_idx] = _union_change_0_confirmed
        union_change_0_growth[start_idx] = _union_change_0_growth
        union_change_0_death[start_idx] = _union_change_0_death
        union_change_0_recovered[start_idx] = _union_change_0_recovered
        union_change_0_active[start_idx] = _union_change_0_active
    
        print('Covid19 computing done @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

    all_date = union_change
    all_from_0 = union_change_0
    all_from_0_confirmed = union_change_0_confirmed
    all_from_0_growth = union_change_0_growth
    all_from_0_death = union_change_0_death
    all_from_0_recovered = union_change_0_recovered
    all_from_0_active = union_change_0_active

    __lock_loading.release()
