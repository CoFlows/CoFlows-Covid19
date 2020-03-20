import numpy as np
import pandas as pd
import datetime

import threading

all_date = None
all_from_0 = None
all_from_0_confirmed = None
all_from_0_active = None
all_from_0_death = None
all_from_0_recovered = None
first_infection = {}
first_death = {}
first_recovered = {}
first_dates = {}

__lock_loading = threading.Lock()

def Load():
    __lock_loading.acquire()

    global all_date, all_from_0, all_from_0_confirmed, all_from_0_active, all_from_0_death, all_from_0_recovered, first_infection, first_death, first_recovered, first_dates

    if all_date is not None:
        __lock_loading.release()
        return

    print('Covid19 Loading data starting @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')


    covid19_confirmed_url = 'https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv'
    covid19_death_url = 'https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv'
    covid19_recovered_url = 'https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv'

    covid19_confirmed_pd = pd.read_csv(covid19_confirmed_url)
    covid19_death_pd = pd.read_csv(covid19_death_url)
    covid19_recovered_pd = pd.read_csv(covid19_recovered_url)

    def cleanPD(dirty_pd):
        clean_pd = dirty_pd.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'])
        clean_pd[['date']] = clean_pd[['variable']].apply(pd.to_datetime)
        clean_pd.drop(columns=['variable', 'Lat', 'Long'], inplace=True)
        clean_pd.reindex(['Province/State', 'Country/Region'])
        return clean_pd

    def unitePD(confirmed, death, recovered):
        confirmed_clean = cleanPD(confirmed)
        confirmed_clean.rename(columns={'value':'confirmed'}, inplace=True)
        death_clean = cleanPD(death)
        death_clean.rename(columns={'value':'death'}, inplace=True)
        recovered_clean = cleanPD(recovered)
        recovered_clean.rename(columns={'value':'recovered'}, inplace=True)
        union = confirmed_clean.merge(death_clean, how='left').merge(recovered_clean, how='left')

        union = union[['date', 'Province/State', 'Country/Region', 'confirmed', 'recovered', 'death']]
        return union

    union = unitePD(covid19_confirmed_pd, covid19_death_pd, covid19_recovered_pd)

    def transform_change(union_pd, country_region, province_state):
        if str(province_state) == 'nan':
            res_pd = union_pd.loc[(union_pd['Country/Region'] == str(country_region))].copy(deep = True)
        else:
            res_pd = union_pd.loc[(union_pd['Country/Region'] == str(country_region)) & (union_pd['Province/State'] == str(province_state))].copy(deep = True)

        res_pd.loc[:, 'active'] = res_pd.loc[:, 'confirmed'] - res_pd.loc[:, 'recovered'] - res_pd.loc[:, 'death']

        res_pd.loc[:, 'confirmed_change'] = res_pd.loc[:, 'confirmed'].diff(1).fillna(0)
        res_pd.loc[:, 'recovered_change'] = res_pd.loc[:, 'recovered'].diff(1).fillna(0)
        res_pd.loc[:, 'death_change'] = res_pd.loc[:, 'death'].diff(1).fillna(0)
        res_pd.loc[:, 'active_change'] = res_pd.loc[:, 'active'].diff(1).fillna(0)

        res_pd.loc[:, 'Province/State'] = res_pd.apply(lambda row: row['Country/Region'] if str(row['Province/State']) == 'nan' else row['Province/State'], axis=1)

        # Take Hong Kong out from China
        res_pd.loc[:, 'Country/Region'] = res_pd.apply(lambda row: row['Province/State'] if str(row['Province/State']) == 'Hong Kong' else row['Country/Region'], axis=1)
        return res_pd

    union_change = pd.DataFrame()
    countries_provinces_pd = union[['Country/Region', 'Province/State']].drop_duplicates()
    for index, row in countries_provinces_pd.iterrows():
        transform_pd = transform_change(union, row['Country/Region'], row['Province/State'])

        if union_change.empty:
            union_change = transform_pd
        else:
            union_change = union_change.append(transform_pd)

    countries_pd = union[['Country/Region']].drop_duplicates()
    union_change_aggregated = union_change.groupby(['date', 'Country/Region']).agg(
        {
            "Province/State": "first",
            "confirmed": "sum",
            "recovered": "sum",
            "death": "sum",
            "active": "sum",

            "confirmed_change": "sum",
            "recovered_change": "sum",
            "death_change": "sum",
            "active_change": "sum"
        }).reset_index()

    union_change_aggregated['Province/State'] = 'All' # union_change_aggregated['Country/Region']

    union_change_world_aggregated = union_change.groupby(['date']).agg(
        {
            "Country/Region": lambda x: 'World',
            "Province/State": lambda x: 'All',
            "confirmed": "sum",
            "recovered": "sum",
            "death": "sum",
            "active": "sum",

            "confirmed_change": "sum",
            "recovered_change": "sum",
            "death_change": "sum",
            "active_change": "sum"
        }).reset_index()

    

    union_change = union_change.append(union_change_aggregated, sort=True)
    union_change = union_change.append(union_change_world_aggregated, sort=True)
    union_change = union_change.drop_duplicates()
    union_change = union_change.reset_index()

    countries_provinces_pd = union_change[['Country/Region', 'Province/State']].drop_duplicates()

    
    starting_dates = [1, 100, 200, 300, 500, 750, 1000]
    union_change_0 = {}
    union_change_0_confirmed = {}
    union_change_0_active = {}
    union_change_0_death = {}
    union_change_0_recovered = {}
    
    
    for start_idx in starting_dates:
        _union_change_0 = pd.DataFrame()
        _union_change_0_confirmed = pd.DataFrame()
        _union_change_0_active = pd.DataFrame()
        _union_change_0_death = pd.DataFrame()
        _union_change_0_recovered = pd.DataFrame()
    

        print('Covid19 computing first ' + str(start_idx) + ' dates @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')


        first_infection[start_idx] = union_change[union_change['confirmed'] >= start_idx][['date', 'Country/Region', 'Province/State']].groupby(['Country/Region', 'Province/State']).min().reset_index().rename(columns={'date':'infection'})
        first_death[start_idx] = union_change[union_change['death'] >= start_idx][['date', 'Country/Region', 'Province/State']].groupby(['Country/Region', 'Province/State']).min().reset_index().rename(columns={'date':'death'})
        first_recovered[start_idx] = union_change[union_change['recovered'] >= start_idx][['date', 'Country/Region', 'Province/State']].groupby(['Country/Region', 'Province/State']).min().reset_index().rename(columns={'date':'recovery'})
        first_dates[start_idx] = first_infection[start_idx].merge(first_death[start_idx], how='left').merge(first_recovered[start_idx], how='left')

        print('Covid19 computing first merge @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

        
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
                    _union_change_0 = _union_change_0.append(data_0)

        print('Covid19 computing first confirmed @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

        
        for index, row in countries_provinces_pd.iterrows():
            country_region = str(row['Country/Region'])
            province_state = str(row['Province/State'])
            province_state = country_region if province_state == 'nan' else province_state
            name = country_region if province_state == 'All' else country_region + ' / ' + province_state
            pd_0 = _union_change_0[(_union_change_0['Country/Region'] == country_region) & (_union_change_0['Province/State'] == province_state)][['Province/State', 'confirmed']].rename(columns={'confirmed': name }).drop(columns=['Province/State'])
            if _union_change_0_confirmed.empty:
                _union_change_0_confirmed = pd_0
            else:
                _union_change_0_confirmed = _union_change_0_confirmed.merge(pd_0, how='outer', left_index=True, right_index=True)

        print('Covid19 computing first active @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

        
        for index, row in countries_provinces_pd.iterrows():
            country_region = str(row['Country/Region'])
            province_state = str(row['Province/State'])
            province_state = country_region if province_state == 'nan' else province_state
            name = country_region if province_state == 'All' else country_region + ' / ' + province_state
            pd_0 = _union_change_0[(_union_change_0['Country/Region'] == country_region) & (_union_change_0['Province/State'] == province_state)][['Province/State', 'active']].rename(columns={'active': name }).drop(columns=['Province/State'])
            if _union_change_0_active.empty:
                _union_change_0_active = pd_0
            else:
                _union_change_0_active = _union_change_0_active.merge(pd_0, how='outer', left_index=True, right_index=True)

        print('Covid19 computing first death @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

        
        for index, row in countries_provinces_pd.iterrows():
            country_region = str(row['Country/Region'])
            province_state = str(row['Province/State'])
            province_state = country_region if province_state == 'nan' else province_state
            name = country_region if province_state == 'All' else country_region + ' / ' + province_state
            pd_0 = _union_change_0[(_union_change_0['Country/Region'] == country_region) & (_union_change_0['Province/State'] == province_state)][['Province/State', 'death']].rename(columns={'death': name }).drop(columns=['Province/State'])
            if _union_change_0_death.empty:
                _union_change_0_death = pd_0
            else:
                _union_change_0_death = _union_change_0_death.merge(pd_0, how='outer', left_index=True, right_index=True)

        print('Covid19 computing first recovered @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

        for index, row in countries_provinces_pd.iterrows():
            country_region = str(row['Country/Region'])
            province_state = str(row['Province/State'])
            province_state = country_region if province_state == 'nan' else province_state
            name = country_region if province_state == 'All' else country_region + ' / ' + province_state
            pd_0 = _union_change_0[(_union_change_0['Country/Region'] == country_region) & (_union_change_0['Province/State'] == province_state)][['Province/State', 'recovered']].rename(columns={'recovered': name }).drop(columns=['Province/State'])
            if _union_change_0_recovered.empty:
                _union_change_0_recovered = pd_0
            else:
                _union_change_0_recovered = _union_change_0_recovered.merge(pd_0, how='outer', left_index=True, right_index=True)

        union_change_0[start_idx] = _union_change_0
        union_change_0_confirmed[start_idx] = _union_change_0_confirmed
        union_change_0_active[start_idx] = _union_change_0_active
        union_change_0_death[start_idx] = _union_change_0_death
        union_change_0_recovered[start_idx] = _union_change_0_recovered
    
        print('Covid19 computing done @ ' + datetime.datetime.now().strftime("%H:%M:%S") + ' ...')

    # print('------------------ Confirmed')
    # print(union_change_0_confirmed)
    # print('------------------ Active')
    # print(union_change_0_active)
    # print('------------------ Deaths')
    # print(union_change_0_death)
    # print('------------------ Recovered')
    # print(union_change_0_recovered)

    all_date = union_change
    all_from_0 = union_change_0
    all_from_0_confirmed = union_change_0_confirmed
    all_from_0_active = union_change_0_active
    all_from_0_death = union_change_0_death
    all_from_0_recovered = union_change_0_recovered

    __lock_loading.release()
    

    return union_change, union_change_0, union_change_0_confirmed, union_change_0_active, union_change_0_death, union_change_0_recovered, first_infection, first_death, first_recovered, first_dates