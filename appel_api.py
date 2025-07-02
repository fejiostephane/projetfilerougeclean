import requests
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
import time

# --------------------------
# CONFIGURATION
# --------------------------
url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
headers = {
    "token": "eFZvpKlGaLOahZsErYSzDjndthqBzFlj"
}

# Plage de dates (3 ans)
start_year = 1939
end_year = 2025

# Station spécifique
station_id = "GHCND:USW00014607"  # remplace par ton ID station

# --------------------------
# Récupération des données
# --------------------------
data_dict = {
    "date": [],
    "station": [],
    "datatype": [],
    "value": []
}

for year in range(start_year, end_year + 1):
    print(f"📅 Traitement de l'année {year} ...")
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    limit = 1000
    offset = 1  # NOAA utilise un offset commençant à 1

    while True:
        params = {
            "datasetid": "GHCND",
            "stationid": station_id,
            "startdate": start_date,
            "enddate": end_date,
            "units": "metric",
            "limit": limit,
            "offset": offset
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()

            if 'results' not in data:
                print(f"✅ Aucune donnée supplémentaire pour l'année {year} à offset {offset}.")
                break

            for record in data['results']:
                if record['datatype'] in ['TMIN', 'TMAX', 'SNOW', 'SNWD']:
                    data_dict['date'].append(record['date'])
                    data_dict['station'].append(record['station'])
                    data_dict['datatype'].append(record['datatype'])
                    data_dict['value'].append(record['value'])

            print(f"   → Reçus {len(data['results'])} enregistrements (offset={offset})")

            if len(data['results']) < limit:
                # Plus de résultats à récupérer
                break
            else:
                offset += limit  # Passe à la page suivante

            time.sleep(1)  # Délai pour éviter de saturer l'API

        except requests.exceptions.RequestException as e:
            print(f"🚫 Erreur pour l'année {year}, offset {offset} : {e}")
            break

# --------------------------
# Création du DataFrame pivoté
# --------------------------
print("✅ Traitement du DataFrame ...")
df = pd.DataFrame(data_dict)
df['date'] = pd.to_datetime(df['date'])

# Pivot pour avoir une ligne par date + station
df_pivot = df.pivot_table(
    index=['date', 'station'],
    columns='datatype',
    values='value'
).reset_index()

# Colonnes supplémentaires
df_pivot['MONTH'] = df_pivot['date'].dt.month
df_pivot['DAYOFYEAR'] = df_pivot['date'].dt.dayofyear

def get_season(month):
    if month in [12, 1, 2]:
        return 'Hiver'
    elif month in [3, 4, 5]:
        return 'Printemps'
    elif month in [6, 7, 8]:
        return 'Été'
    else:
        return 'Automne'

df_pivot['SEASON'] = df_pivot['MONTH'].apply(get_season)

print(df_pivot.head())

# --------------------------
# Connexion MySQL
# --------------------------
username = "root"   # ton username MySQL
host = "127.0.0.1"
database = "projet_spe"

engine = create_engine(f"mysql+pymysql://{username}@{host}:3306/{database}")

# --------------------------
# Insertion dans la table
# --------------------------
df_pivot.to_sql("meteo", engine, if_exists="append", index=False)

print("✅ Données insérées avec succès dans la table 'meteo'.")
