#!/usr/bin/env python
# coding: utf-8


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# from .modules.create_graph import add_graph

@st.cache
def load_urgences():
    global dep_reg
    urg = pd.read_csv('../data/urgences.csv', delimiter=';', dtype={'dep':'object'}, usecols=['dep', 'date_de_passage', 'nbre_pass_corona', 'nbre_acte_corona'], 
                    parse_dates=['date_de_passage'], infer_datetime_format=True, dayfirst=True)
    urg.rename(columns={'date_de_passage':'date', 'nbre_pass_corona':'pass', 'nbre_acte_corona':'acte'}, inplace=True)
    # grouper par département (diviser par  2, car le fichier contient par classe d'âge et une ligne de total)
    urg = urg.groupby(['date', 'dep'], as_index=False).agg(lambda x : (x/2).sum())
    urg.set_index('date', inplace=True)
    # Mettre les départements en colonnes pour obtenir des time series
    urg = urg.pivot(columns='dep', values=['pass', 'acte'])
    # resample par semaine
    urg_w = urg.resample('W-MON').mean()
    # Moyenne mobile sur 7 jours
    urg_mm = urg[['pass', 'acte']].rolling(7).mean()
    return urg_mm

@st.cache
def load_google():
    global dep_reg
    google = pd.read_csv('../data/Region_Mobility_Report_CSVs/2020_FR_Region_Mobility_Report.csv', usecols=[0, 1, 2, 3, 4, 8, 9, 10, 11, 12, 13, 14],
                        parse_dates=['date'], infer_datetime_format=True, dayfirst=True)
    # suppression des colonnes inutiles
    google.drop(['country_region_code', 'country_region', 'sub_region_1', 'metro_area'], axis=1, inplace = True)
    google.columns = ['dep', 'date', 'retail', 'grocery', 'parks', 'transit', 'work', 'residential']
    google.set_index('date', inplace=True)
    # remplacer les noms de départements par les numéros
    google['date'] = google.index
    temp = google.merge(dep_reg, how='left', left_on='dep', right_on='nom_dep', validate='many_to_one')
    temp.drop(['dep', 'Région', 'departement', 'nom_dep'], axis=1, inplace=True)
    temp.set_index('date', inplace=True)
    temp.head()
    # Mettre les départements en colonnes
    google = temp[temp['num_dep'].notna()].pivot(columns='num_dep', values=['retail', 'grocery', 'parks', 'transit', 'work', 'residential'])
    # resample par semaine
    google_w = google.resample('W-MON').mean()
    # Moyenne mobile sur 7 jours
    google_mm = google.rolling(7).mean()
    return google

@st.cache
def load_apple():
    global dep_reg
    apple = pd.read_csv('../data/applemobilitytrends-2021-03-16.csv', dtype={'alternative_name':'object'})
    # on ne garde que la France
    apple = apple[apple.country == 'France'].copy()
    # unpivot car les dates sont en colonnes
    apple = apple.melt(id_vars=['geo_type', 'region', 'transportation_type', 'alternative_name', 'sub-region', 'country'], var_name='date', value_name='mobility' )
    # pivot les modes de transportations pour qu'ils soient en colonne
    apple = apple.pivot(index=['geo_type', 'region', 'alternative_name', 'sub-region', 'country', 'date'], columns='transportation_type', values ='mobility')
    apple.reset_index(inplace=True)
    apple.date = pd.to_datetime(apple.date, infer_datetime_format=True, dayfirst=True)
    apple['region'].unique()
    # on trim la mention 'Region' et on françise les noms anglais
    apple['region'] = apple['region'].str.rsplit(' Region', 1, False).str.get(0)
    apple['region'].replace({'Lower Normandy':'Basse Normandie', 'Upper Normany':'Haute Normandie', 'Burgundy':'Bourgogne', 'Corsica':'Corse','Brittany':'Bretagne', 'Lower':'Basse', 'Upper':'Haute', 'Picardy':'Picardie'}, inplace=True)
    # date en index
    apple.set_index('date', inplace=True)
    # regions en colonnes et suppression des autres colonnes géographiques
    temp = apple.pivot(columns='region', values=['driving', 'transit', 'walking'])
    apple = temp.copy()
    # resample par semaine
    apple_w = apple.resample('W-MON').mean()
    # moyenne mobile sur 7 jours
    apple_mm = apple.rolling(7).mean()
    return apple

# ### Préparation du fichier tests
# test = pd.read_csv('/data/tests.csv', delimiter=';', dtype={0:'object'}, parse_dates=['jour'], infer_datetime_format=True, dayfirst=True)


@st.cache
def load_regions():
    # Liste des départements et régions
    dep = pd.read_html('https://www.regions-departements-france.fr/')
    dep_reg = dep[3]
    dep_reg['departement'] = dep_reg['N°'] + ' - ' + dep_reg['Département']
    dep_reg.rename(columns={'Département':'nom_dep'}, inplace=True)
    dep_reg.rename(columns={'N°':'num_dep'}, inplace=True)
    return dep_reg

def add_graph(location, urg_mm, google):
    fig = make_subplots(rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    subplot_titles=['Données Covid', 'Google Mobility'])

    fig.add_scatter(
        name='Actes SOS Médecin', 
        x = urg_mm['acte'][location].index,
        y = urg_mm['acte'][location],
        row=1, col=1,
        marker_colorscale='Viridis'

    )

    fig.add_scatter(
        name='Passages aux urgences', 
        x = urg_mm['pass'][location].index,
        y = urg_mm['pass'][location],
        row=1, col=1,
        marker_color=urg_mm['pass'][location], 
        marker_colorscale='Plasma_r'
    )

    fig.update_layout(
            width = 800,
            height = 600
    )
    

    # extract places : retail, grocery, parks...
    places, _ = zip(*google.columns)
    for place in set(places):
        fig.add_scatter(
            name=place,
            x=google[place][location].index,
            y=google[place][location],
            row=2, col=1
        )
    
    return fig

dep_reg = load_regions()
urg_mm = load_urgences()
google = load_google()
#apple = load_apple()

fig = add_graph('75', urg_mm, google)

st.plotly_chart(fig)

print(fig)



# fig = make_subplots(rows=3, cols=1,
#                     shared_xaxes=True, #                     vertical_spacing=0.05,
#                     subplot_titles=['Actes SOS Médecin', 'Google Mobility', 'Apple Mobility'])

# fig.add_scatter(name='actes SOS Médecin', 
#                 x=urg_mm['acte']['75'].index, y=urg_mm['acte']['75'],
#                 row=1, col=1)
# fig.add_scatter(x=[fig.data[0].x[-1]], y=[fig.data[0].y[-1]],
#                 mode='lines + text', text='Actes', textposition='middle right')
# fig.add_scatter(name='passage aux urgences', x=urg_mm['pass']['75'].index, y=urg_mm['pass']['75'], row=1, col=1)

# # google mobility data
# fig.add_scatter(name='retail', x=google['retail']['75'].index, y=google['retail']['75'], row=2, col=1)
# fig.add_scatter(name='transit', x=google['transit']['75'].index, y=google['transit']['75'], row=2, col=1)
# fig.add_scatter(name='grocery', x=google['grocery']['75'].index, y=google['grocery']['75'], row=2, col=1)

# fig.add_scatter(name='transit', x=apple['transit']['Paris'].index, y=apple['transit']['Paris'], row=3, col=1)
# fig.add_scatter(name='driving', x=apple['driving']['Paris'].index, y=apple['driving']['Paris'], row=3, col=1)
# fig.add_scatter(name='walking', x=apple['walking']['Paris'].index, y=apple['walking']['Paris'], row=3, col=1)

# fig.update_layout(width=800, height=800, title_text='Actes SOS médecins et mobilité')
# fig.update_xaxes(
#     dtick='M1', 
#     tickformat='%b\n%Y', 
#     ticklabelmode='period'
# )
