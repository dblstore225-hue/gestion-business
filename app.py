# app.py
import streamlit as st
import pandas as pd
from datetime import date
import os
import shutil
from logic import (
    calcul_benefice_net,
    taux_rentabilite,
    taux_livraison,
    objectif_colis_jour
)
from config import MONNAIE, BENEFICE_PAR_COLIS

# =========================
# FORMAT MONTANTS LISIBLES
# =========================
def fmt(val):
    try:
        return f"{int(val):,}".replace(",", ".")
    except:
        return "0"

# =========================
# SAUVEGARDE AUTOMATIQUE CSV
# =========================
def backup_csv(path):
    if os.path.exists(path):
        shutil.copy(path, path.replace(".csv", "_backup.csv"))

# =========================
# DÉFICIT CUMULATIF (COLIS)
# =========================
def recalcul_deficit(df):
    deficit = 0
    for _, row in df.iterrows():
        deficit += 4 - int(row["commandes_livrees"])
        deficit = max(deficit, 0)
    return int(deficit)

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(page_title="Gestion Business", layout="centered")
st.title("📊 Gestion Business – Tableau de Bord")

today = date.today()
file_month = f"data/{today.year}_{today.month:02}.csv"

COLUMNS = [
    "date","commandes_passees","commandes_livrees","commandes_perdues",
    "taux_livraison","chiffre_affaire","charges","pub","pub_reelle",
    "benefice_net","taux_benefice","objectif_colis","deficit_colis"
]

# =========================
# 🔄 RESTAURATION CSV
# =========================
st.header("🔄 Restaurer des données existantes")

uploaded = st.file_uploader(
    "Importer un ancien fichier CSV (sauvegarde)",
    type=["csv"]
)

if uploaded is not None:
    df = pd.read_csv(uploaded)

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = 0

    df = df[COLUMNS]
    df["date"] = df["date"].astype(str)
    df["objectif_colis"] = df["objectif_colis"].apply(lambda x: max(int(x), 4))
    df["deficit_colis"] = recalcul_deficit(df)

    st.success("✅ Données restaurées avec succès")
else:
    try:
        df = pd.read_csv(file_month)
    except FileNotFoundError:
        df = pd.DataFrame(columns=COLUMNS)

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = 0

    df = df[COLUMNS]
    df["date"] = df["date"].astype(str)
    df["objectif_colis"] = df["objectif_colis"].apply(lambda x: max(int(x), 4))

# =========================
# 📥 TÉLÉCHARGEMENT SÉCURITÉ
# =========================
st.download_button(
    "💾 Télécharger les données (sécurité)",
    data=df.to_csv(index=False),
    file_name=file_month,
    mime="text/csv"
)

# =========================
# SAISIE
# =========================
st.header("📝 Saisie d’une journée")

selected_date = st.date_input("📅 Date", value=today).isoformat()

commandes_passees = st.number_input("🛒 Commandes passées", 0)
commandes_livrees = st.number_input("📦 Commandes livrées", 0)
chiffre_affaire = st.number_input("💰 Chiffre d'affaires", 0)
charges = st.number_input("🧾 Charges", 0)
pub = st.number_input("📢 Publicité", 0)

benefice, pub_reelle = calcul_benefice_net(chiffre_affaire, charges, pub)
taux_benef = taux_rentabilite(benefice, chiffre_affaire)
taux_livr = taux_livraison(commandes_livrees, commandes_passees)
commandes_perdues = max(commandes_passees - commandes_livrees, 0)
objectif = objectif_colis_jour(pub_reelle)

if st.button("💾 Enregistrer la journée"):
    ligne = {
        "date": selected_date,
        "commandes_passees": commandes_passees,
        "commandes_livrees": commandes_livrees,
        "commandes_perdues": commandes_perdues,
        "taux_livraison": taux_livr,
        "chiffre_affaire": chiffre_affaire,
        "charges": charges,
        "pub": pub,
        "pub_reelle": pub_reelle,
        "benefice_net": benefice,
        "taux_benefice": taux_benef,
        "objectif_colis": objectif,
        "deficit_colis": 0
    }

    df = pd.concat([df, pd.DataFrame([ligne])], ignore_index=True)
    df["deficit_colis"] = recalcul_deficit(df)

    backup_csv(file_month)
    df.to_csv(file_month, index=False)

    st.success("✅ Journée enregistrée")

# =========================
# 📊 VUE GLOBALE
# =========================
st.header("📆 Vue globale")

st.metric("📦 Colis livrés", int(df["commandes_livrees"].sum()))
st.metric("💵 Bénéfice total", f"{fmt(df['benefice_net'].sum())} {MONNAIE}")
st.metric("🚨 Déficit", recalcul_deficit(df))

st.dataframe(df)
