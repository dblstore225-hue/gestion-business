# app.py
import streamlit as st
import pandas as pd
from datetime import date
from logic import (
    calcul_benefice_net,
    taux_rentabilite,
    taux_livraison,
    objectif_colis_jour,
    calcul_deficit_mensuel
)
from config import MONNAIE, BENEFICE_PAR_COLIS

# =========================
# FORMAT MONTANT LISIBLE
# =========================
def fmt(val):
    try:
        return f"{int(val):,}".replace(",", ".")
    except:
        return "0"

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

# =========================
# 🗑️ SUPPRESSION D’UN JOUR (TEST / ERREUR)
# =========================
st.header("🗑️ Supprimer un enregistrement")

if len(df) > 0:
    del_date = st.selectbox(
        "Choisir la date à supprimer",
        df["date"].astype(str).tolist()
    )

    if st.button("❌ Supprimer cette journée"):
        df = df[df["date"].astype(str) != del_date].reset_index(drop=True)
        df["deficit_colis"] = calcul_deficit_mensuel(df)
        df.to_csv(file_month, index=False)
        st.success("✅ Journée supprimée")
        st.rerun()
else:
    st.info("Aucune donnée à supprimer")

# =========================
# SAISIE / MODIFICATION
# =========================
st.header("📝 Saisie / Modification du jour")

edit_mode = st.checkbox("✏️ Modifier une journée existante")

if edit_mode and len(df) > 0:
    selected_date = st.selectbox(
        "Choisir la date",
        df["date"].astype(str).tolist()
    )
    row = df[df["date"].astype(str) == selected_date].iloc[0]
else:
    selected_date = today.isoformat()
    row = None

def val(col):
    return int(row[col]) if row is not None else 0

commandes_passees = st.number_input(
    "🛒 Commandes passées",
    min_value=0,
    value=val("commandes_passees")
)
commandes_livrees = st.number_input(
    "📦 Commandes livrées",
    min_value=0,
    value=val("commandes_livrees")
)
chiffre_affaire = st.number_input(
    "💰 Chiffre d'affaires (FCFA)",
    min_value=0,
    value=val("chiffre_affaire")
)
charges = st.number_input(
    "🧾 Charges (FCFA)",
    min_value=0,
    value=val("charges")
)
pub = st.number_input(
    "📢 Publicité (FCFA)",
    min_value=0,
    value=val("pub")
)

# =========================
# CALCULS
# =========================
benefice, pub_reelle = calcul_benefice_net(chiffre_affaire, charges, pub)
taux_benef = taux_rentabilite(benefice, chiffre_affaire)
taux_livr = taux_livraison(commandes_livrees, commandes_passees)
commandes_perdues = max(commandes_passees - commandes_livrees, 0)
objectif = objectif_colis_jour(pub_reelle)

# =========================
# ENREGISTREMENT
# =========================
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

    if edit_mode:
        idx = df.index[df["date"].astype(str) == selected_date][0]
        df.loc[idx] = ligne
    else:
        df = pd.concat([df, pd.DataFrame([ligne])], ignore_index=True)

    # 🔒 recalcul UNIQUE du déficit mensuel
    df["deficit_colis"] = calcul_deficit_mensuel(df)

    df.to_csv(file_month, index=False)
    st.success("✅ Journée enregistrée")

# =========================
# DÉFICIT OFFICIEL UNIQUE
# =========================
deficit_officiel = calcul_deficit_mensuel(df)

# =========================
# RÉSUMÉ DU JOUR
# =========================
st.header("📌 Résumé du jour")

st.metric("💵 Bénéfice net", f"{fmt(benefice)} {MONNAIE}")
st.metric("📦 Déficit mensuel officiel", deficit_officiel)

# =========================
# 🧠 ANALYSE & RECOMMANDATIONS
# =========================
st.header("🧠 Analyse & recommandations")

if deficit_officiel > 0:
    st.error(
        f"🔴 DÉFICIT RÉEL : {deficit_officiel} colis.\n\n"
        "👉 Priorité : livrer les commandes en attente.\n"
        "👉 Réduire la publicité tant que le déficit n’est pas comblé."
    )
else:
    st.success(
        "🟢 Aucun déficit.\n\n"
        "👉 Situation saine, tu peux te concentrer sur la croissance."
    )

# =========================
# 🎯 OBJECTIF MENSUEL
# =========================
st.header("🎯 Objectif mensuel – 1 000 000 FCFA")

OBJECTIF_MENSUEL = 1_000_000
benefice_mensuel = int(df["benefice_net"].sum())
reste = OBJECTIF_MENSUEL - benefice_mensuel
jours_restants = max(30 - today.day, 1)

st.metric("💰 Bénéfice actuel", f"{fmt(benefice_mensuel)} {MONNAIE}")
st.metric("🎯 Objectif", f"{fmt(OBJECTIF_MENSUEL)} {MONNAIE}")
st.metric("⏳ Reste à atteindre", f"{fmt(max(reste, 0))} {MONNAIE}")

if reste > 0:
    colis_jour = int((reste / (BENEFICE_PAR_COLIS * jours_restants)) + 1)
    st.info(
        f"📦 Pour atteindre l’objectif, vise **{colis_jour} colis livrés par jour** "
        f"sur les **{jours_restants} jours restants**."
    )
else:
    st.success("🔥 OBJECTIF MENSUEL ATTEINT")

# =========================
# 📆 VUE MENSUELLE
# =========================
st.header("📆 Vue mensuelle")

if len(df) > 0:
    st.metric("🛒 Commandes passées", int(df["commandes_passees"].sum()))
    st.metric("📦 Commandes livrées", int(df["commandes_livrees"].sum()))
    st.metric("❌ Commandes perdues", int(df["commandes_perdues"].sum()))
    st.metric("💰 CA total", f"{fmt(df['chiffre_affaire'].sum())} {MONNAIE}")
    st.metric("💵 Bénéfice net total", f"{fmt(df['benefice_net'].sum())} {MONNAIE}")
    st.metric("📦 Déficit final", deficit_officiel)
    st.dataframe(df)
else:
    st.info("Aucune donnée ce mois-ci")
