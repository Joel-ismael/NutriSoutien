import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Nutri-Soutien Cloud", page_icon="🥗", layout="wide")

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    .welcome-msg {
        background-color: #e8f5e9;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #2ecc71;
        font-size: 14px;
        color: #1b5e20;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('nutrisoutien_official.db', check_same_thread=False)
    c = conn.cursor()
    # Table des membres
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, nom TEXT, prenom TEXT, 
                dob TEXT, pays TEXT, phone TEXT, sex TEXT, password TEXT)''')
    # Table des saisies de données
    c.execute('''CREATE TABLE IF NOT EXISTS data_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, 
                date TEXT, patient TEXT, poids REAL, taille REAL, imc REAL, statut TEXT)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

def hash_pwd(pwd):
    return hashlib.sha256(str.encode(pwd)).hexdigest()

# --- GESTION DE SESSION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""

# --- APPLICATION PRINCIPALE ---
def main():
    # BARRE LATÉRALE DE NAVIGATION (Toujours visible)
    st.sidebar.title("🥗 Nutri-Soutien")
    
    if not st.session_state.logged_in:
        # MENU AUTHENTIFICATION
        st.sidebar.subheader("Menu")
        auth_mode = st.sidebar.radio("Sélectionnez une option :", ["Connexion", "Inscription"])
        
        # Message de bienvenue en bas du menu
        st.sidebar.markdown("---")
        st.sidebar.markdown("""
            <div class='welcome-msg'>
                ✅ <b>Logiciel Officiel</b><br>
                Bienvenue sur la plateforme sécurisée Nutri-Soutien.
            </div>
            """, unsafe_allow_html=True)

        if auth_mode == "Inscription":
            st.header("📝 Formulaire d'adhésion")
            col1, col2 = st.columns(2)
            
            with col1:
                nom = st.text_input("Nom")
                prenom = st.text_input("Prénom")
                dob = st.date_input("Date de naissance", min_value=datetime(1930, 1, 1))
                sex = st.selectbox("Sexe", ["Masculin", "Féminin", "Autre"])
            
            with col2:
                # Dictionnaire des pays et indicatifs
                pays_list = {"Cameroun": "+237", "Gabon": "+241", "Sénégal": "+221", "Côte d'Ivoire": "+225", "France": "+33"}
                pays_choisi = st.selectbox("Pays de résidence", list(pays_list.keys()))
                indicatif = pays_list[pays_choisi]
                
                phone = st.text_input(f"Téléphone (Indicatif {indicatif} obligatoire)", value=indicatif)
                email = st.text_input("Adresse Email")
                pwd = st.text_input("Définir un mot de passe", type='password')

            if st.button("Valider l'inscription"):
                if not phone.startswith(indicatif):
                    st.error(f"Erreur : Le numéro pour le {pays_choisi} doit commencer par {indicatif}")
                elif len(pwd) < 4:
                    st.error("Le mot de passe est trop court.")
                elif not (email and nom and prenom):
                    st.warning("Veuillez remplir les informations obligatoires.")
                else:
                    try:
                        c.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?)', 
                                 (email, nom, prenom, str(dob), pays_choisi, phone, sex, hash_pwd(pwd)))
                        conn.commit()
                        st.success("✅ Inscription réussie ! Basculez sur 'Connexion' à gauche pour entrer.")
                    except:
                        st.error("Cet email est déjà enregistré.")

        else: # MODE CONNEXION
            st.header("🔑 Accès à la plateforme")
            c_nom = st.text_input("Nom de famille")
            c_prenom = st.text_input("Prénom")
            c_pwd = st.text_input("Mot de passe", type='password')
            
            if st.button("Accéder à l'application"):
                c.execute('SELECT email FROM users WHERE nom=? AND prenom=? AND password=?', 
                         (c_nom, c_prenom, hash_pwd(c_pwd)))
                result = c.fetchone()
                if result:
                    st.session_state.logged_in = True
                    st.session_state.user_email = result[0]
                    st.session_state.user_name = f"{c_prenom} {c_nom}"
                    st.rerun()
                else:
                    st.error("❌ Identifiants introuvables ou incorrects.")

    else:
        # INTERFACE UNE FOIS CONNECTÉ
        st.sidebar.success(f"Utilisateur : {st.session_state.user_name}")
        page = st.sidebar.selectbox("Navigation", ["📥 Saisie de données", "📊 Mon Historique", "🚪 Déconnexion"])

        if page == "Déconnexion":
            st.session_state.logged_in = False
            st.rerun()

        elif page == "📥 Saisie de données":
            st.header("Enregistrement des données nutritionnelles")
            with st.form("saisie_patient"):
                p_nom = st.text_input("Nom du Patient")
                p_poids = st.number_input("Poids (kg)", 1.0, 200.0, 70.0)
                p_taille = st.number_input("Taille (cm)", 50, 250, 170)
                
                if st.form_submit_button("Sauvegarder dans ma base"):
                    imc = round(p_poids / ((p_taille/100)**2), 2)
                    statut = "Normal" if 18.5 <= imc < 25 else "Alerte"
                    c.execute('INSERT INTO data_records (user_email, date, patient, poids, taille, imc, statut) VALUES (?,?,?,?,?,?,?)',
                             (st.session_state.user_email, str(datetime.now().date()), p_nom, p_poids, p_taille, imc, statut))
                    conn.commit()
                    st.success(f"Données sauvegardées pour {p_nom}. Statut : {statut}")

        elif page == "📊 Mon Historique":
            st.header("Vos archives de collecte")
            c.execute('SELECT date, patient, poids, taille, imc, statut FROM data_records WHERE user_email=?', (st.session_state.user_email,))
            data = c.fetchall()
            if data:
                df = pd.DataFrame(data, columns=["Date", "Patient", "Poids", "Taille", "IMC", "Statut"])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Aucune donnée enregistrée pour le moment.")

if __name__ == '__main__':
    main()