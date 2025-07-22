import streamlit as st
import pandas as pd
from pathlib import Path
import re
from datetime import datetime
from PIL import Image
import os
import subprocess
import sys

st.set_page_config(page_icon=':open_book:', page_title='BD produits Latty')

st.markdown("""
    <style>
    /* General font size reduction */
    html, body, .stApp {
        font-size: 1.0rem;
        line-height: 1.0;
    }

    /* General fallback for h2 */
    h2 {
        font-size: 1rem !important;  /* force smaller */
    }

    /* Target specifically Streamlit-markdown headings */
    .stMarkdown h2 {
        font-size: 2rem !important;
    }

    /* Target Streamlit's special heading class (if present) */
    .stMarkdownHeading {
        font-size: 2rem !important;
    }

    /* If Streamlit wraps subheaders in a div with role heading */
    [data-testid="stMarkdownContainer"] h2 {
        font-size: 2rem !important;
    }
    /* Bullet list and paragraph text */
    .stMarkdown p, .stMarkdown li {
        font-size: 0.9rem;
    }

    /* Optional: reduce spacing between bullets */
    .stMarkdown li {
        margin-bottom: 0.2rem;
        line-height: 1.2;
    }

    /* Footer text */
    .footer-container {
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

# dossier_actuel = Path(__file__).parent
# chemin_bd = dossier_actuel/'bd.xlsx'

# Folder where the current script is located
dossier_actuel = os.path.dirname(os.path.abspath(__file__))

# Full path to your Excel file
chemin_bd = os.path.join(dossier_actuel, 'bd.xlsx')

# Charger la base de données
df = pd.read_excel(chemin_bd,index_col='id')

# Supprimer les colonnes vides (entièrement vides)
# df = df.dropna(axis=1, how='all')

# Liste des produits disponibles
produits = df['nom'].dropna().unique()

# Sélection de produit
produit_selectionne = st.sidebar.selectbox("Sélectionnez un produit :", produits)

# Filtrer le DataFrame
ligne_produit = df[df['nom'] == produit_selectionne]


# Afficher uniquement les colonnes avec données non nulles
df = ligne_produit.dropna(axis=1, how='all')

# Affichage
st.title(f"{produit_selectionne}")

product = df.iloc[0]

raw_date = str(product["date_maj"])
try:
    date_obj = pd.to_datetime(raw_date)
    formatted_date = date_obj.strftime("%d/%m/%Y")
except:
    formatted_date = raw_date  # fallback if parsing fails

st.caption(f"Fiche technique: {product['version_ft']} (dernière mise à jour : {formatted_date})")
st.markdown(f"**<div style='text-align: justify; font-size: 1.0rem; color: #333; line-height:1.7rem'>{product['description']}</div>**", unsafe_allow_html=True)


# Helper function to extract groups
def extract_grouped_fields(prefix):
    grouped = {}
    for key in product.index:
        if key.startswith(prefix):
            parts = key.split('_')
            name = parts[1]
            unit = parts[2] if len(parts) > 2 else ''
            grouped[name] = (product[key], unit)
    return grouped

# --- Display by categories ---
def display_category(title, prefix):
    grouped = extract_grouped_fields(prefix)
    if grouped:
        st.markdown(f"#### {title}")
        with st.container(border=True):
            for name, (value, unit) in grouped.items():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{name}**", unsafe_allow_html=True)
                with col2:
                    formatted_unit = unit.replace("cm3", "cm<sup>3</sup>")
                    st.markdown(f"{value} {formatted_unit if unit != 'adim' else ''}", unsafe_allow_html=True)

def display_homologations():
    homologations = []
    show_pmuc_ref = False
    show_bam_details = False

    for key in product.index:
        if key.startswith("homologation_"):
            val = str(product[key]).strip()
            if val and val.lower() != 'nan':
                homologations.append(val)
                if "pmuc" in val.lower():
                    show_pmuc_ref = True
                if "bam" in val.lower():
                    show_bam_details = True

    if homologations:
        st.markdown("#### 🛡️ Homologation(s)")
        with st.container(border=True):
            st.markdown(f'**- {", ".join(homologations)}**')

            if show_pmuc_ref and "pmuc_ref" in product and str(product["pmuc_ref"]).strip():
                st.markdown(f"**Référence PMUC**: {product['pmuc_ref']}")

            if show_bam_details:
                if "bam_ref" in product and str(product["bam_ref"]).strip():
                    st.markdown(f"**Référence BAM**: {product['bam_ref']}")
                if "bam_application" in product and str(product["bam_application"]).strip():
                    st.markdown(f"📄 **Application BAM**: {product['bam_application']}")
                if "bam_tmax_pressionox_1" in product and str(product["bam_tmax_pressionox_1"]).strip():
                    st.markdown(f"🔥 **Conditions BAM (1)**: {product['bam_tmax_pressionox_1']}")
                if "bam_tmax_pressionox_2" in product and str(product.get('bam_tmax_pressionox_2', '')).strip():
                    st.markdown(f"🔥 **Conditions BAM (2)**: {product['bam_tmax_pressionox_2']}")


def display_avantages():
    avantages = []
    for key in product.index:
        if key.startswith("obs_") or key.startswith("observation_"):
            val = str(product[key]).strip()
            if val and val.lower() != 'nan':
                avantages.append(val)

    if avantages:
        with st.container():
            st.markdown("#### 🗨️ Informations complémentaires")
            for phrase in avantages:
                st.markdown(f"- {phrase}")
            st.markdown("""
<hr style='margin-top: 0.5rem; margin-bottom: 0.5rem; text-align: justify;' />
""", unsafe_allow_html=True)

display_category("🔬 Composition moyenne", "composition_")
display_category("📐 Caractéristiques techniques", "caract_")
display_category("⚙️ Paramètres de fonctionnement (non associés)", "param_")
display_homologations()
display_avantages()

dossier_images = os.path.join(dossier_actuel, 'images')

afaq = Image.open(os.path.join(dossier_images, 'afaq.png'))
latty = Image.open(os.path.join(dossier_images, 'latty.jpg'))

with st.container():
    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        st.image(afaq, width=60)
    with col2:
        st.markdown("""
            <div style='text-align: center; font-size: 0.75rem; color: #333; line-height:1.1rem'>
                Les recommandations et limites de stockage avant utilisation sont décrites dans le document référencé
                <strong>AQ SPE 009</strong> disponible sur notre site internet.
            </div>
        """, unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align: center; font-size: 0.85rem; color: #333; line-height:1.1rem'>
                LATTY® International – 1 rue Xavier Latty – 28160 BROU – www.latty.com
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.image(latty, width=60)

def generate_product_html(product):
    def render_section(title, fields):
        html = f"<h3>{title}</h3><ul>"
        for name, value in fields.items():
            html += f"<li><strong>{name}</strong>: {value}</li>"
        html += "</ul>"
        return html

    # Extract grouped fields
    composition = {}
    caracteristiques = {}
    parametres = {}
    avantages = []
    homologations = []
    bam_info = {}
    pmuc_ref = ""

    for key in product.index:
        val = str(product[key]).strip()
        if val.lower() in ["", "nan"]:
            continue
        if key.startswith("composition_"):
            name = key.split("_", 1)[1].replace("_", " ")
            composition[name] = val
        elif key.startswith("caract_"):
            name = key.split("_", 1)[1].replace("_", " ")
            caracteristiques[name] = val
        elif key.startswith("param_"):
            name = key.split("_", 1)[1].replace("_", " ")
            parametres[name] = val
        elif key.startswith("obs_") or key.startswith("observation_"):
            avantages.append(val)
        elif key.startswith("homologation_"):
            homologations.append(val)
            if "bam" in val.lower():
                bam_info = {
                    "Référence BAM": product.get("bam_ref", ""),
                    "Application": product.get("bam_application", ""),
                    "Conditions (1)": product.get("bam_tmax_pressionox_1", ""),
                    "Conditions (2)": product.get("bam_tmax_pressionox_2", ""),
                }
            if "pmuc" in val.lower():
                pmuc_ref = product.get("pmuc_ref", "")
