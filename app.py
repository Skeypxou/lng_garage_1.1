# ==========================================
# LNS GARAGE PRO - APPLICATION COMPLÈTE
# Design ERP Premium & JSONDB (Fichier Unique)
# ==========================================

import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import hashlib
import shutil
from datetime import date, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import qrcode
from PIL import Image
import io
import time

# ==========================================
# 1. MOTEUR BASE DE DONNÉES JSONDB INTÉGRÉ
# ==========================================
DB_DIR = "database"
BACKUP_DIR = os.path.join(DB_DIR, "backups")

SCHEMA = {
    "clients": [], "vehicules": [], "devis": [], "factures": [], "reparations": [],
    "stock": [], "accessoires": [], "pieces": [], "assurances": [], "paiements": [],
    "fournisseurs": [], "utilisateurs": [], "parametres": {},
    "counters": {
        "dernier_client": 0, "dernier_vehicule": 0, "dernier_devis": 0,
        "derniere_facture": 0, "dernier_reparation": 0
    },
    "reception": [], "suivi_atelier": [], "achats": [], "employes": [], "photos": [], "documents": []
}

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for entity, default in SCHEMA.items():
        path = os.path.join(DB_DIR, f"{entity}.json")
        if not os.path.exists(path):
            _save_raw(entity, default)
    users = load_data("utilisateurs")
    if not any(u.get("role") == "Administrateur" for u in users):
        hashed_pw = hashlib.sha256("admin123".encode()).hexdigest()
        create_record("utilisateurs", {"nom": "Admin LNS", "username": "admin", "password_hash": hashed_pw, "role": "Administrateur"})

def _get_path(entity):
    return os.path.join(DB_DIR, f"{entity}.json")

def _save_raw(entity, data):
    path = _get_path(entity)
    temp_path = path + ".tmp"
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    with open(temp_path, 'r', encoding='utf-8') as f:
        json.load(f)
    os.replace(temp_path, path)

def load_data(entity):
    path = _get_path(entity)
    if not os.path.exists(path):
        return [] if isinstance(SCHEMA.get(entity), list) else {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(entity, data):
    path = _get_path(entity)
    if os.path.exists(path):
        backup_name = f"{entity}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy(path, os.path.join(BACKUP_DIR, backup_name))
    _save_raw(entity, data)

def get_next_id(entity):
    data = load_data(entity)
    if not data: return 1
    return max(item.get("id", 0) for item in data) + 1

def create_record(entity, record):
    data = load_data(entity)
    record["id"] = get_next_id(entity)
    data.append(record)
    save_data(entity, data)
    return record["id"]

def update_record(entity, record_id, updates):
    data = load_data(entity)
    for item in data:
        if item.get("id") == record_id:
            item.update(updates)
            break
    save_data(entity, data)

def delete_record(entity, record_id):
    data = load_data(entity)
    data = [item for item in data if item.get("id") != record_id]
    save_data(entity, data)

def get_record(entity, record_id):
    data = load_data(entity)
    for item in data:
        if item.get("id") == record_id:
            return item
    return None

def get_all_records(entity):
    return load_data(entity)

def get_next_numero(entity_type):
    counters = load_data("counters")
    year = datetime.now().year
    if entity_type == "devis":
        counters["dernier_devis"] += 1
        prefix = f"DEV-{year}-{counters['dernier_devis']:04d}"
    elif entity_type == "facture":
        counters["derniere_facture"] += 1
        prefix = f"FAC-{year}-{counters['derniere_facture']:04d}"
    else:
        return "NUM-0000"
    save_data("counters", counters)
    return prefix

def get_df(entity):
    return pd.DataFrame(get_all_records(entity))

# Initialisation au lancement
init_db()

# ==========================================
# 2. CONFIGURATION & DESIGN PREMIUM
# ==========================================
st.set_page_config(page_title="LNS GARAGE PRO", page_icon="🚗", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    :root {
        --primary-color: #1E3A8A; --secondary-color: #3B82F6; --bg-color: #F8FAFC;
        --text-color: #1E293B; --card-bg: #FFFFFF; --border-radius: 12px;
    }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--text-color); }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }
    
    /* === SIDEBAR BLANC CASSÉ === */
    [data-testid="stSidebar"] {
        background: #F8FAFC; color: #1E293B; border-right: 1px solid #E2E8F0;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
        color: #334155 !important;
    }
    [data-testid="stSidebar"] hr { border-color: #E2E8F0; }
    [data-testid="stSidebar"] [role="radiogroup"] { gap: 8px; width: 100%; }
    [data-testid="stSidebar"] [role="radio"] {
        padding: 12px 16px; border-radius: 8px; border: 1px solid #E2E8F0;
        background-color: #FFFFFF; transition: all 0.3s ease; display: flex; align-items: center; color: #475569;
    }
    [data-testid="stSidebar"] [role="radio"]:hover { background-color: #F1F5F9; border-color: #CBD5E1; }
    [data-testid="stSidebar"] [role="radio"][aria-checked="true"] {
        background-color: #1E3A8A; border-color: #1E3A8A; color: #FFFFFF !important;
        box-shadow: 0 4px 6px rgba(30, 58, 138, 0.2); font-weight: 600;
    }
    [data-testid="stSidebar"] [role="radio"][aria-checked="true"] svg { fill: white; }

    .stButton>button { background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); color: white; border-radius: 8px; border: none; padding: 10px 24px; font-weight: 600; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 4px 6px rgba(30, 58, 138, 0.2); width: 100%; }
    .stButton>button:hover { transform: translateY(-1px); box-shadow: 0 6px 12px rgba(30, 58, 138, 0.3); color: white; }
    .stButton>button[kind="secondary"] { background: #F1F5F9; color: #1E293B; border: 1px solid #E2E8F0; box-shadow: none; }
    
    .kpi-card { background-color: var(--card-bg); border-radius: var(--border-radius); padding: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border-top: 4px solid var(--primary-color); transition: transform 0.2s, box-shadow 0.2s; }
    .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px rgba(0,0,0,0.1); }
    .kpi-card h3 { color: #64748B; font-size: 1.1rem; font-weight: 500; margin-bottom: 0.5rem; }
    .kpi-card h1 { color: var(--primary-color); font-size: 2.5rem; font-weight: 800; margin: 0; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 4px; background-color: #F1F5F9; padding: 6px; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; border-radius: 8px; color: #64748B; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: var(--card-bg); color: var(--primary-color); box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stDataFrame { border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden; }
    .stExpander { border: 1px solid #E2E8F0; border-radius: 12px; background-color: #FFFFFF; }
    h1, h2, h3 { color: var(--text-color) !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

COLOR_PALETTE = ['#1E3A8A', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#10B981', '#34D399']

# ==========================================
# 3. MENU DE NAVIGATION
# ==========================================
try:
    st.sidebar.image("assets/logo.png", width=150)
except:
    st.sidebar.markdown("### 🚗 LNS GARAGE PRO")

st.sidebar.markdown("---")

menu_items = {
    "📊 Tableau de bord": "dashboard", "👤 Clients": "clients", "🚘 Véhicules": "vehicules",
    "📥 Réception Véhicule": "reception", "🛡️ Sinistres Assurance": "sinistres",
    "📝 Devis": "devis", "🔧 Ordres de Réparation": "ordres", "🏭 Suivi Atelier": "atelier",
    "📦 Stock": "stock", "🔩 Accessoires": "accessoires", "🏭 Fournisseurs": "fournisseurs",
    "🛒 Achats": "achats", "🧾 Facturation": "facturation", "💰 Caisse": "caisse",
    "📸 Galerie Photos": "photos", "👷 Employés": "employes", "📂 Documents": "documents",
    "📈 Statistiques": "statistiques", "📱 QR Code": "qrcode", "🔐 Multi-Utilisateurs": "users"
}

choice = st.sidebar.radio("Navigation", list(menu_items.keys()))
module_name = menu_items[choice]

# ==========================================
# 4. DÉFINITION DES MODULES
# ==========================================

def show_dashboard():
    st.title("📊 Tableau de Bord")
    st.markdown("### Vue d'ensemble de l'activité")
    
    nb_clients = len(get_all_records('clients'))
    nb_vehicules = len(get_all_records('vehicules'))
    nb_devis_attente = len([d for d in get_all_records('devis') if d.get('statut') == 'En attente'])
    nb_factures_impayees = len([f for f in get_all_records('factures') if f.get('statut_paiement') == 'Impayée'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(f"<div class='kpi-card'><h3>Clients</h3><h1>{nb_clients}</h1></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='kpi-card'><h3>Véhicules</h3><h1>{nb_vehicules}</h1></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='kpi-card'><h3>Devis en attente</h3><h1>{nb_devis_attente}</h1></div>", unsafe_allow_html=True)
    with col4: st.markdown(f"<div class='kpi-card'><h3>Factures impayées</h3><h1>{nb_factures_impayees}</h1></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Analyse visuelle")
    col_graph1, col_graph2 = st.columns(2)
    
    with col_graph1:
        df_marques = get_df('vehicules')
        if not df_marques.empty:
            mar = df_marques.groupby('marque').size().reset_index(name='count')
            fig = px.pie(mar, values='count', names='marque', title="Véhicules par Marque", hole=0.5, color_discrete_sequence=COLOR_PALETTE)
            fig.update_layout(margin=dict(t=50, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Aucun véhicule enregistré.")

    with col_graph2:
        df_caisse = get_df('paiements')
        if not df_caisse.empty:
            ca = df_caisse.groupby('categorie')['montant'].sum().reset_index()
            fig = px.bar(ca, x='categorie', y='montant', title="Flux Caisse par Catégorie", color='categorie', color_discrete_sequence=COLOR_PALETTE)
            fig.update_layout(margin=dict(t=50, b=0, l=0, r=0), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Aucune transaction en caisse.")

def show_clients():
    st.title("👤 Gestion des Clients")
    tab1, tab2, tab3 = st.tabs(["📋 Liste", "➕ Ajouter", "🔍 Détails / Modifier"])
    
    with tab1:
        df = get_df('clients')
        if not df.empty: st.dataframe(df[['id', 'nom', 'prenom', 'telephone', 'email', 'ville']], use_container_width=True, hide_index=True)
        else: st.info("Aucun client enregistré.")

    with tab2:
        with st.form("ajout_client"):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nom *"); prenom = st.text_input("Prénom *"); telephone = st.text_input("Téléphone *")
            with col2:
                telephone2 = st.text_input("Téléphone secondaire"); email = st.text_input("Email"); ville = st.text_input("Ville")
            adresse = st.text_area("Adresse")
            if st.form_submit_button("Enregistrer le client"):
                if nom and prenom and telephone:
                    create_record('clients', {"nom": nom, "prenom": prenom, "telephone": telephone, "telephone2": telephone2, "email": email, "adresse": adresse, "ville": ville, "date_creation": str(date.today())})
                    st.success(f"Client {nom} {prenom} ajouté avec succès !")
                else: st.error("Les champs Nom, Prénom et Téléphone sont obligatoires.")

    with tab3:
        df_clients = get_df('clients')
        if not df_clients.empty:
            client_dict = df_clients.apply(lambda row: f"{row['nom']} {row['prenom']} (ID: {row['id']})", axis=1).tolist()
            client_choice = st.selectbox("Choisir un client", client_dict)
            client_id = int(client_choice.split("ID: ")[1].replace(")", ""))
            client_data = get_record('clients', client_id)
            
            with st.expander("Modifier ou Supprimer ce client"):
                with st.form("modif_client"):
                    m_nom = st.text_input("Nom", value=client_data['nom'])
                    m_prenom = st.text_input("Prénom", value=client_data['prenom'])
                    m_tel = st.text_input("Téléphone", value=client_data['telephone'])
                    if st.form_submit_button("Sauvegarder modifications"):
                        update_record('clients', client_id, {"nom": m_nom, "prenom": m_prenom, "telephone": m_tel})
                        st.success("Client modifié !"); st.rerun()
                if st.button("🗑️ Supprimer ce client", type="secondary"):
                    delete_record('clients', client_id)
                    st.warning("Client supprimé !"); st.rerun()
        else: st.info("Veuillez ajouter des clients d'abord.")

def show_vehicules():
    st.title("🚘 Gestion des Véhicules")
    tab1, tab2 = st.tabs(["📋 Liste", "➕ Ajouter"])
    
    with tab1:
        df_v = get_df('vehicules'); df_c = get_df('clients')
        if not df_v.empty and not df_c.empty:
            df = pd.merge(df_v, df_c, left_on='client_id', right_on='id', suffixes=('_v', '_c'))
            df['Propriétaire'] = df['nom_c'] + ' ' + df['prenom_c']
            st.dataframe(df[['immatriculation', 'marque', 'modele', 'annee', 'couleur', 'Propriétaire']], use_container_width=True, hide_index=True)
        else: st.info("Aucun véhicule enregistré.")

    with tab2:
        df_clients = get_df('clients')
        if df_clients.empty: st.error("Vous devez ajouter un client avant d'ajouter un véhicule !")
        else:
            client_dict = df_clients.apply(lambda row: f"{row['nom']} {row['prenom']} (ID: {row['id']})", axis=1).tolist()
            client_choice = st.selectbox("Propriétaire du véhicule", client_dict)
            client_id = int(client_choice.split("ID: ")[1].replace(")", ""))
            
            with st.form("ajout_vehicule"):
                col1, col2 = st.columns(2)
                with col1:
                    immat = st.text_input("Immatriculation *"); vin = st.text_input("VIN"); marque = st.text_input("Marque *"); modele = st.text_input("Modèle *")
                with col2:
                    annee = st.number_input("Année", min_value=1900, max_value=2025, value=2020); couleur = st.text_input("Couleur")
                    kilometrage = st.number_input("Kilométrage", min_value=0); carburant = st.selectbox("Carburant", ["Diesel", "Essence", "Hybride", "Electrique", "GPL"])
                if st.form_submit_button("Enregistrer le véhicule"):
                    if immat and marque and modele:
                        create_record('vehicules', {"client_id": client_id, "immatriculation": immat, "vin": vin, "marque": marque, "modele": modele, "annee": int(annee), "couleur": couleur, "kilometrage": int(kilometrage), "carburant": carburant})
                        st.success(f"Véhicule {immat} ajouté avec succès !")
                    else: st.error("Immatriculation, Marque et Modèle sont obligatoires.")

def show_reception():
    st.title("📥 Réception Véhicule")
    tab1, tab2, tab3 = st.tabs(["📋 Liste", "➕ Nouvelle Réception", "🔍 Détails / Modifier"])
    
    with tab1:
        df_r = get_df('reception'); df_v = get_df('vehicules'); df_c = get_df('clients')
        if not df_r.empty and not df_v.empty and not df_c.empty:
            df = pd.merge(df_r, df_v, left_on='vehicule_id', right_on='id', suffixes=('_r', '_v'))
            df = pd.merge(df, df_c, left_on='client_id_v', right_on='id', suffixes=('', '_c'))
            df['Client'] = df['nom_c'] + ' ' + df['prenom_c']
            st.dataframe(df[['date_entree', 'immatriculation', 'marque', 'Client', 'observations']], use_container_width=True, hide_index=True)
        else: st.info("Aucune réception enregistrée.")

    with tab2:
        df_v = get_df('vehicules'); df_c = get_df('clients')
        if df_v.empty or df_c.empty: st.error("⚠️ Vous devez ajouter un client et un véhicule avant de faire une réception !")
        else:
            df_veh = pd.merge(df_v, df_c, left_on='client_id', right_on='id', suffixes=('_v', '_c'))
            df_veh['display'] = df_veh.apply(lambda r: f"{r['immatriculation']} - {r['marque']} {r['modele']} ({r['nom_c']}) [ID:{r['id_v']}]", axis=1)
            veh_choice = st.selectbox("Véhicule reçu", df_veh['display'].tolist())
            veh_id = int(veh_choice.split("[ID:")[1].replace("]", ""))
            
            with st.form("new_reception"):
                col1, col2 = st.columns(2)
                with col1: date_entree = st.date_input("Date d'entrée *"); kilometrage = st.number_input("Kilométrage à l'entrée", min_value=0, step=1)
                with col2: niveau_carburant = st.selectbox("Niveau carburant", ["Plein", "3/4", "1/2", "1/4", "Vide", "Inconnu"])
                observations = st.text_area("Observations / Description du problème")
                
                col3, col4, col5 = st.columns(3)
                with col3: roue_secours = st.checkbox("Roue de secours"); cric = st.checkbox("Cric")
                with col4: radio = st.checkbox("Radio / Autoradio"); documents = st.checkbox("Documents (CG, Assurance)")
                with col5: clees = st.checkbox("Clés (doublon)")
                
                signature_check = st.checkbox("Le client confirme la remise du véhicule et la véracité de la checklist")
                signature_nom = st.text_input("Nom et Prénom du signataire (si checkbox coché)")
                
                if st.form_submit_button("📥 Enregistrer la Réception"):
                    if date_entree and signature_check and signature_nom:
                        create_record('reception', {"vehicule_id": veh_id, "date_entree": str(date_entree), "kilometrage": int(kilometrage), "niveau_carburant": niveau_carburant, "observations": observations, "roue_secours": int(roue_secours), "cric": int(cric), "radio": int(radio), "documents": int(documents), "clees": int(clees), "signature_client": signature_nom})
                        st.success("✅ Fiche de réception enregistrée avec succès !")
                    else: st.error("❌ La date, la confirmation de signature et le nom du signataire sont obligatoires.")

    with tab3:
        df_r = get_df('reception'); df_v = get_df('vehicules'); df_c = get_df('clients')
        if not df_r.empty and not df_v.empty and not df_c.empty:
            df = pd.merge(df_r, df_v, left_on='vehicule_id', right_on='id', suffixes=('_r', '_v'))
            df = pd.merge(df, df_c, left_on='client_id_v', right_on='id', suffixes=('', '_c'))
            df['Client'] = df['nom_c'] + ' ' + df['prenom_c']
            df['display'] = df.apply(lambda r: f"{r['date_entree']} - {r['immatriculation']} ({r['Client']}) [ID:{r['id_r']}]", axis=1)
            recep_choice = st.selectbox("Choisir une fiche de réception", df['display'].tolist())
            recep_id = int(recep_choice.split("[ID:")[1].replace("]", ""))
            detail = get_record('reception', recep_id)
            
            st.write(f"**Véhicule ID:** {detail['vehicule_id']} | **Date entrée:** {detail['date_entree']}")
            st.write(f"**Kilométrage:** {detail['kilometrage']} km | **Carburant:** {detail['niveau_carburant']}")
            st.write(f"**Observations:** {detail['observations']}")
            st.markdown("---")
            checklist_items = {"Roue de secours": detail['roue_secours'], "Cric": detail['cric'], "Radio": detail['radio'], "Documents": detail['documents'], "Clés": detail['clees']}
            for item, val in checklist_items.items():
                st.write(f"{'✅' if val else '❌'} {item}")
            st.write(f"**Signataire :** {detail['signature_client']}")
            
            with st.expander("🔧 Modifier ou Supprimer cette fiche"):
                with st.form("modif_reception"):
                    m_obs = st.text_area("Observations", value=detail['observations'])
                    m_km = st.number_input("Kilométrage", value=int(detail['kilometrage']))
                    m_roue = st.checkbox("Roue de secours", value=bool(detail['roue_secours']))
                    m_cric = st.checkbox("Cric", value=bool(detail['cric']))
                    m_radio = st.checkbox("Radio", value=bool(detail['radio']))
                    m_docs = st.checkbox("Documents", value=bool(detail['documents']))
                    m_clees = st.checkbox("Clés", value=bool(detail['clees']))
                    if st.form_submit_button("Sauvegarder modifications"):
                        update_record('reception', recep_id, {"observations": m_obs, "kilometrage": int(m_km), "roue_secours": int(m_roue), "cric": int(m_cric), "radio": int(m_radio), "documents": int(m_docs), "clees": int(m_clees)})
                        st.success("Fiche modifiée !"); st.rerun()
                if st.button("🗑️ Supprimer cette fiche", type="secondary"):
                    delete_record('reception', recep_id)
                    st.warning("Fiche supprimée !"); st.rerun()
        else: st.info("Aucune réception à modifier.")

def show_sinistres():
    st.title("🛡️ Sinistres & Assurances")
    tab1, tab2, tab3 = st.tabs(["📋 Liste", "➕ Nouveau Sinistre", "🔍 Détails / Modifier"])
    
    with tab1:
        df_s = get_df('assurances'); df_v = get_df('vehicules'); df_c = get_df('clients')
        if not df_s.empty and not df_v.empty and not df_c.empty:
            df = pd.merge(df_s, df_v, left_on='vehicule_id', right_on='id', suffixes=('_s', '_v'))
            df = pd.merge(df, df_c, left_on='client_id_v', right_on='id', suffixes=('', '_c'))
            df['Client'] = df['nom_c'] + ' ' + df['prenom_c']
            st.dataframe(df[['numero_dossier', 'compagnie', 'immatriculation', 'Client', 'date_expertise', 'montant_valide']], use_container_width=True, hide_index=True)
        else: st.info("Aucun sinistre d'assurance enregistré.")

    with tab2:
        df_v = get_df('vehicules'); df_c = get_df('clients')
        if df_v.empty or df_c.empty: st.error("⚠️ Vous devez ajouter un client et un véhicule avant de créer un sinistre !")
        else:
            df_veh = pd.merge(df_v, df_c, left_on='client_id', right_on='id', suffixes=('_v', '_c'))
            df_veh['Client'] = df_veh['nom_c'] + ' ' + df_veh['prenom_c']
            df_veh['display'] = df_veh.apply(lambda r: f"{r['immatriculation']} - {r['Client']} [VehID:{r['id_v']}]", axis=1)
            
            with st.form("new_sinistre"):
                veh_choice = st.selectbox("Véhicule concerné *", df_veh['display'].tolist())
                veh_id = int(veh_choice.split("[VehID:")[1].replace("]", ""))
                col1, col2 = st.columns(2)
                with col1: compagnie = st.text_input("Compagnie d'assurance *"); numero_dossier = st.text_input("N° Dossier *"); expert = st.text_input("Nom de l'Expert")
                with col2: date_expertise = st.date_input("Date de l'expertise *"); montant_valide = st.number_input("Montant validé (€)", min_value=0.0, format="%.2f")
                commentaires = st.text_area("Commentaires")
                if st.form_submit_button("🛡️ Créer le Sinistre"):
                    if compagnie and numero_dossier and date_expertise:
                        create_record('assurances', {"vehicule_id": veh_id, "compagnie": compagnie, "numero_dossier": numero_dossier, "expert": expert, "date_expertise": str(date_expertise), "montant_valide": float(montant_valide), "commentaires": commentaires})
                        st.success(f"✅ Dossier sinistre {numero_dossier} créé avec succès !")
                    else: st.error("❌ La Compagnie, le N° Dossier et la Date sont obligatoires.")

    with tab3:
        df_s = get_df('assurances'); df_v = get_df('vehicules')
        if not df_s.empty and not df_v.empty:
            df = pd.merge(df_s, df_v, left_on='vehicule_id', right_on='id', suffixes=('_s', '_v'))
            df['display'] = df.apply(lambda r: f"{r['numero_dossier']} - {r['compagnie']} ({r['immatriculation']}) [SinID:{r['id_s']}]", axis=1)
            sin_choice = st.selectbox("Choisir un sinistre", df['display'].tolist())
            sin_id = int(sin_choice.split("[SinID:")[1].replace("]", ""))
            detail = get_record('assurances', sin_id)
            
            with st.form("modif_sinistre"):
                col1, col2 = st.columns(2)
                with col1: m_compagnie = st.text_input("Compagnie *", value=detail['compagnie']); m_dossier = st.text_input("N° Dossier *", value=detail['numero_dossier']); m_expert = st.text_input("Expert", value=detail.get('expert', ''))
                with col2: m_date = st.date_input("Date expertise", value=pd.to_datetime(detail['date_expertise'])); m_montant = st.number_input("Montant validé (€)", min_value=0.0, format="%.2f", value=float(detail.get('montant_valide', 0.0)))
                m_comments = st.text_area("Commentaires", value=detail.get('commentaires', ''))
                if st.form_submit_button("💾 Sauvegarder"):
                    update_record('assurances', sin_id, {"compagnie": m_compagnie, "numero_dossier": m_dossier, "expert": m_expert, "date_expertise": str(m_date), "montant_valide": float(m_montant), "commentaires": m_comments})
                    st.success("✅ Sinistre mis à jour !"); st.rerun()
            if st.button(f"🗑️ Supprimer le sinistre {detail['numero_dossier']}", type="secondary"):
                delete_record('assurances', sin_id)
                st.success("Sinistre supprimé !"); st.rerun()
        else: st.info("Aucun sinistre à modifier.")

def generate_devis_pdf(devis_info, client_info, vehicule_info, details):
    if not os.path.exists("pdf"): os.makedirs("pdf")
    pdf_path = f"pdf/Devis_{devis_info['numero_devis']}.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph("LNS GARAGE PRO - DEVIS", styles['Title']))
    elements.append(Spacer(1, 15))
    info_data = [
        [f"Client: {client_info['nom']} {client_info['prenom']}", f"Date: {devis_info['date_creation']}"],
        [f"Véhicule: {vehicule_info['marque']} {vehicule_info['modele']}", f"Immat: {vehicule_info['immatriculation']}"]
    ]
    info_table = Table(info_data, colWidths=[120*mm, 60*mm])
    info_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    table_data = [["Type", "Description", "Quantité", "Prix Unitaire", "Total"]]
    for item in details.get('mo', []):
        if item['qty'] > 0: table_data.append(["MO", item['desc'], f"{item['qty']} H", f"{item['price']:.2f} dzd", f"{item['total']:.2f} dzd"])
    for item in details.get('pieces', []):
        if item['qty'] > 0: table_data.append(["Pièce", f"{item.get('ref', '')} - {item['desc']}", f"{item['qty']}", f"{item['price']:.2f} dzd", f"{item['total']:.2f} dzd"])
        
    items_table = Table(table_data, colWidths=[20*mm, 70*mm, 25*mm, 30*mm, 30*mm])
    items_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
    elements.append(items_table)
    elements.append(Spacer(1, 20))
    
    ht = devis_info['total_mo'] + devis_info['total_pieces']
    totals_data = [
        ["Total Hors Taxe (HT)", f"{ht:.2f} dzd"],
        ["TVA (20%)", f"{devis_info['tva']:.2f} dzd"],
        ["Total TTC (À payer)", f"{devis_info['total_ttc']:.2f} dzd"]
    ]
    totals_table = Table(totals_data, colWidths=[120*mm, 50*mm])
    totals_table.setStyle(TableStyle([('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(totals_table)
    doc.build(elements)
    return pdf_path

with tab2:
    df_v = get_df('vehicules')
    df_c = get_df('clients')

    if df_v.empty or df_c.empty:
        st.error("⚠️ Vous devez ajouter un client et un véhicule avant de créer un devis !")

    else:

        # Fusion véhicules + clients
        df_veh = pd.merge(
            df_v,
            df_c,
            left_on='client_id',
            right_on='id',
            suffixes=('_v', '_c')
        )

        # Création du nom complet client
        if 'prenom' in df_veh.columns:
            df_veh['client_nom'] = (
                df_veh['nom'].fillna('') +
                ' ' +
                df_veh['prenom'].fillna('')
            )
        else:
            df_veh['client_nom'] = df_veh['nom'].fillna('')

        # Création du texte affiché
        df_veh['display'] = df_veh.apply(
            lambda r:
            f"{r['immatriculation']} - "
            f"{r['marque']} {r['modele']} "
            f"({r['client_nom']}) "
            f"[ID:{r['id_v']}]",
            axis=1
        )

        veh_choice = st.selectbox(
            "Véhicule concerné",
            df_veh['display'].tolist()
        )

        veh_id = int(
            veh_choice.split("[ID:")[1]
            .replace("]", "")
        )

        with st.form("new_devis"):

            col_date, col_num, col_statut = st.columns(3)

            with col_date:
                date_creation = st.date_input("Date du devis *")

            with col_num:
                numero_devis = st.text_input(
                    "N° Devis",
                    value=get_next_numero('devis')
                )

            with col_statut:
                statut = st.selectbox(
                    "Statut",
                    ["En attente", "Validé", "Refusé"]
                )

            st.markdown("---")
            st.subheader("🔧 Main d'œuvre")

            mo_details_list = []

            for task in [
                "Débosselage",
                "Redressage",
                "Soudure",
                "Préparation",
                "Peinture",
                "Polissage"
            ]:

                col1, col2, col3 = st.columns(3)

                with col1:
                    h = st.number_input(
                        f"{task} (Heures)",
                        min_value=0.0,
                        step=0.5,
                        key=f"mo_h_{task}"
                    )

                with col2:
                    p = st.number_input(
                        f"Prix / H",
                        min_value=0.0,
                        value=45.0,
                        format="%.2f",
                        key=f"mo_p_{task}"
                    )

                with col3:
                    st.write(
                        f"Total: **{h * p:.2f} DZD**"
                    )

                mo_details_list.append({
                    "desc": task,
                    "qty": h,
                    "price": p,
                    "total": h * p
                })

            st.markdown("---")
            st.subheader("🔩 Pièces et Fournitures")

            pieces_details_list = []

            for i in range(5):

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    ref = st.text_input(
                        f"Réf. Pièce {i+1}",
                        key=f"p_ref_{i}"
                    )

                with col2:
                    des = st.text_input(
                        f"Désignation Pièce {i+1}",
                        key=f"p_des_{i}"
                    )

                with col3:
                    qty = st.number_input(
                        f"Qté Pièce {i+1}",
                        min_value=0,
                        step=1,
                        key=f"p_qty_{i}"
                    )

                with col4:
                    px = st.number_input(
                        f"Prix Pièce {i+1}",
                        min_value=0.0,
                        format="%.2f",
                        key=f"p_px_{i}"
                    )

                if qty > 0 and des:
                    pieces_details_list.append({
                        "ref": ref,
                        "desc": des,
                        "qty": int(qty),
                        "price": px,
                        "total": qty * px
                    })

            if st.form_submit_button(
                "📊 Calculer et Sauvegarder le Devis"
            ):

                total_mo = sum(
                    item['total']
                    for item in mo_details_list
                )

                total_pieces = sum(
                    item['total']
                    for item in pieces_details_list
                )

                total_ht = total_mo + total_pieces
                tva = total_ht * 0.20
                total_ttc = total_ht + tva

                create_record(
                    'devis',
                    {
                        "vehicule_id": veh_id,
                        "numero_devis": numero_devis,
                        "date_creation": str(date_creation),
                        "statut": statut,
                        "total_pieces": total_pieces,
                        "total_mo": total_mo,
                        "tva": tva,
                        "total_ttc": total_ttc,
                        "details": {
                            "mo": mo_details_list,
                            "pieces": pieces_details_list
                        }
                    }
                )

                st.success(
                    f"✅ Devis {numero_devis} sauvegardé ! "
                    f"Total TTC : {total_ttc:.2f} DZD"
                )

def show_ordres():
    st.title("🔧 Ordres de Réparation (OR)")
    tab1, tab2, tab3 = st.tabs(["📋 Liste", "➕ Créer", "🔍 Suivi / Modifier"])
    
    with tab1:
        df_o = get_df('reparations'); df_v = get_df('vehicules'); df_c = get_df('clients')
        if not df_o.empty and not df_v.empty and not df_c.empty:
            df = pd.merge(df_o, df_v, left_on='vehicule_id', right_on='id', suffixes=('_o', '_v'))
            df = pd.merge(df, df_c, left_on='client_id_v', right_on='id', suffixes=('', '_c'))
            df['Client'] = df['nom_c'] + ' ' + df['prenom_c']
            def statut_icon(val): return "⏳ En attente" if val=="En attente" else "🔄 En cours" if val=="En cours" else "⏸️ Suspendu" if val=="Suspendu" else "✅ Terminé" if val=="Terminé" else val
            df['statut'] = df['statut'].apply(statut_icon)
            st.dataframe(df[['numero_or', 'immatriculation', 'Client', 'responsable', 'statut', 'date_debut', 'date_fin']], use_container_width=True, hide_index=True)
        else: st.info("Aucun ordre de réparation créé pour le moment.")

    with tab2:
        df_v = get_df('vehicules'); df_c = get_df('clients'); df_d = get_df('devis')
        if df_v.empty or df_c.empty: st.error("⚠️ Vous devez ajouter un client et un véhicule avant de créer un OR !")
        else:
           df_veh = pd.merge(
    df_v,
    df_c,
    left_on='client_id',
    right_on='id',
    suffixes=('_v', '_c')
)

# Construction du nom complet client
if 'prenom' in df_veh.columns:
    df_veh['client_nom'] = (
        df_veh['nom'].fillna('') +
        ' ' +
        df_veh['prenom'].fillna('')
    )
else:
    df_veh['client_nom'] = df_veh['nom'].fillna('')

df_veh['display'] = df_veh.apply(
    lambda r:
        f"{r['immatriculation']} - "
        f"{r['marque']} {r['modele']} "
        f"({r['client_nom']}) "
        f"[ID:{r['id_v']}]",
    axis=1
)
            df_devis_filtered = df_d[df_d['vehicule_id'] == veh_id]
            devis_options = ["Aucun devis (Travaux internes)"]
            if not df_devis_filtered.empty:
                devis_dict_filtered = df_devis_filtered.apply(lambda r: f"{r['numero_devis']} - {r['statut']} ({r['total_ttc']}dzd) [DevisID:{r['id']}]", axis=1).tolist()
                devis_options.extend(devis_dict_filtered)
            devis_choice = st.selectbox("Associer à un Devis ?", devis_options)
            devis_id = None if devis_choice == "Aucun devis (Travaux internes)" else int(devis_choice.split("[DevisID:")[1].replace("]", ""))
            
            with st.form("new_or"):
                last_id_or = max([o['id'] for o in get_all_records('reparations')], default=0)
                col1, col2, col3 = st.columns(3)
                with col1: numero_or = st.text_input("N° Ordre de Réparation *", value=f"OR-{last_id_or+1:04d}"); responsable = st.text_input("Responsable *")
                with col2: date_debut = st.date_input("Date de début *")
                with col3: date_fin = st.date_input("Date de fin *")
                statut = st.selectbox("Statut initial", ["En attente", "En cours", "Suspendu", "Terminé"])
                if st.form_submit_button("🛠️ Créer l'Ordre de Réparation"):
                    if numero_or and responsable and date_debut and date_fin:
                        if str(date_fin) < str(date_debut): st.error("❌ La date de fin prévue doit être après la date de début !")
                        else:
                            create_record('reparations', {"devis_id": devis_id, "vehicule_id": veh_id, "numero_or": numero_or, "responsable": responsable, "date_debut": str(date_debut), "date_fin": str(date_fin), "statut": statut})
                            st.success(f"✅ Ordre de Réparation {numero_or} créé avec succès !")
                    else: st.error("❌ Le numéro, le responsable et les dates sont obligatoires.")

    with tab3:
        df_o = get_df('reparations'); df_v = get_df('vehicules'); df_c = get_df('clients')
        if not df_o.empty and not df_v.empty and not df_c.empty:
            df = pd.merge(df_o, df_v, left_on='vehicule_id', right_on='id', suffixes=('_o', '_v'))
            df = pd.merge(df, df_c, left_on='client_id_v', right_on='id', suffixes=('', '_c'))
            df['Client'] = (
    df['nom'].fillna('') +
    ' ' +
    df['prenom'].fillna('')
)
            df['display'] = df.apply(lambda r: f"{r['numero_or']} - {r['Client']} ({r['immatriculation']}) Statut: {r['statut']} [ORID:{r['id_o']}]", axis=1)
            or_choice = st.selectbox("Choisir un Ordre de Réparation", df['display'].tolist())
            or_id = int(or_choice.split("[ORID:")[1].replace("]", ""))
            detail = get_record('reparations', or_id)
            
            st.write(f"### Ordre N° {detail['numero_or']}")
            st.write(f"**Responsable :** {detail['responsable']} | **Période :** {detail['date_debut']} au {detail['date_fin']}")
            
            with st.form("update_or"):
                new_statut = st.selectbox("Statut des travaux", ["En attente", "En cours", "Suspendu", "Terminé"], index=["En attente", "En cours", "Suspendu", "Terminé"].index(detail['statut']))
                col1, col2 = st.columns(2)
                with col1: new_debut = st.date_input("Nouvelle date de début", value=pd.to_datetime(detail['date_debut']))
                with col2: new_fin = st.date_input("Nouvelle date de fin prévue", value=pd.to_datetime(detail['date_fin']))
                new_resp = st.text_input("Responsable", value=detail['responsable'])
                if st.form_submit_button("Sauvegarder les modifications"):
                    update_record('reparations', or_id, {"statut": new_statut, "date_debut": str(new_debut), "date_fin": str(new_fin), "responsable": new_resp})
                    st.success("Ordre de réparation mis à jour !"); st.rerun()
            if st.button("🗑️ Supprimer cet Ordre", type="secondary"):
                delete_record('reparations', or_id)
                st.warning("Ordre supprimé !"); st.rerun()
        else: st.info("Aucun ordre de réparation à suivre.")

def show_atelier():
    st.title("🏭 Suivi Atelier - Progression des Travaux")
    etapes_atelier = ["Réception", "Diagnostic", "Tôlerie", "Préparation", "Peinture", "Remontage", "Contrôle Qualité", "Livraison"]
    tab1, tab2 = st.tabs(["🚜 Tableau de l'Atelier", "📊 Progression Détaillée"])
    
    with tab1:
        df_o = get_df('reparations'); df_v = get_df('vehicules'); df_c = get_df('clients')
        if not df_o.empty and not df_v.empty and not df_c.empty:
            df = pd.merge(df_o, df_v, left_on='vehicule_id', right_on='id', suffixes=('_o', '_v'))
            df = pd.merge(df, df_c, left_on='client_id_v', right_on='id', suffixes=('', '_c'))
            df['Client'] = df['nom_c'] + ' ' + df['prenom_c']
            st.dataframe(df[df['statut'] != 'Terminé'][['numero_or', 'immatriculation', 'marque', 'modele', 'Client', 'statut', 'responsable']], use_container_width=True, hide_index=True)
        else: st.info("🎉 Aucun véhicule en cours de réparation dans l'atelier !")
    
    with tab2:
        df_o = get_df('reparations'); df_v = get_df('vehicules'); df_c = get_df('clients')
        if not df_o.empty and not df_v.empty and not df_c.empty:
            df = pd.merge(df_o, df_v, left_on='vehicule_id', right_on='id', suffixes=('_o', '_v'))
            df = pd.merge(df, df_c, left_on='client_id_v', right_on='id', suffixes=('', '_c'))
            df['Client'] = df['nom_c'] + ' ' + df['prenom_c']
            df = df[df['statut'] != 'Terminé']
            if df.empty: st.info("Aucun véhicule à suivre.")
            else:
                df['display'] = df.apply(lambda r: f"{r['numero_or']} - {r['immatriculation']} ({r['Client']}) [ORID:{r['id_o']}]", axis=1)
                or_choice = st.selectbox("Choisir un Ordre de Réparation à suivre", df['display'].tolist())
                or_id = int(or_choice.split("[ORID:")[1].replace("]", ""))
                
                df_suivi = pd.DataFrame([s for s in get_all_records('suivi_atelier') if s['or_id'] == or_id])
                if df_suivi.empty:
                    create_record('suivi_atelier', {"or_id": or_id, "etape_actuelle": etapes_atelier[0], "progression": 12})
                    df_suivi = pd.DataFrame([s for s in get_all_records('suivi_atelier') if s['or_id'] == or_id])
                
                suivi_data = df_suivi.iloc[0]
                current_etape = suivi_data['etape_actuelle']
                current_progress = int(suivi_data['progression'])
                current_etape_index = etapes_atelier.index(current_etape) if current_etape in etapes_atelier else 0
                
                st.markdown("---")
                cols = st.columns(len(etapes_atelier))
                for i, etape in enumerate(etapes_atelier):
                    with cols[i]:
                        if i < current_etape_index: st.markdown(f"<div style='text-align: center; background-color: #d4edda; padding: 10px; border-radius: 5px; color: black;'><b>✅</b><br>{etape}</div>", unsafe_allow_html=True)
                        elif i == current_etape_index: st.markdown(f"<div style='text-align: center; background-color: #cce5ff; padding: 10px; border-radius: 5px; color: black; border: 2px solid #1E3A8A;'><b>🔧</b><br><b>{etape}</b></div>", unsafe_allow_html=True)
                        else: st.markdown(f"<div style='text-align: center; background-color: #f8f9fa; padding: 10px; border-radius: 5px; color: grey;'><b>⬜</b><br>{etape}</div>", unsafe_allow_html=True)
                st.markdown("---")
                
                st.progress(current_progress / 100, text=f"Progression globale : {current_progress}%")
                with st.form("update_etape"):
                    new_etape = st.selectbox("Définir l'étape actuelle :", etapes_atelier, index=current_etape_index)
                    if st.form_submit_button("Mettre à jour la progression"):
                        new_etape_index = etapes_atelier.index(new_etape)
                        new_progress = int((new_etape_index + 1) * (100 / len(etapes_atelier)))
                        update_record('suivi_atelier', suivi_data['id'], {"etape_actuelle": new_etape, "progression": new_progress})
                        if new_etape == "Livraison":
                            update_record('reparations', or_id, {"statut": "Terminé"})
                            st.balloons()
                            st.success("🎉 Véhicule livré ! L'Ordre de Réparation est maintenant marqué comme TERMINÉ.")
                        else: st.success(f"✅ Progression mise à jour : Étape **{new_etape}** ({new_progress}%)")
                        st.rerun()
        else: st.info("Aucun véhicule à suivre.")

def show_qr_dashboard(veh_id):
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚗 LNS GARAGE PRO - Suivi Véhicule</h1>", unsafe_allow_html=True)
    veh_info = get_record('vehicules', veh_id)
    if not veh_info: st.error("Véhicule introuvable."); return
    client_info = get_record('clients', veh_info['client_id'])
    st.markdown(f"<h3 style='text-align: center;'>{client_info['nom']} - {veh_info['marque']} {veh_info['modele']} ({veh_info['immatriculation']})</h3>", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("🏭 Statut des Travaux")
    ordres = [o for o in get_all_records('reparations') if o['vehicule_id'] == veh_id and o['statut'] != 'Terminé']
    if ordres:
        o = ordres[-1]
        suivi = next((s for s in get_all_records('suivi_atelier') if s['or_id'] == o['id']), None)
        if suivi: st.progress(int(suivi['progression']) / 100, text=f"Étape : {suivi['etape_actuelle']} ({o['statut']})")
    else: st.success("✅ Réparation Terminée ou Non commencée")

def show_qrcode():
    st.title("📱 Génération de QR Code Client")
    st.info("Génère un QR Code unique pour chaque véhicule.")
    app_base_url = st.text_input("URL de base de l'application", "http://localhost:8501")
    df_vehicules = get_df('vehicules'); df_clients = get_df('clients')
    if not df_vehicules.empty and not df_clients.empty:
        df_veh = pd.merge(df_vehicules, df_clients, left_on='client_id', right_on='id', suffixes=('_v', '_c'))
        df_veh['display'] = df_veh.apply(lambda r: f"{r['immatriculation']} - {r['marque']} ({r['nom_c']}) [VehID:{r['id_v']}]", axis=1)
        veh_choice = st.selectbox("Choisir le véhicule", df_veh['display'].tolist())
        veh_id = int(veh_choice.split("[VehID:")[1].replace("]", ""))
        qr_url = f"{app_base_url}?veh_id={veh_id}"
        st.code(qr_url)
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(qr_url); qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO(); img.save(buf, format="PNG"); byte_im = buf.getvalue()
        st.image(byte_im, caption="QR Code généré")
        st.download_button(label="⬇️ Télécharger QR Code", data=byte_im, file_name=f"QRCode_Veh_{veh_id}.png", mime="image/png")

def show_users():
    st.title("🔐 Gestion des Utilisateurs")
    tab1, tab2, tab3 = st.tabs(["📋 Liste", "➕ Ajouter", "🔍 Modifier / Supprimer"])
    
    with tab1:
        df = get_df('utilisateurs')
        if not df.empty: st.dataframe(df[['id', 'nom', 'username', 'role']], use_container_width=True, hide_index=True)
        else: st.info("Aucun utilisateur.")

    with tab2:
        with st.form("add_user"):
            col1, col2 = st.columns(2)
            with col1: nom = st.text_input("Nom complet *"); username = st.text_input("Pseudo (Login) *")
            with col2: mot_de_passe = st.text_input("Mot de passe *", type="password"); role = st.selectbox("Rôle *", ["Administrateur", "Réceptionniste", "Chef atelier", "Tôlier", "Peintre", "Comptable"])
            if st.form_submit_button("✅ Créer le compte"):
                if nom and username and mot_de_passe:
                    users = get_all_records('utilisateurs')
                    if any(u['username'] == username for u in users): st.error("❌ Ce Pseudo existe déjà.")
                    else:
                        hashed_pw = hashlib.sha256(mot_de_passe.encode()).hexdigest()
                        create_record('utilisateurs', {"nom": nom, "username": username, "password_hash": hashed_pw, "role": role})
                        st.success(f"✅ Compte '{username}' créé !")
                else: st.error("❌ Tous les champs sont obligatoires.")

    with tab3:
        df_users = get_df('utilisateurs')
        if not df_users.empty:
            user_dict = df_users.apply(lambda r: f"{r['nom']} ({r['username']}) [ID:{r['id']}]", axis=1).tolist()
            user_choice = st.selectbox("Choisir un utilisateur", user_dict)
            user_id = int(user_choice.split("[ID:")[1].replace("]", ""))
            detail = get_record('utilisateurs', user_id)
            with st.form("modif_user"):
                m_nom = st.text_input("Nom", value=detail['nom']); m_pseudo = st.text_input("Pseudo", value=detail['username'])
                m_mdp = st.text_input("Nouveau Mot de passe (laisser vide si inchangé)", type="password")
                m_role = st.selectbox("Rôle", ["Administrateur", "Réceptionniste", "Chef atelier", "Tôlier", "Peintre", "Comptable"], index=["Administrateur", "Réceptionniste", "Chef atelier", "Tôlier", "Peintre", "Comptable"].index(detail['role']))
                if st.form_submit_button("💾 Sauvegarder"):
                    updates = {"nom": m_nom, "username": m_pseudo, "role": m_role}
                    if m_mdp: updates["password_hash"] = hashlib.sha256(m_mdp.encode()).hexdigest()
                    update_record('utilisateurs', user_id, updates)
                    st.success("✅ Utilisateur modifié !"); st.rerun()
            if st.button(f"🗑️ Supprimer {detail['nom']}", type="secondary"):
                delete_record('utilisateurs', user_id)
                st.success("Utilisateur supprimé !"); st.rerun()

# ==========================================
# 5. EXÉCUTION PRINCIPALE
# ==========================================
query_params = st.query_params
if "veh_id" in query_params:
    show_qr_dashboard(int(query_params["veh_id"]))
else:
    if module_name == "dashboard": show_dashboard()
    elif module_name == "clients": show_clients()
    elif module_name == "vehicules": show_vehicules()
    elif module_name == "reception": show_reception()
    elif module_name == "sinistres": show_sinistres()
    elif module_name == "devis": show_devis()
    elif module_name == "ordres": show_ordres()
    elif module_name == "atelier": show_atelier()
    elif module_name == "qrcode": show_qrcode()
    elif module_name == "users": show_users()
