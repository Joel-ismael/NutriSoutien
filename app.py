import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import re
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Nutri-Soutien Cloud", page_icon="🥗", layout="wide")

# --- STYLE CSS (Pour masquer GitHub) ---
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
    # Table des utilisateurs
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, firstname TEXT, lastname TEXT, 
                phone TEXT, password TEXT, sex TEXT, nationality TEXT)''')
    # Table des collectes (Liée à l'email de l'utilisateur)
    c.execute('''CREATE TABLE IF NOT EXISTS collectes (
                id_collecte TEXT, user_email TEXT, date TEXT, patient TEXT, 
                age INTEGER, poids REAL, taille REAL, imc REAL, statut TEXT)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- FONCTIONS DE SÉCURITÉ ---
def hash_pwd(pwd):
    return hashlib.sha256(str.encode(pwd)).hexdigest()

def check_phone(phone, code):
    # Vérifie si le numéro commence par le code pays
    return phone.startswith(code)

# --- LOGIQUE DE L'APPLICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""

def main():
    if not st.session_state.logged_in:
        menu = ["Connexion", "Inscription"]
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Inscription":
            st.subheader("📝 Créer un compte professionnel")
            col1, col2 = st.columns(2)
            
            with col1:
                nom = st.text_input("Nom")
                prenom = st.text_input("Prénom")
                email = st.text_input("Adresse Email")
                sex = st.selectbox("Sexe", ["Masculin", "Féminin", "Autre"])
            
            with col2:
                countries = {"Cameroun": "+237", "Gabon": "+241", "Sénégal": "+221", "Côte d'Ivoire": "+225", "France": "+33"}
                nat = st.selectbox("Nationalité", list(countries.keys()))
                code = countries[nat]
                phone = st.text_input(f"Téléphone (Doit commencer par {code})")
                pwd = st.text_input("Mot de passe", type='password', help="Majuscule, minuscule, chiffre requis")

            if st.button("S'inscrire"):
                # Validation robuste
                if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    st.error("Email invalide.")
                elif not check_phone(phone, code):
                    st.error(f"Le numéro doit commencer par {code}")
                elif len(pwd) < 6:
                    st.error("Mot de passe trop court.")
                else:
                    try:
                        c.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?)', 
                                 (email, prenom, nom, phone, hash_pwd(pwd), sex, nat))
                        conn.commit()
                        st.success("Compte créé avec succès ! Veuillez vous connecter.")
                    except:
                        st.error("Cet email est déjà utilisé.")

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
        # --- L'UTILISATEUR EST CONNECTÉ ---
        st.sidebar.title(f"👤 {st.session_state.user_name}")
        page = st.sidebar.radio("Navigation", ["Collecte & Dashboard", "Mon Profil", "Déconnexion"])

        if page == "Déconnexion":
            st.session_state.logged_in = False
            st.rerun()

        elif page == "Mon Profil":
            st.subheader("⚙️ Paramètres du profil")
            c.execute('SELECT * FROM users WHERE email=?', (st.session_state.user_email,))
            u = c.fetchone()
            
            with st.form("update_profile"):
                new_fname = st.text_input("Prénom", value=u[1])
                new_lname = st.text_input("Nom", value=u[2])
                new_phone = st.text_input("Téléphone", value=u[3])
                if st.form_submit_button("Mettre à jour"):
                    c.execute('UPDATE users SET firstname=?, lastname=?, phone=? WHERE email=?', 
                             (new_fname, new_lname, new_phone, st.session_state.user_email))
                    conn.commit()
                    st.success("Profil mis à jour !")
                    st.rerun()

        elif page == "Collecte & Dashboard":
            # --- CODE DE COLLECTE PRÉCÉDENT MAIS LIÉ À L'UTILISATEUR ---
            tab1, tab2 = st.tabs(["📥 Saisie", "📊 Historique"])
            
            with tab1:
                with st.form("collecte"):
                    pid = st.text_input("ID Patient")
                    p_nom = st.text_input("Nom Patient")
                    p_poids = st.number_input("Poids (kg)", 2.0, 200.0, 60.0)
                    p_taille = st.number_input("Taille (cm)", 50, 250, 170)
                    if st.form_submit_button("Sauvegarder"):
                        imc = round(p_poids / ((p_taille/100)**2), 2)
                        status = "Normal" if 18.5 <= imc < 25 else "Alerte"
                        c.execute('INSERT INTO collectes VALUES (?,?,?,?,?,?,?,?,?)',
                                 (pid, st.session_state.user_email, str(datetime.now().date()), p_nom, 25, p_poids, p_taille, imc, status))
                        conn.commit()
                        st.success("Données enregistrées en base !")

           with tab2:
                # On ne lit que les données de l'utilisateur connecté
                c.execute('SELECT * FROM collectes WHERE user_email=?', (st.session_state.user_email,))
                my_data = pd.DataFrame(c.fetchall(), columns=["ID", "User", "Date", "Patient", "Âge", "Poids", "Taille", "IMC", "Statut"])
                
                if not my_data.empty:
                    st.subheader("📋 Historique des patients")
                    st.dataframe(my_data, use_container_width=True)
                    
                    # --- NOUVEAU : AJOUT DU PIE CHART ---
                    st.divider()
                    st.subheader("📊 Répartition Nutritionnelle Globale")
                    
                    # Création du graphique avec des couleurs fixes pour la cohérence
                    fig_pie = px.pie(
                        my_data, 
                        names="Statut", 
                        hole=0.4, # Transforme le camembert en "Doughnut" plus moderne
                        color="Statut",
                        color_discrete_map={
                            "Normal": "#2ecc71", # Vert
                            "Alerte": "#e74c3c", # Rouge
                            "Obésité": "#e67e22",# Orange
                            "Surpoids": "#f1c40f" # Jaune
                        }
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("Vous n'avez pas encore enregistré de patients.")

if __name__ == '__main__':
    main()
