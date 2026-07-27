# ==========================================
# LNS GARAGE PRO - APPLICATION COMPLÈTE
# Design ERP Premium & JSONDB
# ==========================================

import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import hashlib
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

# Importation du moteur JSONDB
from database import json_db as db

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="LNS GARAGE PRO", page_icon="🚗", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS POUR DESIGN ERP PREMIUM ---
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    :root {
        --primary-color: #1E3A8A; /* Bleu Roi */
        --secondary-color: #3B82F6; /* Bleu Clair */
        --bg-color: #F8FAFC;
        --text-color: #1E293B;
        --card-bg: #FFFFFF;
        --border-radius: 12px;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text-color);
    }

    /* Main Layout */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E3A8A 0%, #172554 100%);
        color: white;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
        color: white !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.2);
    }
    
    /* Sidebar Radio Buttons (Menu) */
    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 10px;
        width: 100%;
    }
    [data-testid="stSidebar"] [role="radio"] {
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.1);
        background-color: rgba(255,255,255,0.05);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
    }
    [data-testid="stSidebar"] [role="radio"]:hover {
        background-color: rgba(255,255,255,0.15);
        border-color: var(--secondary-color);
    }
    [data-testid="stSidebar"] [role="radio"][aria-checked="true"] {
        background-color: var(--secondary-color);
        border-color: var(--secondary-color);
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3);
        font-weight: 600;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 4px 6px rgba(30, 58, 138, 0.2);
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 12px rgba(30, 58, 138, 0.3);
        color: white;
    }
    .stButton>button[kind="secondary"] {
        background: #F1F5F9;
        color: #1E293B;
        border: 1px solid #E2E8F0;
        box-shadow: none;
    }

    /* KPI Cards */
    .kpi-card {
        background-color: var(--card-bg);
        border-radius: var(--border-radius);
        padding: 24px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-top: 4px solid var(--primary-color);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
    }
    .kpi-card h3 {
        color: #64748B;
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .kpi-card h1 {
        color: var(--primary-color);
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #F1F5F9;
        padding: 6px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px;
        color: #64748B;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--card-bg);
        color: var(--primary-color);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* DataFrames */
    .stDataFrame {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Form Inputs */
    .stTextInput>div>div, .stNumberInput>div>div, .stTextArea>div>div, .stSelectbox>div>div {
        border-radius: 8px;
        border-color: #E2E8F0;
    }
    
    /* Expander */
    .stExpander {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        background-color: #FFFFFF;
    }

    /* Titres */
    h1, h2, h3 {
        color: var(--text-color) !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. INITIALISATION BASE DE DONNÉES JSON ---
db.initialize_database()

# Palette de couleurs pour les graphiques
COLOR_PALETTE = ['#1E3A8A', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#10B981', '#34D399']

# --- 4. MENU DE NAVIGATION ---
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
# FONCTIONS UTILITAIRES
# ==========================================
def get_df(entity):
    return pd.DataFrame(db.get_all_records(entity))

# ==========================================
# DÉFINITION DES MODULES
# ==========================================

# --- MODULE 1 : TABLEAU DE BORD ---
def show_dashboard():
    st.title("📊 Tableau de Bord")
    st.markdown("### Vue d'ensemble de l'activité")
    
    nb_clients = len(db.get_all_records('clients'))
    nb_vehicules = len(db.get_all_records('vehicules'))
    nb_devis_attente = len([d for d in db.get_all_records('devis') if d.get('statut') == 'En attente'])
    nb_factures_impayees = len([f for f in db.get_all_records('factures') if f.get('statut_paiement') == 'Impayée'])
    
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

# --- MODULE 2 : CLIENTS ---
def show_clients():
    st.title("👤 Gestion des Clients")
    tab1, tab2, tab3 = st.tabs(["📋 Liste", "➕ Ajouter", "🔍 Détails / Modifier"])
    
    with tab1:
        df = get_df('clients')
        if not df.empty:
            st.dataframe(df[['id', 'nom', 'prenom', 'telephone', 'email', 'ville']], use_container_width=True, hide_index=True)
        else: st.info("Aucun client enregistré.")

    with tab2:
        with st.form("ajout_client"):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nom *")
                prenom = st.text_input("Prénom *")
                telephone = st.text_input("Téléphone *")
            with col2:
                telephone2 = st.text_input("Téléphone secondaire")
                email = st.text_input("Email")
                ville = st.text_input("Ville")
            adresse = st.text_area("Adresse")
            submitted = st.form_submit_button("Enregistrer le client")
            if submitted:
                if nom and prenom and telephone:
                    db.create_record('clients', {"nom": nom, "prenom": prenom, "telephone": telephone, "telephone2": telephone2, "email": email, "adresse": adresse, "ville": ville, "date_creation": str(date.today())})
                    st.success(f"Client {nom} {prenom} ajouté avec succès !")
                else: st.error("Les champs Nom, Prénom et Téléphone sont obligatoires.")

    with tab3:
        df_clients = get_df('clients')
        if not df_clients.empty:
            client_dict = df_clients.apply(lambda row: f"{row['nom']} {row['prenom']} (ID: {row['id']})", axis=1).tolist()
            client_choice = st.selectbox("Choisir un client", client_dict)
            client_id = int(client_choice.split("ID: ")[1].replace(")", ""))
            client_data = db.get_record('clients', client_id)
            
            with st.expander("Modifier ou Supprimer ce client"):
                with st.form("modif_client"):
                    m_nom = st.text_input("Nom", value=client_data['nom'])
                    m_prenom = st.text_input("Prénom", value=client_data['prenom'])
                    m_tel = st.text_input("Téléphone", value=client_data['telephone'])
                    save = st.form_submit_button("Sauvegarder modifications")
                    if save:
                        db.update_record('clients', client_id, {"nom": m_nom, "prenom": m_prenom, "telephone": m_tel})
                        st.success("Client modifié !"); st.rerun()
                if st.button("🗑️ Supprimer ce client", type="secondary"):
                    db.delete_record('clients', client_id)
                    st.warning("Client supprimé !"); st.rerun()
        else: st.info("Veuillez ajouter des clients d'abord.")

# --- MODULE 3 : VÉHICULES ---
def show_vehicules():
    st.title("🚘 Gestion des Véhicules")
    tab1, tab2 = st.tabs(["📋 Liste", "➕ Ajouter"])
    
    with tab1:
        df_v = get_df('vehicules')
        df_c = get_df('clients')
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
                        db.create_record('vehicules', {"client_id": client_id, "immatriculation": immat, "vin": vin, "marque": marque, "modele": modele, "annee": int(annee), "couleur": couleur, "kilometrage": int(kilometrage), "carburant": carburant})
                        st.success(f"Véhicule {immat} ajouté avec succès !")
                    else: st.error("Immatriculation, Marque et Modèle sont obligatoires.")

# --- FONCTION GÉNÉRATION PDF ---
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

# --- MODULE 6 : DEVIS ---
def show_devis():
    st.title("📝 Gestion des Devis")
    tab1, tab2, tab3 = st.tabs(["📋 Liste", "➕ Créer", "🔍 Voir / PDF / Modifier"])
    
    with tab1:
        df_d = get_df('devis')
        df_v = get_df('vehicules')
        df_c = get_df('clients')
        if not df_d.empty:
            df = pd.merge(df_d, df_v, left_on='vehicule_id', right_on='id', suffixes=('_d', '_v'))
            df = pd.merge(df, df_c, left_on='client_id_v', right_on='id', suffixes=('', '_c'))
            df['Client'] = df['nom_c'] + ' ' + df['prenom_c']
            st.dataframe(df[['numero_devis', 'immatriculation', 'Client', 'date_creation', 'statut', 'total_ttc']], use_container_width=True, hide_index=True)
        else: st.info("Aucun devis créé pour le moment.")

    with tab2:
        df_v = get_df('vehicules')
        df_c = get_df('clients')
        if df_v.empty or df_c.empty: st.error("⚠️ Vous devez ajouter un client et un véhicule avant de créer un devis !")
        else:
            df_veh = pd.merge(df_v, df_c, left_on='client_id', right_on='id', suffixes=('_v', '_c'))
            df_veh['display'] = df_veh.apply(lambda r: f"{r['immatriculation']} - {r['marque']} {r['modele']} ({r['nom_c']}) [ID:{r['id_v']}]", axis=1)
            veh_choice = st.selectbox("Véhicule concerné", df_veh['display'].tolist())
            veh_id = int(veh_choice.split("[ID:")[1].replace("]", ""))
            
            with st.form("new_devis"):
                col_date, col_num, col_statut = st.columns(3)
                with col_date: date_creation = st.date_input("Date du devis *")
                with col_num: numero_devis = st.text_input("N° Devis", value=db.get_next_numero('devis'))
                with col_statut: statut = st.selectbox("Statut", ["En attente", "Validé", "Refusé"])
                
                st.markdown("---")
                st.subheader("🔧 Main d'œuvre")
                mo_details_list = []
                for task in ["Débosselage", "Redressage", "Soudure", "Préparation", "Peinture", "Polissage"]:
                    col1, col2, col3 = st.columns(3)
                    with col1: h = st.number_input(f"{task} (Heures)", min_value=0.0, step=0.5, key=f"mo_h_{task}")
                    with col2: p = st.number_input(f"Prix / H", min_value=0.0, value=45.0, format="%.2f", key=f"mo_p_{task}")
                    with col3: st.write(f"Total: **{h * p:.2f} dzd**")
                    mo_details_list.append({"desc": task, "qty": h, "price": p, "total": h * p})
                
                st.markdown("---")
                st.subheader("🔩 Pièces et Fournitures")
                pieces_details_list = []
                for i in range(5):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: ref = st.text_input(f"Réf. Pièce {i+1}", key=f"p_ref_{i}")
                    with col2: des = st.text_input(f"Désignation Pièce {i+1}", key=f"p_des_{i}")
                    with col3: qty = st.number_input(f"Qté Pièce {i+1}", min_value=0, step=1, key=f"p_qty_{i}")
                    with col4: px = st.number_input(f"Prix Pièce {i+1}", min_value=0.0, format="%.2f", key=f"p_px_{i}")
                    if qty > 0 and des: pieces_details_list.append({"ref": ref, "desc": des, "qty": int(qty), "price": px, "total": qty * px})
                
                submitted = st.form_submit_button("📊 Calculer et Sauvegarder le Devis")
                if submitted:
                    total_mo = sum(item['total'] for item in mo_details_list)
                    total_pieces = sum(item['total'] for item in pieces_details_list)
                    total_ht = total_mo + total_pieces
                    tva = total_ht * 0.20
                    total_ttc = total_ht + tva
                    
                    db.create_record('devis', {
                        "vehicule_id": veh_id, "numero_devis": numero_devis, "date_creation": str(date_creation),
                        "statut": statut, "total_pieces": total_pieces, "total_mo": total_mo, "tva": tva,
                        "total_ttc": total_ttc, "details": {"mo": mo_details_list, "pieces": pieces_details_list}
                    })
                    st.success(f"✅ Devis {numero_devis} sauvegardé ! Total TTC : {total_ttc:.2f} dzd")

    with tab3:
        all_devis = db.get_all_records('devis')
        if all_devis:
            devis_dict = [f"{d['numero_devis']} (TTC: {d['total_ttc']}dzd) [ID:{d['id']}]" for d in all_devis]
            devis_choice = st.selectbox("Choisir un devis", devis_dict)
            devis_id = int(devis_choice.split("[ID:")[1].replace("]", ""))
            devis_info = db.get_record('devis', devis_id)
            veh_info = db.get_record('vehicules', devis_info['vehicule_id'])
            client_info = db.get_record('clients', veh_info['client_id'])
            
            if st.button("📄 Générer / Télécharger le PDF"):
                pdf_path = generate_devis_pdf(devis_info, client_info, veh_info, devis_info.get('details', {}))
                with open(pdf_path, "rb") as f: pdf_bytes = f.read()
                st.download_button(label="⬇️ Télécharger le Devis PDF", data=pdf_bytes, file_name=f"Devis_{devis_info['numero_devis']}.pdf", mime="application/pdf")
            
            with st.expander("🔄 Modifier le statut du devis"):
                new_statut = st.selectbox("Nouveau statut", ["En attente", "Validé", "Refusé", "Facturé"])
                if st.button("Sauvegarder le nouveau statut"):
                    db.update_record('devis', devis_id, {"statut": new_statut})
                    st.success("Statut mis à jour !"); st.rerun()
        else: st.info("Aucun devis à afficher pour le moment.")

# --- MODULE QR CODE ---
def show_qr_dashboard(veh_id):
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚗 LNS GARAGE PRO - Suivi Véhicule</h1>", unsafe_allow_html=True)
    veh_info = db.get_record('vehicules', veh_id)
    if not veh_info: st.error("Véhicule introuvable."); return
    client_info = db.get_record('clients', veh_info['client_id'])
    
    st.markdown(f"<h3 style='text-align: center;'>{client_info['nom']} - {veh_info['marque']} {veh_info['modele']} ({veh_info['immatriculation']})</h3>", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("🏭 Statut des Travaux")
    ordres = [o for o in db.get_all_records('reparations') if o['vehicule_id'] == veh_id and o['statut'] != 'Terminé']
    if ordres:
        o = ordres[-1]
        suivi = next((s for s in db.get_all_records('suivi_atelier') if s['or_id'] == o['id']), None)
        if suivi: st.progress(int(suivi['progression']) / 100, text=f"Étape : {suivi['etape_actuelle']} ({o['statut']})")
    else: st.success("✅ Réparation Terminée ou Non commencée")

def show_qrcode():
    st.title("📱 Génération de QR Code Client")
    st.info("Génère un QR Code unique pour chaque véhicule.")
    app_base_url = st.text_input("URL de base de l'application", "http://localhost:8501")
    df_vehicules = get_df('vehicules')
    df_clients = get_df('clients')
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

# --- MODULE MULTI-UTILISATEURS ---
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
                    users = db.get_all_records('utilisateurs')
                    if any(u['username'] == username for u in users): st.error("❌ Ce Pseudo existe déjà.")
                    else:
                        hashed_pw = hashlib.sha256(mot_de_passe.encode()).hexdigest()
                        db.create_record('utilisateurs', {"nom": nom, "username": username, "password_hash": hashed_pw, "role": role})
                        st.success(f"✅ Compte '{username}' créé !")
                else: st.error("❌ Tous les champs sont obligatoires.")

    with tab3:
        df_users = get_df('utilisateurs')
        if not df_users.empty:
            user_dict = df_users.apply(lambda r: f"{r['nom']} ({r['username']}) [ID:{r['id']}]", axis=1).tolist()
            user_choice = st.selectbox("Choisir un utilisateur", user_dict)
            user_id = int(user_choice.split("[ID:")[1].replace("]", ""))
            detail = db.get_record('utilisateurs', user_id)
            
            with st.form("modif_user"):
                m_nom = st.text_input("Nom", value=detail['nom'])
                m_pseudo = st.text_input("Pseudo", value=detail['username'])
                m_mdp = st.text_input("Nouveau Mot de passe (laisser vide si inchangé)", type="password")
                m_role = st.selectbox("Rôle", ["Administrateur", "Réceptionniste", "Chef atelier", "Tôlier", "Peintre", "Comptable"], index=["Administrateur", "Réceptionniste", "Chef atelier", "Tôlier", "Peintre", "Comptable"].index(detail['role']))
                if st.form_submit_button("💾 Sauvegarder"):
                    updates = {"nom": m_nom, "username": m_pseudo, "role": m_role}
                    if m_mdp: updates["password_hash"] = hashlib.sha256(m_mdp.encode()).hexdigest()
                    db.update_record('utilisateurs', user_id, updates)
                    st.success("✅ Utilisateur modifié !"); st.rerun()
            
            if st.button(f"🗑️ Supprimer {detail['nom']}", type="secondary"):
                db.delete_record('utilisateurs', user_id)
                st.success("Utilisateur supprimé !"); st.rerun()

# ==========================================
# EXÉCUTION PRINCIPALE
# ==========================================
query_params = st.query_params
if "veh_id" in query_params:
    show_qr_dashboard(int(query_params["veh_id"]))
else:
    if module_name == "dashboard": show_dashboard()
    elif module_name == "clients": show_clients()
    elif module_name == "vehicules": show_vehicules()
    elif module_name == "devis": show_devis()
    elif module_name == "qrcode": show_qrcode()
    elif module_name == "users": show_users()
