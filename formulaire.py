import streamlit as st
import joblib
import numpy as np
import pandas as pd
import altair as alt
import datetime

# Charger modèle et scaler
model = joblib.load("mon_model.pkl")
scaler = joblib.load("mon_scaler.pkl")

# Noms des mois
mois_noms = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
}

# Mois autorisés par saison
mois_saison = {
    0: [12, 1, 2],   # Hiver
    1: [3, 4, 5],    # Printemps
    2: [6, 7, 8],    # Été
    3: [9, 10, 11]   # Automne
}

st.markdown("<h1 style='text-align: center; color: #4B8BBE;'>🌞 Prédiction de la Température Maximale</h1>", unsafe_allow_html=True)
st.markdown("#### Renseignez les données météo ou chargez un fichier CSV", unsafe_allow_html=True)
st.markdown("---")

# Entrée manuelle
st.subheader("📝 Entrée manuelle")

col1, col2 = st.columns(2)

with col1:
    TMIN = st.number_input("🧊 Température minimale (x10) — ex: -244 pour 18°C", value=-244)
    SNOW = st.number_input("❄️ Quantité de neige (mm)", min_value=0, max_value=300, value=0)
    SNWD = st.number_input("⛄ Épaisseur de neige au sol (mm)", min_value=0, max_value=1000, value=0)

with col2:
    MONTH = st.selectbox("📆 Mois", options=list(mois_noms.keys()), format_func=lambda x: mois_noms[x])
    DAYOFYEAR = st.number_input("📅 Jour de l'année", min_value=1, max_value=366, value=192)
    SEASON = st.selectbox("🗓️ Saison", options=[0, 1, 2, 3], format_func=lambda x: ["Hiver", "Printemps", "Été", "Automne"][x])

# Affichage automatique de la date
try:
    date_reelle = datetime.datetime.strptime(str(DAYOFYEAR), "%j").strftime("%d %B")
    st.markdown(f"📅 Date correspondante : **{date_reelle}**")
except ValueError:
    st.warning("⚠️ Veuillez entrer un jour valide entre 1 et 366.")

# 🔍 Vérifications de cohérence
erreurs = []

if SEASON == 2:
    if SNOW > 0:
        erreurs.append("☀️ Il ne devrait pas y avoir de neige en été.")
    if TMIN < 0:
        erreurs.append("☀️ Une température minimale négative est peu probable en été.")
if SEASON == 0:
    if TMIN > 150:
        erreurs.append("❄️ Une température minimale trop élevée pour l'hiver (> 15°C).")
if SNOW > 200:
    erreurs.append("🌨️ Neige exceptionnelle (> 200 mm), cela semble anormal.")
if MONTH not in mois_saison[SEASON]:
    erreurs.append(f"❌ Le mois sélectionné ({mois_noms[MONTH]}) n'est pas cohérent avec la saison choisie.")

try:
    mois_du_jour = int(datetime.datetime.strptime(str(DAYOFYEAR), "%j").strftime("%m"))
    if mois_du_jour != MONTH:
        erreurs.append(f"❌ Le jour de l'année ({DAYOFYEAR}) correspond au mois de {mois_noms[mois_du_jour]}, pas à {mois_noms[MONTH]} sélectionné.")
    for saison_code, mois_valides in mois_saison.items():
        if mois_du_jour in mois_valides and saison_code != SEASON:
            erreurs.append(f"❌ Le jour {DAYOFYEAR} correspond à la saison {['Hiver', 'Printemps', 'Été', 'Automne'][saison_code]}, pas à celle sélectionnée ({['Hiver', 'Printemps', 'Été', 'Automne'][SEASON]}).")
except:
    erreurs.append("❌ Jour de l'année invalide.")

st.markdown("---")
if erreurs:
    st.error("🚫 Données incohérentes :")
    for e in erreurs:
        st.error(f"- {e}")
else:
    if st.button("🔮 Prédire (entrée manuelle)", use_container_width=True):
        input_array = np.array([[TMIN, SNOW, SNWD, MONTH, DAYOFYEAR, SEASON]])
        input_scaled = scaler.transform(input_array)
        prediction = model.predict(input_scaled)[0]
        st.success(f"🧪 Résultat de la prédiction (en dixièmes de °C) : **{prediction:.2f}**")
        st.info(f"Ce qui correspond à environ : **{prediction / 10:.1f} °C**")

st.markdown("---")
st.subheader("📁 Tester avec un fichier CSV")
uploaded_file = st.file_uploader("Charge un fichier CSV avec les colonnes : TMIN, SNOW, SNWD, MONTH, DAYOFYEAR, SEASON")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        expected_columns = ['TMIN', 'SNOW', 'SNWD', 'MONTH', 'DAYOFYEAR', 'SEASON']
        if not all(col in df.columns for col in expected_columns):
            st.error(f"❌ Le fichier doit contenir exactement ces colonnes : {expected_columns}")
        else:
            input_scaled = scaler.transform(df[expected_columns])
            predictions = model.predict(input_scaled)
            df["TMAX_prédit"] = predictions
            df["TMAX_Celsius"] = df["TMAX_prédit"] / 10
            df["MOIS_NOM"] = df["MONTH"].map(mois_noms)
            df["DATE"] = df["DAYOFYEAR"].apply(lambda x: datetime.datetime.strptime(str(x), "%j").strftime("%d %B"))

            st.success("✅ Prédictions terminées !")
            st.dataframe(df)

            st.subheader("📊 Évolution de TMAX prédite (en °C)")
            chart = alt.Chart(df).mark_line(point=True).encode(
                x=alt.X('DAYOFYEAR', title='Jour de l’année'),
                y=alt.Y('TMAX_Celsius', title='Température Max (°C)'),
                tooltip=['DAYOFYEAR', 'DATE', 'MOIS_NOM', 'TMAX_Celsius']
            ).properties(width=700, height=400)
            st.altair_chart(chart, use_container_width=True)

            csv_result = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Télécharger les résultats", csv_result, "résultats_prédictions.csv", "text/csv")
    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier : {e}")