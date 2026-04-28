import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import re
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Nutri-Soutien Cloud", page_icon="🥗", layout="wide")

# --- STYLE CSS POUR NETTOYER L'INTERFACE ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    /* Force la sidebar à être visible */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('nutrisoutien_data.db', check_same_thread=False)
    c = conn.cursor()
    # Table Utilisateurs
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, firstname TEXT, lastname TEXT, 
                phone TEXT, password TEXT, sex TEXT, nationality TEXT)''')
    # Table Collectes
    c.execute('''CREATE TABLE IF NOT EXISTS collectes (
                id_collecte TEXT, user_email TEXT, date TEXT, patient TEXT, 
                age INTEGER, poids REAL, taille REAL, imc REAL, statut TEXT)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- SÉCURITÉ ---
def hash_pwd(pwd):
    return hashlib.sha256(str.encode(pwd)).hexdigest()

# --- INITIALISATION DE LA SESSION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""

def main():
    # --- BARRE LATÉRALE (SIDEBAR) ---
    st.sidebar.title("🥗 Nutri-Soutien")
    
    if not st.session_state.logged_in:
        # CE MENU S'AFFICHE QUAND ON N'EST PAS CONNECTÉ
        st.sidebar.subheader("Accès Professionnel")
        auth_choice = st.sidebar.radio("Choisir une action :", ["Connexion", "Inscription"])

        if auth_choice == "Inscription":
            st.subheader("📝 Créer un compte professionnel")
            col1, col2 = st.columns(2)
            
            with col1:
                nom = st.text_input("Nom")
                prenom = st.text_input("Prénom")
                email = st.text_input("Adresse Email")
                sexe = st.selectbox("Sexe", ["Masculin", "Féminin"])
            
            with col2:
                pays = {"Cameroun": "+237", "Gabon": "+241", "Sénégal": "+221", "France": "+33"}
                nat = st.selectbox("Pays de résidence", list(pays.keys()))
                phone = st.text_input(f"Téléphone ({pays[nat]})")
                pwd = st.text_input("Mot de passe", type='password')

            if st.button("Valider l'inscription"):
                if email and pwd and nom:
                    try:
                        c.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?)', 
                                 (email, prenom, nom, phone, hash_pwd(pwd), sexe, nat))
                        conn.commit()
                        st.success("Compte créé ! Sélectionnez 'Connexion' dans le menu à gauche.")
                    except:
                        st.error("Cet email est déjà enregistré.")
                else:
                    st.warning("Veuillez remplir les champs obligatoires.")

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
        # --- MENU QUAND L'UTILISATEUR EST CONNECTÉ ---
        st.sidebar.success(f"Bienvenue, {st.session_state.user_name}")
        page = st.sidebar.radio("Navigation", ["Collecte & Dashboard", "Mon Profil", "Déconnexion"])

        if page == "Déconnexion":
            st.session_state.logged_in = False
            st.rerun()

        elif page == "Mon Profil":
            st.subheader("⚙️ Paramètres du compte")
            c.execute('SELECT * FROM users WHERE email=?', (st.session_state.user_email,))
            u = c.fetchone()
            st.info(f"Email : {u[0]} | Nom : {u[2]} | Téléphone : {u[3]}")

        elif page == "Collecte & Dashboard":
            tab1, tab2 = st.tabs(["📥 Saisie de données", "📊 Historique & Analyse"])
            
            with tab1:
                st.subheader("Nouveau Patient")
                with st.form("form_saisie"):
                    p_nom = st.text_input("Nom du patient")
                    p_poids = st.number_input("Poids (kg)", 1.0, 250.0, 70.0)
                    p_taille = st.number_input("Taille (cm)", 40, 250, 170)
                    submit = st.form_submit_button("Enregistrer")
                    
                    if submit:
                        imc = round(p_poids / ((p_taille/100)**2), 2)
                        statut = "Normal" if 18.5 <= imc < 25 else "Alerte"
                        c.execute('INSERT INTO collectes VALUES (?,?,?,?,?,?,?,?,?)',
                                 ("ID", st.session_state.user_email, str(datetime.now().date()), p_nom, 25, p_poids, p_taille, imc, statut))
                        conn.commit()
                        st.success(f"Patient enregistré ! IMC : {imc}")

            with tab2:
                c.execute('SELECT * FROM collectes WHERE user_email=?', (st.session_state.user_email,))
                df = pd.DataFrame(c.fetchall(), columns=["ID", "User", "Date", "Patient", "Âge", "Poids", "Taille", "IMC", "Statut"])
                
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    st.divider()
                    fig = px.pie(df, names="Statut", hole=0.4, title="Répartition des statuts",
                                 color="Statut", color_discrete_map={"Normal": "#2ecc71", "Alerte": "#e74c3c"})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Aucune donnée enregistrée pour le moment.")

if __name__ == '__main__':
    main()