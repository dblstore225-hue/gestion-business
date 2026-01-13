# app.py
import streamlit as st
import pandas as pd
from datetime import date
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
# DÉFICIT UNIQUE (CUMULATIF)
# =========================
def recalcul_deficit(df):
    deficit = 0
    for _, row in df.iterrows():
        deficit += row["objectif_colis"] - row["commandes_livrees"]
        deficit = max(deficit, 0)
    return int(deficit)

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(page_title="Gestion Business", layout="centered")
st.title("📊 Gestion Business – Tableau de Bord")

# =========================
# FICHIER DU MOIS
# =========================
today = date.today()
file_month = f"data/{today.year}_{today.month:02}.csv"

COLUMNS = [
    "date",
    "commandes_passees",
    "commandes_livrees",
    "commandes_perdues",
    "taux_livraison",
    "chiffre_affaire",
    "charges",
    "pub",
    "pub_reelle",
    "benefice_net",
    "taux_benefice",
    "objectif_colis",
    "deficit_colis"
]

# =========================
# CHARGEMENT SÉCURISÉ
# =========================
try:
    df = pd.read_csv(file_month)
except FileNotFoundError:
    df = pd.DataFrame(columns=COLUMNS)

for col in COLUMNS:
    if col not in df.columns:
        df[col] = 0

df = df[COLUMNS]
df["date"] = df["date"].astype(str)

# 🔒 CORRECTION AUTOMATIQUE DES OBJECTIFS CORROMPUS
df["objectif_colis"] = df["objectif_colis"].apply(
    lambda x: max(int(x), 4)
)

# =========================
# 🗑️ SUPPRESSION SÉCURISÉE
# =========================
st.header("🗑️ Supprimer un enregistrement")

if len(df) > 0:
    del_date = st.selectbox(
        "Choisir la date à supprimer",
        df["date"].unique().tolist()
    )

    indices = df.index[df["date"] == del_date].tolist()

    if len(indices) == 1:
        idx = indices[0]
        st.warning(f"⚠️ Suppression de la journée {del_date}")
        confirm = st.checkbox("Je confirme la suppression")

        if confirm and st.button("❌ Supprimer définitivement"):
            df = df.drop(index=idx).reset_index(drop=True)
            df["deficit_colis"] = recalcul_deficit(df)
            df.to_csv(file_month, index=False)
            st.success("✅ Journée supprimée")
            st.rerun()
else:
    st.info("Aucune donnée à supprimer")

# =========================
# SAISIE / MODIFICATION
# =========================
st.header("📝 Saisie / Modification")

edit_mode = st.checkbox("✏️ Modifier une journée existante")

if edit_mode and len(df) > 0:
    selected_date = st.selectbox("Choisir la date", df["date"].tolist())
    row = df[df["date"] == selected_date].iloc[0]
else:
    selected_date = today.isoformat()
    row = None

def val(col):
    return int(row[col]) if row is not None else 0

commandes_passees = st.number_input("🛒 Commandes passées", 0, value=val("commandes_passees"))
commandes_livrees = st.number_input("📦 Commandes livrées", 0, value=val("commandes_livrees"))
chiffre_affaire = st.number_input("💰 Chiffre d'affaires", 0, value=val("chiffre_affaire"))
charges = st.number_input("🧾 Charges", 0, value=val("charges"))
pub = st.number_input("📢 Publicité", 0, value=val("pub"))

# =========================
# CALCULS (OBJECTIF FORCÉ)
# =========================
benefice, pub_reelle = calcul_benefice_net(chiffre_affaire, charges, pub)

# 🔐 OBJECTIF TOUJOURS RECALCULÉ
objectif = objectif_colis_jour(pub_reelle)

taux_benef = taux_rentabilite(benefice, chiffre_affaire)
taux_livr = taux_livraison(commandes_livrees, commandes_passees)
commandes_perdues = max(commandes_passees - commandes_livrees, 0)
deficit_jour = max(objectif - commandes_livrees, 0)

# =========================
# ENREGISTREMENT
# =========================
if st.button("💾 Enregistrer la journée"):
    if not edit_mode and selected_date in df["date"].values:
        st.error("❌ Cette date existe déjà. Active le mode modification.")
        st.stop()

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
        "objectif_colis": objectif,   # 🔐 jamais hérité
        "deficit_colis": 0
    }

    if edit_mode:
        idx = df.index[df["date"] == selected_date][0]
        df.loc[idx] = ligne
    else:
        df = pd.concat([df, pd.DataFrame([ligne])], ignore_index=True)

    df["deficit_colis"] = recalcul_deficit(df)
    df.to_csv(file_month, index=False)
    st.success("✅ Journée enregistrée")

# =========================
# RÉSUMÉ DU JOUR
# =========================
st.header("📌 Résumé du jour")

st.metric("🎯 Objectif colis", objectif)
st.metric("📦 Colis livrés", commandes_livrees)
st.metric("🚨 Déficit du jour", deficit_jour)
st.metric("💵 Bénéfice net", f"{fmt(benefice)} {MONNAIE}")
st.metric("📈 Taux de livraison", f"{taux_livr} %")

# =========================
# VUE MENSUELLE
# =========================
st.header("📆 Vue mensuelle")

if len(df) > 0:
    st.metric("📦 Total livrés", int(df["commandes_livrees"].sum()))
    st.metric("💰 Bénéfice total", f"{fmt(df['benefice_net'].sum())} {MONNAIE}")
    st.metric("🚨 Déficit cumulatif", recalcul_deficit(df))
    st.dataframe(df)
else:
    st.info("Aucune donnée ce mois-ci")
