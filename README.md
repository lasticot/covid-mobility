# Visualisation des consultations pour suspicion de Covid et des données de mobilité pour la France par département

Tableau de bord interactif réalisé avec [Streamlit](http://streamlit.io/) pour visualiser les effets des variations de la mobilité sur les consultations pour Covid. 

Le nombre de consultations Covid est la variable qui est susceptible d'être le plus rapidement influencée par un changement de comportement. Le nombre de tests positifs étant très dépendant du nombre de tests réalisés (très faible lors de la première vague) et le nombre d'hospitalisations est influencé à plus long terme.   

Les données de mobilité sont mises à disposition par [Google](https://www.google.com/covid19/mobility/). 
Les données de consultation Covid SOS Médecin et passage aux urgences sont celles de [Santé Publique France](https://www.data.gouv.fr/fr/datasets/donnees-des-urgences-hospitalieres-et-de-sos-medecins-relatives-a-lepidemie-de-covid-19/#_)

Les graph sont réalisés avec [Plotly](https://plotly.com/python/)
