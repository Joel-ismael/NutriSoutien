import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import re
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Nutri-Soutien Cloud", page_icon="🥗", layout="wide")

# --- STYLE CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION SQLITE ---
def init_db():
    conn = sqlite3.connect('nutrisoutien_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, firstname TEXT, lastname TEXT, 
                phone TEXT, password TEXT, sex TEXT, nationality TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS collectes (
                id_collecte TEXT, user_email TEXT, date TEXT, patient TEXT, 
                age INTEGER, poids REAL, taille REAL, imc REAL, statut TEXT)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

def hash_pwd(pwd):
    return hashlib.sha256(str.encode(pwd)).hexdigest()

# --- LOGIQUE PRINCIPALE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def main():
    # 1. ON FORCE L'AFFICHAGE DU MENU DANS LA SIDEBAR
    st.sidebar.title("📌 Navigation")
    
    if not st.session_state.logged_in:
        # MENU POUR LES VISITEURS (Inscription/Connexion)
        choice = st.sidebar.selectbox("Menu", ["Connexion", "Inscription"])

        if choice == "Inscription":
            st.subheader("📝 Créer un compte professionnel")
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nom")
                prenom = st.text_input("Prénom")
                email = st.text_input("Email")
            with col2:
                phone = st.text_input("Téléphone")
                pwd = st.text_input("Mot de passe", type='password')
            
            if st.button("S'inscrire"):
                try:
                    c.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?)', 
                             (email, prenom, nom, phone, hash_pwd(pwd), "M", "Cameroun"))
                    conn.commit()
                    st.success("Compte créé ! Connectez-vous.")
                except:
                    st.error("Erreur ou email déjà utilisé.")

        else:
            st.subheader("🔑 Connexion")
            login_email = st.text_input("Email")
            login_pwd = st.text_input("Mot de passe", type='password')
            if st.button("Se connecter"):
                c.execute('SELECT * FROM users WHERE email=? AND password=?', (login_email, hash_pwd(login_pwd)))
                data = c.fetchone()
                if data:
                    st.session_state.logged_in = True
                    st.session_state.user_email = login_email
                    st.session_state.user_name = f"{data[1]} {data[2]}"
                    st.rerun()
                else:
                    st.error("Email ou mot de passe incorrect.")

    else:
        # MENU POUR LES CONNECTÉS
        st.sidebar.write(f"Connecté : **{st.session_state.user_name}**")
        page = st.sidebar.radio("Aller vers", ["Collecte & Dashboard", "Mon Profil", "Déconnexion"])

        if page == "Déconnexion":
            st.session_state.logged_in = False
            st.rerun()

        elif page == "Collecte & Dashboard":
            tab1, tab2 = st.tabs(["📥 Saisie", "📊 Historique"])
            with tab1:
                with st.form("form_collecte"):
                    p_nom = st.text_input("Nom Patient")
                    p_poids = st.number_input("Poids (kg)", 20.0, 200.0, 70.0)
                    p_taille = st.number_input("Taille (cm)", 100, 250, 170)
                    if st.form_submit_button("Enregistrer"):
                        imc = round(p_poids / ((p_taille/100)**2), 2)
                        statut = "Normal" if 18.5 <= imc < 25 else "Alerte"
                        c.execute('INSERT INTO collectes VALUES (?,?,?,?,?,?,?,?,?)',
                                 ("ID", st.session_state.user_email, str(datetime.now().date()), p_nom, 25, p_poids, p_taille, imc, statut))
                        conn.commit()
                        st.success("Enregistré !")

            with tab2:
                c.execute('SELECT * FROM collectes WHERE user_email=?', (st.session_state.user_email,))
                df = pd.DataFrame(c.fetchall(), columns=["ID", "User", "Date", "Patient", "Âge", "Poids", "Taille", "IMC", "Statut"])
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    fig = px.pie(df, names="Statut", hole=0.4, color="Statut",
                                 color_discrete_map={"Normal": "#2ecc71", "Alerte": "#e74c3c", "Surpoids": "#f1c40f", "Obésité": "#e67e22"})
                    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()