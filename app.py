import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Nutri-Soutien Pro", page_icon="🥗", layout="wide")

# --- INITIALISATION ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=["ID", "Date", "Patient", "Âge", "Poids", "Taille", "IMC", "Statut"])

# --- FONCTIONS LOGIQUES ---
def calculer_imc(poids, taille):
    imc = poids / ((taille/100)**2)
    if imc < 18.5: status = "Insuffisance pondérale"
    elif 18.5 <= imc < 25: status = "Poids normal"
    elif 25 <= imc < 30: status = "Surpoids"
    else: status = "Obésité"
    return round(imc, 2), status

# --- INTERFACE ---
st.title("🥗 Gestion du Nutri-Soutien")

# Création des onglets pour une navigation professionnelle
tab1, tab2, tab3 = st.tabs(["📥 Collecte & Dashboard", "🔍 Recherche & Gestion", "📊 Analyse Globale"])

# --- ONGLET 1 : COLLECTE ---
with tab1:
    st.subheader("Enregistrement des données")
    with st.form("ajout_patient"):
        col1, col2 = st.columns(2)
        with col1:
            id_p = st.text_input("Identifiant Unique (ID)")
            nom = st.text_input("Nom Complet")
            age = st.number_input("Âge", 0, 110, 25)
        with col2:
            poids = st.number_input("Poids (kg)", 2.0, 200.0, 65.0)
            taille = st.number_input("Taille (cm)", 50, 230, 170)
            date = st.date_input("Date", datetime.now())
        
        btn_save = st.form_submit_button("Enregistrer")

    if btn_save:
        if id_p in st.session_state.db["ID"].values:
            st.error("Cet ID existe déjà ! Utilisez l'onglet Gestion pour modifier.")
        elif id_p and nom:
            imc, status = calculer_imc(poids, taille)
            new_data = pd.DataFrame([[id_p, date, nom, age, poids, taille, imc, status]], columns=st.session_state.db.columns)
            st.session_state.db = pd.concat([st.session_state.db, new_data], ignore_index=True)
            st.success(f"Patient {nom} enregistré avec succès !")

# --- ONGLET 2 : RECHERCHE, MODIFIER, SUPPRIMER ---
with tab2:
    st.subheader("Gestion des dossiers patients")
    search_id = st.text_input("Entrez l'ID du patient pour rechercher")
    
    if search_id:
        patient_data = st.session_state.db[st.session_state.db["ID"] == search_id]
        
        if not patient_data.empty:
            st.write("### Données actuelles :")
            st.dataframe(patient_data)
            
            # --- MODIFICATION ---
            st.divider()
            st.write("#### Modifier les informations")
            with st.expander("Cliquez ici pour modifier"):
                with st.form("edit_form"):
                    new_nom = st.text_input("Nouveau Nom", value=patient_data["Patient"].values[0])
                    new_poids = st.number_input("Nouveau Poids", value=float(patient_data["Poids"].values[0]))
                    new_taille = st.number_input("Nouvelle Taille", value=int(patient_data["Taille"].values[0]))
                    btn_update = st.form_submit_button("Mettre à jour")
                    
                    if btn_update:
                        new_imc, new_status = calculer_imc(new_poids, new_taille)
                        st.session_state.db.loc[st.session_state.db["ID"] == search_id, ["Patient", "Poids", "Taille", "IMC", "Statut"]] = [new_nom, new_poids, new_taille, new_imc, new_status]
                        st.success("Données mises à jour !")
                        st.rerun()

            # --- SUPPRESSION ---
            st.divider()
            if st.button("❌ Supprimer définitivement ce patient"):
                st.session_state.db = st.session_state.db[st.session_state.db["ID"] != search_id]
                st.warning("Patient supprimé.")
                st.rerun()
        else:
            st.info("Aucun patient trouvé avec cet ID.")

# --- ONGLET 3 : ANALYSE GLOBALE ---
with tab3:
    if not st.session_state.db.empty:
        st.subheader("Vue d'ensemble de la population")
        st.dataframe(st.session_state.db, use_container_width=True)
        
        fig = px.pie(st.session_state.db, names="Statut", title="Répartition Nutritionnelle")
        st.plotly_chart(fig)
    else:
        st.info("La base de données est vide.")
