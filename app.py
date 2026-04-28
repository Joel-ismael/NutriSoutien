import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Le Nutri-Soutien",
    page_icon="🥗",
    layout="wide"
)

# --- STYLE PERSONNALISÉ (CSS INJECTÉ) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION DE LA BASE DE DONNÉES TEMPORAIRE ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=["Date", "Patient", "Âge", "Poids", "Taille", "IMC", "Statut"])

# --- LOGIQUE BACKEND : CALCULS MÉDICAUX ---
def interpreter_imc(imc):
    if imc < 18.5: return "Insuffisance pondérale", "🔴"
    elif 18.5 <= imc < 25: return "Poids normal", "🟢"
    elif 25 <= imc < 30: return "Surpoids", "🟡"
    else: return "Obésité", "🟠"

# --- INTERFACE FRONTEND ---
st.title("🥗 Le Nutri-Soutien : Diagnostic Nutritionnel")
st.write("Plateforme de collecte de données pour le suivi de la santé communautaire.")

# --- ZONE DE COLLECTE (SIDEBAR) ---
with st.sidebar:
    st.header("📥 Nouvelle Collecte")
    with st.form("form_patient"):
        nom = st.text_input("Identifiant du Patient")
        age = st.number_input("Âge (ans)", 0, 110, 25)
        poids = st.number_input("Poids (kg)", 2.0, 200.0, 65.0)
        taille = st.number_input("Taille (cm)", 50, 230, 170)
        date = st.date_input("Date de visite", datetime.now())
        
        submit = st.form_submit_button("Enregistrer le diagnostic")

    if submit and nom:
        # Calcul du Backend
        imc_calc = round(poids / ((taille/100)**2), 2)
        statut, emoji = interpreter_imc(imc_calc)
        
        # Ajout à la base de données
        nouvelle_entree = pd.DataFrame([[date, nom, age, poids, taille, imc_calc, statut]], 
                                       columns=st.session_state.db.columns)
        st.session_state.db = pd.concat([st.session_state.db, nouvelle_entree], ignore_index=True)
        st.success(f"Enregistré : {statut} {emoji}")

# --- AFFICHAGE DE L'ANALYSE (DASHBOARD) ---
if not st.session_state.db.empty:
    df = st.session_state.db

    # Ligne d'indicateurs clés
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Total Patients", len(df))
    with m2: st.metric("IMC Moyen", round(df["IMC"].mean(), 2))
    with m3: st.metric("Alertes (Insuffisance)", len(df[df["IMC"] < 18.5]))

# Graphiques d'Analyse Descriptive (Version Corrigée)
    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📊 Répartition par Statut")
        if not df["Statut"].empty:
            fig_pie = px.pie(df, names="Statut", hole=0.4, 
                             color="Statut",
                             color_discrete_map={
                                 "Poids normal":"#2ecc71", 
                                 "Insuffisance pondérale":"#e74c3c", 
                                 "Surpoids":"#f1c40f", 
                                 "Obésité":"#e67e22"
                             })
            st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.subheader("📈 Évolution du Poids")
        # Correction : on vérifie que IMC est bien numérique et on gère les tailles
        if not df.empty:
            try:
                # On force l'IMC en numérique pour éviter le ValueError
                df["IMC"] = pd.to_numeric(df["IMC"])
                fig_line = px.scatter(df, x="Date", y="Poids", 
                                    size="IMC", color="Statut", 
                                    hover_name="Patient",
                                    size_max=30) # size_max aide à la stabilité
                st.plotly_chart(fig_line, use_container_width=True)
            except Exception as e:
                st.error("Erreur d'affichage du graphique : données insuffisantes.")
