import streamlit as st

st.set_page_config(page_title="🌦️ Application Météo", layout="centered")

# Menu de navigation
page = st.sidebar.selectbox("Choisir un mode", ["🧮 Mode Formulaire", "🤖 Mode Chatbot"])

if page == "🧮 Mode Formulaire":
    exec(open("formulaire.py", encoding="utf-8").read())


elif page == "🤖 Mode Chatbot":
    exec(open("chatbot.py", encoding="utf-8").read())
