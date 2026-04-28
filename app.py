import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import re
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Nutri-Soutien", page_icon="🥗", layout="wide")

# --- STYLE CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    .welcome-text { text-align: center; color: #2ecc71; font-weight: bold; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('nutri_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, nom TEXT, prenom TEXT, 
                dob TEXT, pays TEXT, phone TEXT, sex TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS collectes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, 
                date TEXT, patient TEXT, imc REAL, statut TEXT)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

def hash_pwd(pwd):
    return hashlib.sha256(str.encode(pwd)).hexdigest()

# --- INITIALISATION SESSION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""

# --- LOGIQUE PRINCIPALE ---
def main():
    # BARRE LATÉRALE (Toujours visible)
    st.sidebar.title("📌 Menu Principal")
    
    if not st.session_state.logged_in:
        auth_mode = st.sidebar.radio("Navigation", ["Connexion", "Inscription"])
        
        # Message de bienvenue en bas de la sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown("<div class='welcome-text'>✅ Bienvenue sur l'application officielle Nutri-Soutien Cloud.</div>", unsafe_allow_html=True)

        if auth_mode == "Inscription":
            st.header("📝 Créer votre compte")
            col1, col2 = st.columns(2)
            
            with col1:
                nom = st.text_input("Nom")
                prenom = st.text_input("Prénom")
                dob = st.date_input("Date de naissance", min_value=datetime(1940, 1, 1))
                sex = st.selectbox("Sexe", ["Masculin", "Féminin", "Autre"])
            
            with col2:
                # Dictionnaire des codes pays
                pays_codes = {"Cameroun": "+237", "Gabon": "+241", "Sénégal": "+221", "France": "+33", "Côte d'Ivoire": "+225"}
                pays_sel = st.selectbox("Pays", list(pays_codes.keys()))
                code_pays = pays_codes[pays_sel]
                phone = st.text_input(f"Téléphone (Doit commencer par {code_pays})")
                email = st.text_input("Adresse Email")
                pwd = st.text_input("Créer un mot de passe", type='password')

            if st.button("S'inscrire"):
                if not phone.startswith(code_pays):
                    st.error(f"Le numéro pour le {pays_sel} doit commencer par {code_pays}")
                elif not (email and nom and pwd):
                    st.warning("Veuillez remplir tous les champs.")
                else:
                    try:
                        c.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?)', 
                                 (email, nom, prenom, str(dob), pays_sel, phone, sex, hash_pwd(pwd)))
                        conn.commit()
                        st.success("Compte créé ! Vous pouvez maintenant vous connecter dans le menu à gauche.")
                    except:
                        st.error("Cet email est déjà utilisé.")

        else: # Mode Connexion
            st.header("🔑 Connexion")
            # Comme demandé : Nom, Prénom et Mot de passe
            c_nom = st.text_input("Nom")
            c_prenom = st.text_input("Prénom")
            c_pwd = st.text_input("Mot de passe", type='password')
            
            if st.button("Accéder à la plateforme"):
                c.execute('SELECT email FROM users WHERE nom=? AND prenom=? AND password=?', 
                         (c_nom, c_prenom, hash_pwd(c_pwd)))
                user = c.fetchone()
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_email = user[0]
                    st.session_state.user_name = f"{c_prenom} {c_nom}"
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")

    else:
        # --- UTILISATEUR CONNECTÉ ---
        st.sidebar.success(f"Connecté : {st.session_state.user_name}")
        app_page = st.sidebar.radio("Navigation", ["Saisie de données", "Historique", "Déconnexion"])

        if app_page == "Déconnexion":
            st.session_state.logged_in = False
            st.rerun()

        elif app_page == "Saisie de données":
            st.header("📥 Enregistrement Patient")
            with st.form("data_form"):
                p_nom = st.text_input("Nom du patient")
                p_poids = st.number_input("Poids (kg)", 1.0, 250.0, 70.0)
                p_taille = st.number_input("Taille (cm)", 40, 250, 170)
                if st.form_submit_button("Sauvegarder"):
                    imc = round(p_poids / ((p_taille/100)**2), 2)
                    statut = "Normal" if 18.5 <= imc < 25 else "Alerte"
                    c.execute('INSERT INTO collectes (user_email, date, patient, imc, statut) VALUES (?,?,?,?,?)',
                             (st.session_state.user_email, str(datetime.now().date()), p_nom, imc, statut))
                    conn.commit()
                    st.success(f"Données enregistrées pour {p_nom}")

        elif app_page == "Historique":
            st.header("📊 Vos anciennes données")
            c.execute('SELECT date, patient, imc, statut FROM collectes WHERE user_email=?', (st.session_state.user_email,))
            df = pd.DataFrame(c.fetchall(), columns=["Date", "Patient", "IMC", "Statut"])
            if not df.empty:
                st.table(df)
            else:
                st.info("Aucune donnée enregistrée.")

if __name__ == '__main__':
    main()
