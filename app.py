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
    
    tab1, tab2 = st.tabs(["📋 Liste des Véhicules", "➕ Ajouter un Véhicule"])
    
    # --- TAB 1 : LISTE ---
    with tab1:
        vehicules = get_all_records('vehicules')
        
        if not vehicules:
            st.info("Aucun véhicule enregistré.")
        else:
            data_to_display = []
            for v in vehicules:
                # Récupération du client via JSONDB (remplace le JOIN SQL)
                client = get_record('clients', v.get('client_id'))
                
                # Sécurité : vérifier si le client existe
                if client is None:
                    proprietaire = "Client inconnu"
                else:
                    proprietaire = f"{client.get('nom', '')} {client.get('prenom', '')}"
                    
                data_to_display.append({
                    "Immatriculation": v.get('immatriculation', ''),
                    "Marque": v.get('marque', ''),
                    "Modèle": v.get('modele', ''),
                    "Année": v.get('annee', ''),
                    "Couleur": v.get('couleur', ''),
                    "Propriétaire": proprietaire
                })
                
            df_display = pd.DataFrame(data_to_display)
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    # --- TAB 2 : AJOUTER ---
    with tab2:
        clients = get_all_records('clients')
        
        if not clients:
            st.error("Vous devez ajouter un client avant d'ajouter un véhicule !")
        else:
            # Construction du menu déroulant sans Pandas
            client_dict = []
            for c in clients:
                display = f"{c.get('nom', '')} {c.get('prenom', '')} (ID: {c.get('id', '')})"
                client_dict.append(display)
                
            client_choice = st.selectbox("Propriétaire du véhicule", client_dict)
            client_id = int(client_choice.split("ID: ")[1].replace(")", ""))
            
            with st.form("ajout_vehicule"):
                col1, col2 = st.columns(2)
                with col1:
                    immat = st.text_input("Immatriculation *")
                    vin = st.text_input("VIN (Numéro de châssis)")
                    marque = st.text_input("Marque *")
                    modele = st.text_input("Modèle *")
                with col2:
                    annee = st.number_input("Année", min_value=1900, max_value=2025, value=2020)
                    couleur = st.text_input("Couleur")
                    kilometrage = st.number_input("Kilométrage", min_value=0)
                    carburant = st.selectbox("Carburant", ["Diesel", "Essence", "Hybride", "Electrique", "GPL"])
                
                submitted = st.form_submit_button("Enregistrer le véhicule")
                if submitted:
                    if immat and marque and modele:
                        # Sauvegarde via JSONDB
                        create_record('vehicules', {
                            "client_id": client_id,
                            "immatriculation": immat,
                            "vin": vin,
                            "marque": marque,
                            "modele": modele,
                            "annee": int(annee),
                            "couleur": couleur,
                            "kilometrage": int(kilometrage),
                            "carburant": carburant
                        })
                        st.success(f"Véhicule {immat} ajouté avec succès !")
                    else:
                        st.error("Immatriculation, Marque et Modèle sont obligatoires.")
def show_reception():
    st.title("📥 Réception Véhicule")
    
    tab1, tab2, tab3 = st.tabs(["📋 Liste des Réceptions", "➕ Nouvelle Réception", "🔍 Détails / Modifier"])
    
    # --- TAB 1 : LISTE ---
    with tab1:
        receptions = get_all_records('reception')
        
        if not receptions:
            st.info("Aucune réception enregistrée pour le moment.")
        else:
            data_to_display = []
            for r in receptions:
                vehicule = get_record('vehicules', r.get('vehicule_id'))
                client = get_record('clients', vehicule.get('client_id')) if vehicule else None
                
                immat = vehicule.get('immatriculation', '') if vehicule else 'N/A'
                marque = vehicule.get('marque', '') if vehicule else 'N/A'
                modele = vehicule.get('modele', '') if vehicule else 'N/A'
                client_name = f"{client.get('nom', '')} {client.get('prenom', '')}" if client else 'Inconnu'
                
                data_to_display.append({
                    "Date entrée": r.get('date_entree', ''),
                    "Immatriculation": immat,
                    "Marque": marque,
                    "Modèle": modele,
                    "Client": client_name,
                    "Observations": r.get('observations', '')
                })
                
            df_display = pd.DataFrame(data_to_display)
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    # --- TAB 2 : NOUVELLE RÉCEPTION ---
    with tab2:
        vehicules = get_all_records('vehicules')
        clients = get_all_records('clients')
        
        if not vehicules or not clients:
            st.error("⚠️ Vous devez ajouter un client et un véhicule avant de faire une réception !")
        else:
            veh_dict = []
            for v in vehicules:
                client = get_record('clients', v.get('client_id'))
                if client:
                    display = (
                        f"{v.get('immatriculation', '')} - "
                        f"{v.get('marque', '')} "
                        f"{v.get('modele', '')} "
                        f"({client.get('nom', '')} "
                        f"{client.get('prenom', '')}) [ID:{v.get('id', '')}]"
                    )
                    veh_dict.append(display)
            
            if not veh_dict:
                st.warning("Aucun véhicule valide associé à un client.")
            else:
                veh_choice = st.selectbox("Véhicule reçu", veh_dict)
                veh_id = int(veh_choice.split("[ID:")[1].replace("]", ""))
                
                with st.form("new_reception"):
                    st.subheader("🚗 Informations d'entrée")
                    col1, col2 = st.columns(2)
                    with col1:
                        date_entree = st.date_input("Date d'entrée *")
                        kilometrage = st.number_input("Kilométrage à l'entrée", min_value=0, step=1)
                    with col2:
                        niveau_carburant = st.selectbox("Niveau carburant", ["Plein", "3/4", "1/2", "1/4", "Vide", "Inconnu"])
                        
                    observations = st.text_area("Observations / Description du problème par le client")
                    
                    st.subheader("✅ Checklist Véhicule")
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        roue_secours = st.checkbox("Roue de secours")
                        cric = st.checkbox("Cric")
                    with col4:
                        radio = st.checkbox("Radio / Autoradio")
                        documents = st.checkbox("Documents (CG, Assurance)")
                    with col5:
                        clees = st.checkbox("Clés (doublon)")
                        
                    st.subheader("✍️ Signature Client")
                    signature_check = st.checkbox("Le client confirme la remise du véhicule et la véracité de la checklist")
                    signature_nom = st.text_input("Nom et Prénom du signataire (si checkbox coché)")
                    
                    submitted = st.form_submit_button("📥 Enregistrer la Réception")
                    if submitted:
                        if date_entree and signature_check and signature_nom:
                            create_record('reception', {
                                "vehicule_id": veh_id,
                                "date_entree": str(date_entree),
                                "kilometrage": int(kilometrage),
                                "niveau_carburant": niveau_carburant,
                                "observations": observations,
                                "roue_secours": int(roue_secours),
                                "cric": int(cric),
                                "radio": int(radio),
                                "documents": int(documents),
                                "clees": int(clees),
                                "signature_client": signature_nom
                            })
                            st.success("✅ Fiche de réception enregistrée avec succès !")
                        else:
                            st.error("❌ La date, la confirmation de signature et le nom du signataire sont obligatoires.")

    # --- TAB 3 : DÉTAILS / MODIFIER ---
    with tab3:
        receptions = get_all_records('reception')
        
        if not receptions:
            st.info("Aucune réception à modifier pour le moment.")
        else:
            recep_dict = []
            for r in receptions:
                vehicule = get_record('vehicules', r.get('vehicule_id'))
                client = get_record('clients', vehicule.get('client_id')) if vehicule else None
                
                immat = vehicule.get('immatriculation', '') if vehicule else 'N/A'
                client_name = f"{client.get('nom', '')} {client.get('prenom', '')}" if client else 'Inconnu'
                
                display = f"{r.get('date_entree', '')} - {immat} ({client_name}) [ID:{r.get('id', '')}]"
                recep_dict.append(display)
                
            recep_choice = st.selectbox("Choisir une fiche de réception", recep_dict)
            recep_id = int(recep_choice.split("[ID:")[1].replace("]", ""))
            
            detail = get_record('reception', recep_id)
            
            if detail is None:
                st.error("Fiche de réception introuvable dans la base de données.")
                return
            
            st.write(f"**Véhicule ID:** {detail.get('vehicule_id', '')} | **Date entrée:** {detail.get('date_entree', '')}")
            st.write(f"**Kilométrage:** {detail.get('kilometrage', 0)} km | **Carburant:** {detail.get('niveau_carburant', '')}")
            st.write(f"**Observations:** {detail.get('observations', '')}")
            
            st.markdown("---")
            st.write("**Checklist :**")
            checklist_items = {
                "Roue de secours": detail.get('roue_secours', 0),
                "Cric": detail.get('cric', 0),
                "Radio": detail.get('radio', 0),
                "Documents": detail.get('documents', 0),
                "Clés": detail.get('clees', 0)
            }
            for item, val in checklist_items.items():
                icon = "✅" if val else "❌"
                st.write(f"{icon} {item}")
                
            st.write(f"**Signataire :** {detail.get('signature_client', '')}")
            
            with st.expander("🔧 Modifier ou Supprimer cette fiche"):
                with st.form("modif_reception"):
                    m_obs = st.text_area("Observations", value=detail.get('observations', ''))
                    m_km = st.number_input("Kilométrage", value=int(detail.get('kilometrage', 0)))
                    
                    m_roue = st.checkbox("Roue de secours", value=bool(detail.get('roue_secours', 0)))
                    m_cric = st.checkbox("Cric", value=bool(detail.get('cric', 0)))
                    m_radio = st.checkbox("Radio", value=bool(detail.get('radio', 0)))
                    m_docs = st.checkbox("Documents", value=bool(detail.get('documents', 0)))
                    m_clees = st.checkbox("Clés", value=bool(detail.get('clees', 0)))
                    
                    save = st.form_submit_button("Sauvegarder modifications")
                    if save:
                        update_record('reception', recep_id, {
                            "observations": m_obs,
                            "kilometrage": int(m_km),
                            "roue_secours": int(m_roue),
                            "cric": int(m_cric),
                            "radio": int(m_radio),
                            "documents": int(m_docs),
                            "clees": int(m_clees)
                        })
                        st.success("Fiche modifiée !")
                        st.rerun()
                
                if st.button("🗑️ Supprimer cette fiche de réception", type="secondary"):
                    delete_record('reception', recep_id)
                    st.warning("Fiche supprimée !")
                    st.rerun()
def show_sinistres():
    st.title("🛡️ Sinistres & Assurances")
    
    tab1, tab2, tab3 = st.tabs(["📋 Liste des Sinistres", "➕ Nouveau Sinistre", "🔍 Détails / Modifier"])
    
    # --- TAB 1 : LISTE ---
    with tab1:
        sinistres = get_all_records('assurances')
        
        if not sinistres:
            st.info("Aucun sinistre d'assurance enregistré.")
        else:
            data_to_display = []
            for s in sinistres:
                vehicule = get_record('vehicules', s.get('vehicule_id'))
                client = get_record('clients', vehicule.get('client_id')) if vehicule else None
                
                immat = vehicule.get('immatriculation', '') if vehicule else 'N/A'
                client_name = f"{client.get('nom', '')} {client.get('prenom', '')}" if client else 'Inconnu'
                
                data_to_display.append({
                    "N° Dossier": s.get('numero_dossier', ''),
                    "Compagnie": s.get('compagnie', ''),
                    "Immatriculation": immat,
                    "Client": client_name,
                    "Date Expertise": s.get('date_expertise', ''),
                    "Montant Validé": s.get('montant_valide', 0)
                })
                
            df_display = pd.DataFrame(data_to_display)
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    # --- TAB 2 : AJOUTER ---
    with tab2:
        vehicules = get_all_records('vehicules')
        clients = get_all_records('clients')
        
        if not vehicules or not clients:
            st.error("⚠️ Vous devez ajouter un client et un véhicule avant de créer un sinistre !")
        else:
            veh_dict = []
            for v in vehicules:
                client = get_record('clients', v.get('client_id'))
                if client:
                    display = (
                        f"{v.get('immatriculation', '')} - "
                        f"{client.get('nom', '')} "
                        f"{client.get('prenom', '')} [VehID:{v.get('id', '')}]"
                    )
                    veh_dict.append(display)
                    
            if not veh_dict:
                st.warning("Aucun véhicule valide associé à un client.")
            else:
                with st.form("new_sinistre"):
                    st.subheader("🆕 Ouverture de Dossier Sinistre")
                    veh_choice = st.selectbox("Véhicule concerné *", veh_dict)
                    veh_id = int(veh_choice.split("[VehID:")[1].replace("]", ""))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        compagnie = st.text_input("Compagnie d'assurance * (ex: MAIF, AXA)")
                        numero_dossier = st.text_input("N° Dossier Assurance *")
                        expert = st.text_input("Nom de l'Expert mandateur")
                    with col2:
                        date_expertise = st.date_input("Date de l'expertise prévue *")
                        montant_valide = st.number_input("Montant validé par l'expert (€)", min_value=0.0, format="%.2f")
                        
                    commentaires = st.text_area("Commentaires / Observations de l'expert")
                    
                    submitted = st.form_submit_button("🛡️ Créer le Sinistre")
                    if submitted:
                        if compagnie and numero_dossier and date_expertise:
                            create_record('assurances', {
                                "vehicule_id": veh_id,
                                "compagnie": compagnie,
                                "numero_dossier": numero_dossier,
                                "expert": expert,
                                "date_expertise": str(date_expertise),
                                "montant_valide": float(montant_valide),
                                "commentaires": commentaires
                            })
                            st.success(f"✅ Dossier sinistre {numero_dossier} créé avec succès !")
                        else:
                            st.error("❌ La Compagnie, le N° Dossier et la Date sont obligatoires.")

    # --- TAB 3 : MODIFIER / SUPPRIMER ---
    with tab3:
        sinistres = get_all_records('assurances')
        
        if not sinistres:
            st.info("Aucun sinistre à modifier.")
        else:
            sin_dict = []
            for s in sinistres:
                vehicule = get_record('vehicules', s.get('vehicule_id'))
                immat = vehicule.get('immatriculation', '') if vehicule else 'N/A'
                
                display = f"{s.get('numero_dossier', '')} - {s.get('compagnie', '')} ({immat}) [SinID:{s.get('id', '')}]"
                sin_dict.append(display)
                
            sin_choice = st.selectbox("Choisir un sinistre", sin_dict)
            sin_id = int(sin_choice.split("[SinID:")[1].replace("]", ""))
            
            detail = get_record('assurances', sin_id)
            
            if detail is None:
                st.error("Sinistre introuvable dans la base de données.")
                return
            
            with st.form("modif_sinistre"):
                col1, col2 = st.columns(2)
                with col1:
                    m_compagnie = st.text_input("Compagnie *", value=detail.get('compagnie', ''))
                    m_dossier = st.text_input("N° Dossier *", value=detail.get('numero_dossier', ''))
                    m_expert = st.text_input("Expert", value=detail.get('expert', ''))
                with col2:
                    # Sécurité sur la date
                    current_date = detail.get('date_expertise', str(date.today()))
                    m_date = st.date_input("Date expertise", value=pd.to_datetime(current_date))
                    m_montant = st.number_input("Montant validé (€)", min_value=0.0, format="%.2f", value=float(detail.get('montant_valide', 0.0)))
                
                m_comments = st.text_area("Commentaires", value=detail.get('commentaires', ''))
                
                save = st.form_submit_button("💾 Sauvegarder")
                if save:
                    update_record('assurances', sin_id, {
                        "compagnie": m_compagnie,
                        "numero_dossier": m_dossier,
                        "expert": m_expert,
                        "date_expertise": str(m_date),
                        "montant_valide": float(m_montant),
                        "commentaires": m_comments
                    })
                    st.success("✅ Sinistre mis à jour !")
                    st.rerun()
            
            st.markdown("---")
            if st.button(f"🗑️ Supprimer le sinistre {detail.get('numero_dossier', '')}", type="secondary"):
                delete_record('assurances', sin_id)
                st.success("Sinistre supprimé !")
                st.rerun()


# --- FONCTION GÉNÉRATION PDF ---
def generate_devis_pdf(devis_info, client_info, vehicule_info, details):
    # S'assurer que le dossier pdf existe
    if not os.path.exists("pdf"):
        os.makedirs("pdf")
        
    # Sécurisation des dictionnaires pour éviter les KeyError dans ReportLab
    devis_info = devis_info if devis_info else {}
    client_info = client_info if client_info else {}
    vehicule_info = vehicule_info if vehicule_info else {}
    details = details if details else {}
        
    pdf_path = f"pdf/Devis_{devis_info.get('numero_devis', 'inconnu')}.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    
    styles = getSampleStyleSheet()
    elements = []
    
    # En-tête
    elements.append(Paragraph("LNS GARAGE PRO - DEVIS", styles['Title']))
    elements.append(Spacer(1, 15))
    
    # Informations générales (Utilisation de .get() partout)
    info_data = [
        [f"Client: {client_info.get('nom', '')} {client_info.get('prenom', '')}", f"Date: {devis_info.get('date_creation', '')}"],
        [f"Adresse: {client_info.get('adresse', 'N/A')}", f"N° Devis: {devis_info.get('numero_devis', '')}"],
        [f"Véhicule: {vehicule_info.get('marque', '')} {vehicule_info.get('modele', '')}", f"Immat: {vehicule_info.get('immatriculation', '')}"],
        [f"Carburant: {vehicule_info.get('carburant', 'N/A')}", f"Statut: {devis_info.get('statut', '')}"]
    ]
    info_table = Table(info_data, colWidths=[120*mm, 60*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    # Tableau des travaux et pièces
    table_data = [["Type", "Description", "Quantité", "Prix Unitaire", "Total"]]
    
    # Ajout Main d'œuvre
    for item in details.get('mo', []):
        if item.get('qty', 0) > 0:
            table_data.append([
                "MO", 
                item.get('desc', ''), 
                f"{item.get('qty', 0)} H", 
                f"{item.get('price', 0):.2f} dzd", 
                f"{item.get('total', 0):.2f} dzd"
            ])
            
    # Ajout Pièces
    for item in details.get('pieces', []):
        if item.get('qty', 0) > 0:
            table_data.append([
                "Pièce", 
                f"{item.get('ref', '')} - {item.get('desc', '')}", 
                f"{item.get('qty', 0)}", 
                f"{item.get('price', 0):.2f} dzd", 
                f"{item.get('total', 0):.2f} dzd"
            ])
            
    items_table = Table(table_data, colWidths=[20*mm, 70*mm, 25*mm, 30*mm, 30*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 20))
    
    # Totaux
    total_mo = devis_info.get('total_mo', 0)
    total_pieces = devis_info.get('total_pieces', 0)
    ht = total_mo + total_pieces
    tva = devis_info.get('tva', 0)
    total_ttc = devis_info.get('total_ttc', 0)
    
    totals_data = [
        ["Total Main d'œuvre", f"{total_mo:.2f} dzd"],
        ["Total Pièces", f"{total_pieces:.2f} dzd"],
        ["Total Hors Taxe (HT)", f"{ht:.2f} dzd"],
        ["TVA (20%)", f"{tva:.2f} dzd"],
        ["Total TTC (À payer)", f"{total_ttc:.2f} dzd"]
    ]
    totals_table = Table(totals_data, colWidths=[120*mm, 50*mm])
    totals_table.setStyle(TableStyle([
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ]))
    elements.append(totals_table)
    
    # Pied de page
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Signature du Garage:", styles['Normal']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Signature du Client (Bon pour accord):", styles['Normal']))
    
    doc.build(elements)
    return pdf_path
def show_devis():
    st.title("📝 Gestion des Devis")
    
    tab1, tab2, tab3 = st.tabs(["📋 Liste des Devis", "➕ Créer un Devis", "🔍 Voir / PDF / Modifier"])
    
    # --- TAB 1 : LISTE ---
    with tab1:
        all_devis = get_all_records('devis')
        
        if not all_devis:
            st.info("Aucun devis créé pour le moment.")
        else:
            data_to_display = []
            for d in all_devis:
                vehicule = get_record('vehicules', d.get('vehicule_id'))
                client = get_record('clients', vehicule.get('client_id')) if vehicule else None
                
                immat = vehicule.get('immatriculation', '') if vehicule else 'N/A'
                client_name = f"{client.get('nom', '')} {client.get('prenom', '')}" if client else 'Inconnu'
                
                data_to_display.append({
                    "N° Devis": d.get('numero_devis', ''),
                    "Immatriculation": immat,
                    "Client": client_name,
                    "Date création": d.get('date_creation', ''),
                    "Statut": d.get('statut', ''),
                    "Total TTC": d.get('total_ttc', 0)
                })
                
            df_display = pd.DataFrame(data_to_display)
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    # --- TAB 2 : CRÉATION ---
    with tab2:
        vehicules = get_all_records('vehicules')
        clients = get_all_records('clients')
        
        if not vehicules or not clients:
            st.error("⚠️ Vous devez ajouter un client et un véhicule avant de créer un devis !")
        else:
            veh_dict = []
            for v in vehicules:
                client = get_record('clients', v.get('client_id'))
                if client:
                    display = (
                        f"{v.get('immatriculation', '')} - "
                        f"{v.get('marque', '')} "
                        f"{v.get('modele', '')} "
                        f"({client.get('nom', '')} "
                        f"{client.get('prenom', '')}) [ID:{v.get('id', '')}]"
                    )
                    veh_dict.append(display)
                    
            if not veh_dict:
                st.warning("Aucun véhicule valide associé à un client.")
            else:
                veh_choice = st.selectbox("Véhicule concerné", veh_dict)
                veh_id = int(veh_choice.split("[ID:")[1].replace("]", ""))
                
                with st.form("new_devis"):
                    col_date, col_num, col_statut = st.columns(3)
                    with col_date:
                        date_creation = st.date_input("Date du devis *")
                    with col_num:
                        # Génération automatique via JSONDB
                        numero_devis = st.text_input("N° Devis", value=get_next_numero("devis"))
                    with col_statut:
                        statut = st.selectbox("Statut", ["En attente", "Validé", "Refusé"])
                    
                    st.markdown("---")
                    st.subheader("🔧 Main d'œuvre")
                    mo_tasks = ["Débosselage", "Redressage", "Soudure", "Préparation", "Peinture", "Polissage"]
                    mo_details_list = []
                    
                    for task in mo_tasks:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            h = st.number_input(f"{task} (Heures)", min_value=0.0, step=0.5, key=f"mo_h_{task}")
                        with col2:
                            p = st.number_input(f"Prix / H", min_value=0.0, value=45.0, format="%.2f", key=f"mo_p_{task}")
                        with col3:
                            st.write(f"Total: **{h * p:.2f} dzd**")
                        mo_details_list.append({"desc": task, "qty": h, "price": p, "total": h * p})
                    
                    st.markdown("---")
                    st.subheader("🔩 Pièces et Fournitures")
                    pieces_details_list = []
                    
                    for i in range(5):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            ref = st.text_input(f"Réf. Pièce {i+1}", key=f"p_ref_{i}")
                        with col2:
                            des = st.text_input(f"Désignation Pièce {i+1}", key=f"p_des_{i}")
                        with col3:
                            qty = st.number_input(f"Qté Pièce {i+1}", min_value=0, step=1, key=f"p_qty_{i}")
                        with col4:
                            px = st.number_input(f"Prix Pièce {i+1}", min_value=0.0, format="%.2f", key=f"p_px_{i}")
                        
                        if qty > 0 and des:
                            pieces_details_list.append({"ref": ref, "desc": des, "qty": qty, "price": px, "total": qty * px})
                    
                    submitted = st.form_submit_button("📊 Calculer et Sauvegarder le Devis")
                    if submitted:
                        total_mo = sum(item['total'] for item in mo_details_list)
                        total_pieces = sum(item['total'] for item in pieces_details_list)
                        total_ht = total_mo + total_pieces
                        tva = total_ht * 0.20
                        total_ttc = total_ht + tva
                        
                        # Sauvegarde via JSONDB (le dictionnaire details est sauvegardé natif, sans json.dumps)
                        create_record('devis', {
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
                        })
                        st.success(f"✅ Devis {numero_devis} sauvegardé ! Total TTC : {total_ttc:.2f} dzd")

    # --- TAB 3 : VOIR / PDF / MODIFIER ---
    with tab3:
        all_devis = get_all_records('devis')
        
        if not all_devis:
            st.info("Aucun devis à afficher pour le moment.")
        else:
            devis_dict = []
            for d in all_devis:
                vehicule = get_record('vehicules', d.get('vehicule_id'))
                client = get_record('clients', vehicule.get('client_id')) if vehicule else None
                
                immat = vehicule.get('immatriculation', '') if vehicule else 'N/A'
                client_name = f"{client.get('nom', '')} {client.get('prenom', '')}" if client else 'Inconnu'
                
                display = f"{d.get('numero_devis', '')} - {client_name} ({immat}) TTC: {d.get('total_ttc', 0)}dzd [ID:{d.get('id', '')}]"
                devis_dict.append(display)
                
            devis_choice = st.selectbox("Choisir un devis", devis_dict)
            devis_id = int(devis_choice.split("[ID:")[1].replace("]", ""))
            
            # Récupération de l'enregistrement via JSONDB
            devis_info = get_record('devis', devis_id)
            
            # Sécurité : vérifier si l'enregistrement existe
            if devis_info is None:
                st.error("Devis introuvable dans la base de données.")
                return
                
            veh_info = get_record('vehicules', devis_info.get('vehicule_id'))
            client_info = get_record('clients', veh_info.get('client_id')) if veh_info else None
            
            # Affichage des infos
            st.write(f"**Statut actuel :** {devis_info.get('statut', '')} | **Total TTC :** {devis_info.get('total_ttc', 0)} dzd")
            
            # Bouton Génération PDF
            if st.button("📄 Générer / Télécharger le PDF"):
                # Les détails sont déjà un dictionnaire dans JSONDB
                details = devis_info.get('details', {"mo": [], "pieces": []})
                
                # Sécurité supplémentaire pour la génération PDF
                safe_veh_info = veh_info if veh_info else {}
                safe_client_info = client_info if client_info else {}
                
                pdf_path = generate_devis_pdf(devis_info, safe_client_info, safe_veh_info, details)
                
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                
                st.download_button(
                    label="⬇️ Télécharger le Devis PDF",
                    data=pdf_bytes,
                    file_name=f"Devis_{devis_info.get('numero_devis', 'inconnu')}.pdf",
                    mime="application/pdf"
                )
            
            # Modifier le statut
            with st.expander("🔄 Modifier le statut du devis"):
                statuts_possibles = ["En attente", "Validé", "Refusé", "Facturé"]
                current_statut = devis_info.get('statut', 'En attente')
                current_index = statuts_possibles.index(current_statut) if current_statut in statuts_possibles else 0
                
                new_statut = st.selectbox("Nouveau statut", statuts_possibles, index=current_index)
                if st.button("Sauvegarder le nouveau statut"):
                    # Mise à jour via JSONDB
                    update_record('devis', devis_id, {"statut": new_statut})
                    st.success("Statut mis à jour !")
                    st.rerun()
def show_ordres():
    st.title("🔧 Ordres de Réparation (OR)")
    
    tab1, tab2, tab3 = st.tabs(["📋 Liste des Ordres", "➕ Créer un Ordre", "🔍 Suivi / Modifier"])
    
    # --- TAB 1 : LISTE ---
    with tab1:
        ordres = get_all_records('reparations')
        
        if not ordres:
            st.info("Aucun ordre de réparation créé pour le moment.")
        else:
            data_to_display = []
            for o in ordres:
                vehicule = get_record('vehicules', o.get('vehicule_id'))
                client = get_record('clients', vehicule.get('client_id')) if vehicule else None
                devis = get_record('devis', o.get('devis_id')) if o.get('devis_id') else None
                
                # Icône visuelle pour le statut
                statut_val = o.get('statut', '')
                if statut_val == "En attente": statut_icon = "⏳ En attente"
                elif statut_val == "En cours": statut_icon = "🔄 En cours"
                elif statut_val == "Suspendu": statut_icon = "⏸️ Suspendu"
                elif statut_val == "Terminé": statut_icon = "✅ Terminé"
                else: statut_icon = statut_val

                data_to_display.append({
                    "N° OR": o.get('numero_or', ''),
                    "N° Devis": devis.get('numero_devis', 'N/A') if devis else 'N/A',
                    "Immatriculation": vehicule.get('immatriculation', '') if vehicule else '',
                    "Client": f"{client.get('nom', '')} {client.get('prenom', '')}" if client else 'Inconnu',
                    "Responsable": o.get('responsable', ''),
                    "Statut": statut_icon,
                    "Date début": o.get('date_debut', ''),
                    "Date fin": o.get('date_fin', '')
                })
                
            df_display = pd.DataFrame(data_to_display)
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    # --- TAB 2 : CRÉATION ---
    with tab2:
        vehicules = get_all_records('vehicules')
        clients = get_all_records('clients')
        
        if not vehicules or not clients:
            st.error("⚠️ Vous devez ajouter un client et un véhicule avant de créer un OR !")
        else:
            # Construction du menu déroulant sans Pandas merge
            veh_dict = []
            for v in vehicules:
                client = get_record('clients', v.get('client_id'))
                if client:
                    display = (
                        f"{v.get('immatriculation', '')} - "
                        f"{v.get('marque', '')} "
                        f"{v.get('modele', '')} "
                        f"({client.get('nom', '')} "
                        f"{client.get('prenom', '')}) [VehID:{v.get('id', '')}]"
                    )
                    veh_dict.append(display)
                    
            if not veh_dict:
                st.warning("Aucun véhicule valide associé à un client.")
            else:
                veh_choice = st.selectbox("Véhicule concerné", veh_dict)
                veh_id = int(veh_choice.split("[VehID:")[1].replace("]", ""))
                
                # Filtrage des devis pour le véhicule sélectionné
                all_devis = get_all_records('devis')
                devis_filtered = [d for d in all_devis if d.get('vehicule_id') == veh_id]
                
                devis_options = ["Aucun devis (Travaux internes)"]
                for d in devis_filtered:
                    devis_options.append(f"{d.get('numero_devis', '')} - {d.get('statut', '')} ({d.get('total_ttc', 0)}dzd) [DevisID:{d.get('id', '')}]")
                
                with st.form("new_or"):
                    st.subheader("Association Véhicule / Devis")
                    devis_choice = st.selectbox("Associer à un Devis ?", devis_options)
                    
                    devis_id = None
                    if devis_choice != "Aucun devis (Travaux internes)":
                        devis_id = int(devis_choice.split("[DevisID:")[1].replace("]", ""))
                    
                    st.markdown("---")
                    st.subheader("Planification du Travail")
                    
                    # Génération automatique du numéro OR
                    all_ordres = get_all_records('reparations')
                    last_id_or = max([o.get('id', 0) for o in all_ordres], default=0)
                    default_numero_or = f"OR-{last_id_or+1:04d}"
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        numero_or = st.text_input("N° Ordre de Réparation *", value=default_numero_or)
                        responsable = st.text_input("Responsable / Chef d'atelier *")
                    with col2:
                        date_debut = st.date_input("Date de début prévue *")
                    with col3:
                        date_fin = st.date_input("Date de fin prévue *")
                        
                    statut = st.selectbox("Statut initial", ["En attente", "En cours", "Suspendu", "Terminé"])
                    
                    submitted = st.form_submit_button("🛠️ Créer l'Ordre de Réparation")
                    if submitted:
                        if numero_or and responsable and date_debut and date_fin:
                            if str(date_fin) < str(date_debut):
                                st.error("❌ La date de fin prévue doit être après la date de début !")
                            else:
                                # Sauvegarde via JSONDB
                                create_record('reparations', {
                                    "devis_id": devis_id,
                                    "vehicule_id": veh_id,
                                    "numero_or": numero_or,
                                    "responsable": responsable,
                                    "date_debut": str(date_debut),
                                    "date_fin": str(date_fin),
                                    "statut": statut
                                })
                                st.success(f"✅ Ordre de Réparation {numero_or} créé avec succès !")
                        else:
                            st.error("❌ Le numéro, le responsable et les dates sont obligatoires.")

    # --- TAB 3 : SUIVI / MODIFIER ---
    with tab3:
        ordres = get_all_records('reparations')
        
        if not ordres:
            st.info("Aucun ordre de réparation à suivre pour le moment.")
        else:
            or_dict = []
            for o in ordres:
                vehicule = get_record('vehicules', o.get('vehicule_id'))
                client = get_record('clients', vehicule.get('client_id')) if vehicule else None
                
                client_name = f"{client.get('nom', '')} {client.get('prenom', '')}" if client else 'Inconnu'
                immat = vehicule.get('immatriculation', '') if vehicule else 'N/A'
                
                display = f"{o.get('numero_or', '')} - {client_name} ({immat}) Statut: {o.get('statut', '')} [ORID:{o.get('id', '')}]"
                or_dict.append(display)
                
            or_choice = st.selectbox("Choisir un Ordre de Réparation", or_dict)
            or_id = int(or_choice.split("[ORID:")[1].replace("]", ""))
            
            # Récupération de l'enregistrement
            detail = get_record('reparations', or_id)
            
            # Sécurité : vérifier si l'enregistrement existe
            if detail is None:
                st.error("Ordre de réparation introuvable dans la base de données.")
                return
            
            # Affichage visuel du statut
            statut_color = {
                "En attente": "🟡", "En cours": "🔵", "Suspendu": "🔴", "Terminé": "🟢"
            }
            current_color = statut_color.get(detail.get('statut', ''), "⚪")
            
            st.write(f"### {current_color} Ordre N° {detail.get('numero_or', '')}")
            st.write(f"**Responsable :** {detail.get('responsable', '')} | **Période :** {detail.get('date_debut', '')} au {detail.get('date_fin', '')}")
            
            # Formulaire de mise à jour rapide
            with st.form("update_or"):
                st.subheader("Mise à jour du Suivi")
                
                statuts_possibles = ["En attente", "En cours", "Suspendu", "Terminé"]
                current_statut = detail.get('statut', 'En attente')
                current_index = statuts_possibles.index(current_statut) if current_statut in statuts_possibles else 0
                
                new_statut = st.selectbox("Statut des travaux", statuts_possibles, index=current_index)
                
                col1, col2 = st.columns(2)
                with col1:
                    # Sécurité sur la date
                    current_date_debut = detail.get('date_debut', str(date.today()))
                    new_debut = st.date_input("Nouvelle date de début", value=pd.to_datetime(current_date_debut))
                with col2:
                    current_date_fin = detail.get('date_fin', str(date.today()))
                    new_fin = st.date_input("Nouvelle date de fin prévue", value=pd.to_datetime(current_date_fin))
                
                new_resp = st.text_input("Responsable", value=detail.get('responsable', ''))
                
                save = st.form_submit_button("Sauvegarder les modifications")
                if save:
                    # Mise à jour via JSONDB
                    update_record('reparations', or_id, {
                        "statut": new_statut,
                        "date_debut": str(new_debut),
                        "date_fin": str(new_fin),
                        "responsable": new_resp
                    })
                    st.success("Ordre de réparation mis à jour !")
                    st.rerun()
                    
            # Bouton Supprimer
            st.markdown("---")
            if st.button("🗑️ Supprimer cet Ordre de Réparation", type="secondary"):
                delete_record('reparations', or_id)
                st.warning("Ordre supprimé !")
                st.rerun()
def show_atelier():
    st.title("🏭 Suivi Atelier - Progression des Travaux")
    
    # Définition des étapes obligatoires du workflow garage
    etapes_atelier = [
        "Réception", 
        "Diagnostic", 
        "Tôlerie", 
        "Préparation", 
        "Peinture", 
        "Remontage", 
        "Contrôle Qualité", 
        "Livraison"
    ]
    
    tab1, tab2 = st.tabs(["🚜 Tableau de l'Atelier", "📊 Progression Détaillée"])
    
    # Récupération de tous les ordres de réparation
    all_ordres = get_all_records('reparations')
    
    # Filtrer les OR non terminés pour l'atelier
    active_ordres = [o for o in all_ordres if o.get('statut', '') != 'Terminé']
    
    # --- TAB 1 : TABLEAU DE L'ATELIER ---
    with tab1:
        if not active_ordres:
            st.info("🎉 Aucun véhicule en cours de réparation dans l'atelier !")
        else:
            data_to_display = []
            for o in active_ordres:
                vehicule = get_record('vehicules', o.get('vehicule_id'))
                client = get_record('clients', vehicule.get('client_id')) if vehicule else None
                
                data_to_display.append({
                    "N° OR": o.get('numero_or', ''),
                    "Immatriculation": vehicule.get('immatriculation', '') if vehicule else '',
                    "Marque": vehicule.get('marque', '') if vehicule else '',
                    "Modèle": vehicule.get('modele', '') if vehicule else '',
                    "Client": f"{client.get('nom', '')} {client.get('prenom', '')}" if client else 'Inconnu',
                    "Statut": o.get('statut', ''),
                    "Responsable": o.get('responsable', '')
                })
                
            df_display = pd.DataFrame(data_to_display)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # --- TAB 2 : PROGRESSION DÉTAILLÉE ---
    with tab2:
        if not active_ordres:
            st.info("Aucun véhicule à suivre pour le moment.")
        else:
            # Construction du menu déroulant sans Pandas merge
            or_dict = []
            for o in active_ordres:
                vehicule = get_record('vehicules', o.get('vehicule_id'))
                client = get_record('clients', vehicule.get('client_id')) if vehicule else None
                
                immat = vehicule.get('immatriculation', '') if vehicule else 'N/A'
                client_name = f"{client.get('nom', '')} {client.get('prenom', '')}" if client else 'Inconnu'
                
                display = f"{o.get('numero_or', '')} - {immat} ({client_name}) [ORID:{o.get('id', '')}]"
                or_dict.append(display)
                
            or_choice = st.selectbox("Choisir un Ordre de Réparation à suivre", or_dict)
            or_id = int(or_choice.split("[ORID:")[1].replace("]", ""))
            
            # Récupérer ou créer les infos de suivi pour cet OR
            all_suivi = get_all_records('suivi_atelier')
            suivi_data = next((s for s in all_suivi if s.get('or_id') == or_id), None)
            
            # Si le véhicule n'a pas encore de suivi, on le crée à l'étape "Réception"
            if suivi_data is None:
                suivi_id = create_record('suivi_atelier', {
                    "or_id": or_id,
                    "etape_actuelle": etapes_atelier[0],
                    "progression": 12
                })
                # Recharger le suivi créé
                suivi_data = get_record('suivi_atelier', suivi_id)
            
            # Sécurité : vérifier si l'enregistrement existe
            if suivi_data is None:
                st.error("Erreur lors de la récupération du suivi atelier.")
                return
            
            current_etape = suivi_data.get('etape_actuelle', etapes_atelier[0])
            current_progress = int(suivi_data.get('progression', 0))
            current_etape_index = etapes_atelier.index(current_etape) if current_etape in etapes_atelier else 0
            
            # Affichage visuel des étapes (Les colonnes avec les icônes)
            st.markdown("---")
            cols = st.columns(len(etapes_atelier))
            
            for i, etape in enumerate(etapes_atelier):
                with cols[i]:
                    if i < current_etape_index:
                        # Etape terminée
                        st.markdown(f"<div style='text-align: center; background-color: #d4edda; padding: 10px; border-radius: 5px; color: black;'><b>✅</b><br>{etape}</div>", unsafe_allow_html=True)
                    elif i == current_etape_index:
                        # Etape en cours
                        st.markdown(f"<div style='text-align: center; background-color: #cce5ff; padding: 10px; border-radius: 5px; color: black; border: 2px solid #1E3A8A;'><b>🔧</b><br><b>{etape}</b></div>", unsafe_allow_html=True)
                    else:
                        # Etape à venir
                        st.markdown(f"<div style='text-align: center; background-color: #f8f9fa; padding: 10px; border-radius: 5px; color: grey;'><b>⬜</b><br>{etape}</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Barre de progression globale
            st.progress(current_progress / 100, text=f"Progression globale : {current_progress}%")
            
            # Formulaire pour avancer le véhicule
            st.subheader("🚀 Avancer le véhicule dans l'atelier")
            
            with st.form("update_etape"):
                new_etape = st.selectbox(
                    "Définir l'étape actuelle :", 
                    etapes_atelier, 
                    index=current_etape_index
                )
                
                submitted = st.form_submit_button("Mettre à jour la progression")
                if submitted:
                    new_etape_index = etapes_atelier.index(new_etape)
                    # Calcul du pourcentage : 8 étapes = 12.5% par étape (on arrondit)
                    new_progress = int((new_etape_index + 1) * (100 / len(etapes_atelier)))
                    
                    # Mise à jour via JSONDB
                    update_record('suivi_atelier', suivi_data.get('id'), {
                        "etape_actuelle": new_etape,
                        "progression": new_progress
                    })
                    
                    # Si on passe à "Livraison", on termine automatiquement l'Ordre de Réparation
                    if new_etape == "Livraison":
                        update_record('reparations', or_id, {
                            "statut": "Terminé"
                        })
                        st.balloons() # Petit effet visuel de réussite !
                        st.success("🎉 Véhicule livré ! L'Ordre de Réparation est maintenant marqué comme TERMINÉ.")
                    else:
                        st.success(f"✅ Progression mise à jour : Étape **{new_etape}** ({new_progress}%)")
                    
                    st.rerun() # Rafraîchir la page pour voir les couleurs changer immédiatement                
def show_stock():
    st.title("📦 Gestion du Stock")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Inventaire", "➕ Entrée Stock", "➖ Sortie Stock", "⚠️ Alertes & Statistiques"])
    
    # --- TAB 1 : INVENTAIRE ---
    with tab1:
        filtre_type = st.selectbox("Filtrer par catégorie", ["Tous", "Consommable", "Pièce"], key="filtre_stock")
        
        stock_items = get_all_records('stock')
        
        if filtre_type != "Tous":
            stock_items = [s for s in stock_items if s.get('type_article', '') == filtre_type]
            
        if not stock_items:
            st.info("Aucun article en stock pour le moment.")
        else:
            data_to_display = []
            for s in stock_items:
                quantite = s.get('quantite', 0)
                seuil = s.get('seuil_alerte', 0)
                
                if quantite == 0:
                    statut = "⚫ Rupture"
                elif quantite <= seuil:
                    statut = "🔴 Stock Faible"
                else:
                    statut = "🟢 OK"
                    
                data_to_display.append({
                    "Statut": statut,
                    "Type": s.get('type_article', ''),
                    "Référence": s.get('reference', ''),
                    "Désignation": s.get('designation', ''),
                    "Qté": quantite,
                    "Prix Achat": s.get('prix_achat', 0),
                    "Prix Vente": s.get('prix_vente', 0)
                })
                
            df_display = pd.DataFrame(data_to_display)
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    # --- TAB 2 : ENTRÉE STOCK ---
    with tab2:
        action = st.radio("Choisir l'action", ["Ajouter un nouvel article", "Réapprovisionner un article existant"])
        
        if action == "Ajouter un nouvel article":
            with st.form("add_article"):
                st.subheader("🆕 Nouvel Article")
                col1, col2 = st.columns(2)
                with col1:
                    type_article = st.selectbox("Type d'article *", ["Consommable", "Pièce"])
                    reference = st.text_input("Référence (ex: PCH-AV01)")
                    designation = st.text_input("Désignation / Nom * (ex: Pare-chocs avant)")
                with col2:
                    quantite = st.number_input("Quantité initiale *", min_value=0, step=1)
                    prix_achat = st.number_input("Prix d'achat unitaire (dzd)", min_value=0.0, format="%.2f")
                    prix_vente = st.number_input("Prix de vente unitaire (dzd)", min_value=0.0, format="%.2f")
                    seuil_alerte = st.number_input("Seuil d'alerte (quantité min) *", min_value=0, step=1, value=5)
                
                submitted = st.form_submit_button("Ajouter au catalogue")
                if submitted:
                    if designation and quantite >= 0:
                        create_record('stock', {
                            "type_article": type_article,
                            "reference": reference,
                            "designation": designation,
                            "quantite": int(quantite),
                            "prix_achat": float(prix_achat),
                            "prix_vente": float(prix_vente),
                            "seuil_alerte": int(seuil_alerte)
                        })
                        st.success(f"✅ Article '{designation}' ajouté avec {quantite} unités !")
                    else:
                        st.error("❌ La désignation et la quantité sont obligatoires.")

        elif action == "Réapprovisionner un article existant":
            stock_items = get_all_records('stock')
            if not stock_items:
                st.warning("Le catalogue est vide. Ajoutez d'abord un nouvel article.")
            else:
                art_dict = []
                for s in stock_items:
                    display = f"{s.get('designation', '')} (Stock actuel: {s.get('quantite', 0)}) [ID:{s.get('id', '')}]"
                    art_dict.append(display)
                    
                art_choice = st.selectbox("Article à réapprovisionner", art_dict)
                art_id = int(art_choice.split("[ID:")[1].replace("]", ""))
                
                qty_add = st.number_input("Quantité ajoutée", min_value=1, step=1)
                new_buy_price = st.number_input("Nouveau prix d'achat (si changé)", min_value=0.0, format="%.2f")
                
                if st.button("📥 Réapprovisionner"):
                    item = get_record('stock', art_id)
                    if item is None:
                        st.error("Article introuvable.")
                        return
                        
                    # Mise à jour de la quantité et du prix d'achat
                    update_record('stock', art_id, {
                        "quantite": item.get('quantite', 0) + int(qty_add),
                        "prix_achat": float(new_buy_price)
                    })
                    st.success(f"✅ Stock mis à jour ! {qty_add} unités ajoutées.")

    # --- TAB 3 : SORTIE STOCK ---
    with tab3:
        stock_items = get_all_records('stock')
        available_items = [s for s in stock_items if s.get('quantite', 0) > 0]
        
        if not available_items:
            st.warning("Aucun article disponible en stock pour une sortie.")
        else:
            art_dict = []
            for s in available_items:
                display = f"{s.get('designation', '')} (Dispo: {s.get('quantite', 0)}) [ID:{s.get('id', '')}]"
                art_dict.append(display)
                
            art_choice = st.selectbox("Article à consommer / sortir", art_dict)
            art_id = int(art_choice.split("[ID:")[1].replace("]", ""))
            
            qty_remove = st.number_input("Quantité sortie", min_value=1, step=1)
            
            if st.button("📤 Sortir du stock"):
                item = get_record('stock', art_id)
                if item is None:
                    st.error("Article introuvable.")
                    return
                    
                current_qty = item.get('quantite', 0)
                if qty_remove > current_qty:
                    st.error(f"❌ Impossible ! Vous essayez de sortir {qty_remove} unités, mais il n'y en a que {current_qty} en stock.")
                else:
                    new_qty = current_qty - int(qty_remove)
                    update_record('stock', art_id, {"quantite": new_qty})
                    st.success(f"✅ {qty_remove} unité(s) sorties du stock !")
                    if new_qty <= 5: # Valeur d'alerte générique
                        st.warning("⚠️ Attention, le stock de cet article est maintenant bas !")

    # --- TAB 4 : ALERTES & STATS ---
    with tab4:
        st.subheader("⚠️ Articles en Stock Faible ou en Rupture")
        stock_items = get_all_records('stock')
        alertes = [s for s in stock_items if s.get('quantite', 0) <= s.get('seuil_alerte', 0)]
        
        if alertes:
            data_alertes = []
            for s in alertes:
                data_alertes.append({
                    "Désignation": s.get('designation', ''),
                    "Qté": s.get('quantite', 0),
                    "Seuil Alerte": s.get('seuil_alerte', 0)
                })
            df_alertes = pd.DataFrame(data_alertes)
            st.dataframe(df_alertes, use_container_width=True, hide_index=True)
        else:
            st.info("🎉 Aucune alerte de stock faible ! Tout est bien approvisionné.")
            
        st.markdown("---")
        st.subheader("📊 Valeur du Stock par Catégorie")
        
        if stock_items:
            # Création d'un DataFrame pour l'analyse
            df_stats = pd.DataFrame(stock_items)
            # Sécurisation des types numériques
            df_stats['quantite'] = pd.to_numeric(df_stats.get('quantite', 0), errors='coerce').fillna(0)
            df_stats['prix_achat'] = pd.to_numeric(df_stats.get('prix_achat', 0), errors='coerce').fillna(0)
            df_stats['valeur_achat'] = df_stats['quantite'] * df_stats['prix_achat']
            
            # Groupement par type_article
            df_grouped = df_stats.groupby('type_article').agg(
                Valeur_Total_Achat=('valeur_achat', 'sum'),
                Total_Unites=('quantite', 'sum')
            ).reset_index()
            
            col1, col2 = st.columns(2)
            with col1:
                fig_px = px.pie(df_grouped, values='Valeur_Total_Achat', names='type_article', 
                               title="Répartition de la Valeur d'Achat du Stock (dzd)", hole=0.4)
                st.plotly_chart(fig_px, use_container_width=True)
            with col2:
                fig_bar = px.bar(df_grouped, x='type_article', y='Total_Unites', 
                                 title="Nombre d'Unités par Catégorie", color='type_article')
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Aucune donnée statistique disponible pour le moment.")
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
    
    st.info("💡 Génère un QR Code unique pour chaque véhicule. Le client pourra scanner ce QR code avec son téléphone pour voir en temps réel l'avancement de ses travaux, les photos avant/après, et ses documents !")
    
    tab1, tab2 = st.tabs(["🔗 Créer un QR Code", "ℹ️ Comment ça marche ?"])
    
    with tab1:
        # URL de l'application (à adapter selon où l'app est hébergée)
        default_url = "http://localhost:8501" 
        app_base_url = st.text_input("URL de base de votre application *", value=default_url, help="Si déployé sur Streamlit Cloud, mettez l'URL publique (ex: https://lnsgarage.streamlit.app)")
        
        vehicules = get_all_records('vehicules')
        clients = get_all_records('clients')
        
        if not vehicules or not clients:
            st.error("Ajoutez d'abord un client et un véhicule !")
        else:
            veh_dict = []
            for v in vehicules:
                client = get_record('clients', v.get('client_id'))
                if client:
                    display = (
                        f"{v.get('immatriculation', '')} - "
                        f"{v.get('marque', '')} "
                        f"{v.get('modele', '')} "
                        f"({client.get('nom', '')} {client.get('prenom', '')}) [VehID:{v.get('id', '')}]"
                    )
                    veh_dict.append(display)
                    
            if not veh_dict:
                st.warning("Aucun véhicule valide associé à un client.")
            else:
                veh_choice = st.selectbox("Choisir le véhicule pour le QR Code", veh_dict)
                veh_id = int(veh_choice.split("[VehID:")[1].replace("]", ""))
                
                # Récupération du véhicule via JSONDB pour l'affichage sécurisé
                selected_veh = get_record('vehicules', veh_id)
                if selected_veh is None:
                    st.error("Véhicule introuvable dans la base de données.")
                    return
                
                # Construire l'URL finale avec le paramètre
                qr_url = f"{app_base_url}?veh_id={veh_id}"
                
                st.markdown("---")
                st.subheader("🔗 URL de Suivi Générée")
                st.code(qr_url, language="plaintext")
                
                # Générer l'image QR Code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_url)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convertir PIL Image en bytes pour Streamlit
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                # Afficher le QR Code
                st.image(byte_im, caption=f"QR Code pour {selected_veh.get('immatriculation', '')}")
                
                # Bouton de Téléchargement
                st.download_button(
                    label="⬇️ Télécharger l'image QR Code (PNG)",
                    data=byte_im,
                    file_name=f"QRCode_Veh_{veh_id}.png",
                    mime="image/png"
                )

    with tab2:
        st.subheader("📚 Guide d'utilisation")
        st.markdown("""
        **1. Comment ça marche ?**
        - L'application crée un lien URL unique lié à l'ID du véhicule (ex: `?veh_id=3`).
        - Ce lien est transformé en image QR Code.
        - Quand le client scanne ce QR Code avec l'appareil photo de son smartphone, son navigateur s'ouvre sur ce lien.
        
        **2. Ce que le client voit :**
        - L'application détecte qu'il arrive via un QR Code.
        - Elle lui affiche une page **simplifiée et mobile-friendly** (sans le menu latéral complexe de l'ERP).
        - Il peut voir : Le statut de l'atelier (Tôlerie, Peinture...), ses photos Avant/Après, et ses documents.
        
        **3. Important pour le déploiement :**
        - Si tu testes sur ton PC, l'URL est `http://localhost:8501`. Le QR Code fonctionnera **si ton téléphone est connecté au même réseau Wi-Fi que ton PC**.
        - Quand tu déploieras l'app sur **Streamlit Cloud**, change cette URL de base avec l'URL publique de ton app (ex: `https://mon-garage.streamlit.app`). Le QR Code fonctionnera alors pour **tout le monde dans le monde entier** !
        """)

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
