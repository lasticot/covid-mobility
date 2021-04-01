#!/usr/bin/env python
# coding: utf-8

# %%
from pathlib import Path

import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go
# %%

DIR = Path.cwd()
print(DIR)

DATES_CONF1 = ['2020-03-17', '2020-05-11']
DATE_CONF2 = ['2020-10-30', '2020-12-15']
DATE_CONF3 = ['2020-10-30', '2020-12-15']

# %%
@st.cache
def load_urgences():
    global dep_reg
    urg = pd.read_csv(DIR / 'data' / 'urgences.csv', delimiter=';', dtype={'dep':'object'}, usecols=['dep', 'date_de_passage', 'nbre_pass_corona', 'nbre_acte_corona'], 
                    parse_dates=['date_de_passage'], infer_datetime_format=True, dayfirst=True)
    urg.rename(columns={'date_de_passage':'date', 'nbre_pass_corona':'pass', 'nbre_acte_corona':'acte'}, inplace=True)
    # grouper par département (diviser par  2, car le fichier contient par classe d'âge et une ligne de total)
    urg = urg.groupby(['date', 'dep'], as_index=False).agg(lambda x : (x/2).sum())
    urg.set_index('date', inplace=True)
    return urg

# %%
@st.cache
def load_google():
    global dep_reg
    google1 = pd.read_csv(DIR / 'data'/ '2020_FR_Region_Mobility_Report.csv', usecols=[0, 1, 2, 3, 4, 8, 9, 10, 11, 12, 13, 14],
                        parse_dates=['date'], infer_datetime_format=True, dayfirst=True)
    google2 = pd.read_csv(DIR / 'data'/ '2021_FR_Region_Mobility_Report.csv', usecols=[0, 1, 2, 3, 4, 8, 9, 10, 11, 12, 13, 14],
                        parse_dates=['date'], infer_datetime_format=True, dayfirst=True)
    google = google1.append(google2)
    # suppression des colonnes inutiles
    google.drop(['country_region_code', 'country_region', 'sub_region_1', 'metro_area'], axis=1, inplace = True)
    google.columns = ['dep', 'date', 'retail', 'grocery', 'parks', 'transit', 'workplaces', 'residential']
    google.set_index('date', inplace=True)
    # remplacer les noms de départements par les numéros
    google['date'] = google.index
    temp = google.merge(dep_reg, how='left', left_on='dep', right_on='nom_dep', validate='many_to_one')
    temp.drop(['dep', 'Région', 'departement', 'nom_dep'], axis=1, inplace=True)
    temp.set_index('date', inplace=True)
    return temp


# %%
@st.cache
def load_regions():
    # Liste des départements et régions
    dep_reg = pd.read_csv(DIR / 'data' / 'dep_reg.csv')
    return dep_reg

# %%
@st.cache
def load_confinements():
    conf_dates = pd.read_excel(DIR / 'data'/ 'confinement_dates.xlsx', engine='openpyxl', dtype={'Dep': str},  
                            parse_dates=[1,2,3,4,5,6]) 
    conf_dates.set_index('Dep', inplace=True)
    return conf_dates
# %%

def add_graph(location, urg, typ_consult, google, typ_poi):
    global urg_labels, poi_labels, loc_labels, conf_dates

    conf_dates = load_confinements()

    urg_title, = f"{urg_labels[typ_consult]} - {loc_labels[location]} <br> moyenne mobile sur 7 jours",
    google_title, = f"Données de fréquentation pour '{poi_labels[typ_poi]}' - {loc_labels[location]}",

    fig = make_subplots(rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    subplot_titles=[urg_title, google_title])
 
    # calcul de la moyenne mobile à la location choisie
    urg_mm = urg[urg.dep == location].rolling(7).mean()

    fig.add_scatter(
        name=urg_labels[typ_consult], 
        x = urg_mm.index,
        y = urg_mm[typ_consult],
        showlegend=False,
        row=1, col=1,
    )

    # ajoute de la moyenne mobile pour les donnés de mobilité
    google_mm = google[google.num_dep == location][typ_poi].rolling(7).mean()
    fig.add_scatter(
        name='Moyenne mobile sur 7 jours',
        x = google_mm.index,
        y = google_mm,
        row=2, col=1,
        line=dict(color='red', dash='dot')
    )

    fig.add_scatter(
        name=poi_labels[typ_poi],
        x=google[google.num_dep == location].index,
        y=google[google.num_dep == location][typ_poi],
        showlegend = False,
        opacity = 0.8,
        row=2, col=1,
        line=dict(color='grey', width=1)
    )

    fig.update_xaxes(
        dtick = 'M1', 
        tickformat = '%b\n%Y'
    )

    fig.update_layout(
            width = 1000,
            height = 800,
    )

    # ajout des périodes de confinement
    date_conf1 = (conf_dates.loc[location,'conf1_start'], conf_dates.loc[location,'conf1_stop'])
    date_conf2 = (conf_dates.loc[location,'conf2_start'], conf_dates.loc[location,'conf2_stop'])
    fig.add_vrect(x0=date_conf1[0], x1=date_conf1[1], fillcolor='blue', opacity=0.1, name='Confinement')
    fig.add_vrect(x0=date_conf2[0], x1=date_conf2[1], fillcolor='blue', opacity=0.1)
    # check si conf3 existe et utililse la date du jour comme date de fin
    if not conf_dates.loc[location,'conf3_start'] is pd.NaT:
        date_conf3 = (conf_dates.loc[location,'conf3_start'], max(urg_mm.index))
        fig.add_vrect(x0=date_conf3[0], x1=date_conf3[1], fillcolor='blue', opacity=0.1)
    
    return fig


# %%

# dep_reg = load_regions()
# urg = load_urgences()
# google = load_google()

# fig = add_graph('75', urg, 'pass', google, 'retail')

# fig.show()



# %%
dep_reg = load_regions()
urg = load_urgences()
google = load_google()
#apple = load_apple()

loc_labels = dict(zip(dep_reg.num_dep, dep_reg.departement))

urg_labels = dict([('acte', 'Actes SOS Médecin pour suspicion de Covid'),
                   ('pass', 'Passage aux urgences pour suspicion de Covid')]) 

poi_labels = dict([
    ('retail', 'retail & recreation'), 
    ('grocery', 'grocery & pharmacy'), 
    ('parks', 'parks'), 
    ('transit', 'transit stations'),
    ('workplaces', 'workplaces'),
    ('residential', 'residential')
])
st.header('Consultations pour suspicion de Covid et données de mobilité pour la France par département au 26 mars 2021')

# sélection du département
loc = st.sidebar.selectbox('Département', list(loc_labels.keys()), index=75, format_func=lambda x: loc_labels[x])

# sélection du type de consultation Urgences ou SOS Médecins
typ_consult = st.sidebar.radio('Type de consultation', 
        list(urg_labels.keys()), index=1, format_func=lambda x: urg_labels[x])

# sélection du type de POI google
typ_poi = st.sidebar.selectbox('Lieux fréquentés (catégories Google)', list(poi_labels.keys()),
                        format_func=lambda x: poi_labels[x])



fig = add_graph(loc, urg, typ_consult, google, typ_poi)
st.plotly_chart(fig, use_container_width=False)

st.sidebar.write("[@FranklinMaillot](http://www.twitter.com/FranklinMaillot)")
st.sidebar.write("Sources :  \n[Santé Publique France](https://www.data.gouv.fr/fr/datasets/donnees-des-urgences-hospitalieres-et-de-sos-medecins-relatives-a-lepidemie-de-covid-19/#_)  \n[Rapports de mobilité Google](https://www.google.com/covid19/mobility/)")

