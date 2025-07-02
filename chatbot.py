import streamlit as st
import joblib
import numpy as np
import datetime
import re
import os
from dotenv import load_dotenv
load_dotenv()
import together  # ✅ Nouveau import

# Charger modèle et scaler
model_local = joblib.load("mon_model.pkl")
scaler = joblib.load("mon_scaler.pkl")

# Configurer Together.ai avec clé API depuis variable d'environnement
client = together.Together(api_key=os.getenv("TOGETHER_API_KEY"))

# Infos utiles
mois_noms = {1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
             7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"}
saison_codes = {0: "Hiver", 1: "Printemps", 2: "Été", 3: "Automne"}
mois_saison = {0: [12, 1, 2], 1: [3, 4, 5], 2: [6, 7, 8], 3: [9, 10, 11]}

def predire_tmax(TMIN, SNOW, SNWD, MONTH, DAYOFYEAR, SEASON):
    data = np.array([[TMIN, SNOW, SNWD, MONTH, DAYOFYEAR, SEASON]])
    scaled = scaler.transform(data)
    prediction = model_local.predict(scaled)[0]
    return round(prediction / 10, 1)

def utiliser_together(question):
    try:
        response = client.chat.completions.create(
            model="meta-llama-3.3-70b-instruct-turbo",
            messages=[
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Erreur Together : {e}"

def analyse_locale(tmin, snow, snwd, mois, jour, saison, tmax):
    texte = f"La dernière prédiction était **{tmax}°C** pour le **{jour} {mois_noms[mois]}** en saison **{saison_codes[saison]}**.\n"
    if tmin < 0:
        texte += f"➡️ Température minimale très basse ({tmin / 10}°C), cela réduit la TMAX.\n"
    if snow > 0:
        texte += f"➡️ Présence de neige ({snow} mm), ce qui est inhabituel en saison {saison_codes[saison]}.\n"
    if saison == 2 and tmax < 10:
        texte += "⚠️ Température anormalement basse pour l'été.\n"
    return texte

# Streamlit App
st.title("🤖 Chatbot météo intelligent (hybride)")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "dernier_resultat" not in st.session_state:
    st.session_state.dernier_resultat = None

# Affichage historique
for role, msg in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(msg)

# Entrée utilisateur
if prompt := st.chat_input("Pose une question météo..."):
    st.session_state.messages.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    reponse = ""

    # 1. D'abord : analyse locale si format reconnu
    match = re.search(r"TMIN=([-]?\d+),?\s*SNOW=(\d+),?\s*SNWD=(\d+),?\s*mois=(\d+),?\s*jour=(\d+),?\s*saison=(\d+)", prompt)
    if match:
        tmin = int(match.group(1))
        snow = int(match.group(2))
        snwd = int(match.group(3))
        mois = int(match.group(4))
        jour = int(match.group(5))
        saison = int(match.group(6))
        tmax = predire_tmax(tmin, snow, snwd, mois, jour, saison)
        st.session_state.dernier_resultat = (tmin, snow, snwd, mois, jour, saison, tmax)
        reponse = f"📈 Température maximale prédite : **{tmax}°C**"
    elif any(mot in prompt.lower() for mot in ["explique", "pourquoi", "raison"]):
        contexte = st.session_state.dernier_resultat
        if contexte:
            tmin, snow, snwd, mois, jour, saison, tmax = contexte
            reponse = analyse_locale(tmin, snow, snwd, mois, jour, saison, tmax)
        else:
            reponse = "❗ Je n'ai pas encore de prédiction à expliquer. Fais d'abord une demande du type `TMIN=-120, ...`"
    else:
        # 2. Sinon, envoyer à Together.ai
        reponse = utiliser_together(prompt)

    st.session_state.messages.append(("assistant", reponse))
    with st.chat_message("assistant"):
        st.markdown(reponse)
