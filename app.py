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
# DÉFICIT UNIQUE (RECALCUL GLOBAL)
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

# =========================
# 🗑️ SUPPRESSION SÉCURISÉE
# =========================
st.header("🗑️ Supprimer un enregistrement (sécurisé)")

if len(df) > 0:
    del_date = st.selectbox(
        "Choisir la date à supprimer",
        df["date"].unique().tolist()
    )

    indices = df.index[df["date"] == del_date].tolist()

    if len(indices) == 1:
        idx_to_delete = indices[0]

        st.warning(f"⚠️ Tu vas supprimer la journée du **{del_date}**")
        confirm = st.checkbox("✅ Je confirme la suppression")

        if confirm and st.button("❌ Supprimer définitivement"):
            df = df.drop(index=idx_to_delete).reset_index(drop=True)
            df["deficit_colis"] = recalcul_deficit(df)
            df.to_csv(file_month, index=False)
            st.success("✅ Journée supprimée sans toucher aux autres")
            st.rerun()

    else:
        st.error(
            "❌ Plusieurs lignes ont la même date.\n"
            "Suppression bloquée pour éviter une perte de données."
        )
else:
    st.info("Aucun enregistrement à supprimer")

# =========================
# SAISIE / MODIFICATION
# =========================
st.header("📝 Saisie / Modification du jour")

edit_mode = st.checkbox("✏️ Modifier une journée existante")

if edit_mode and len(df) > 0:
    selected_date = st.selectbox(
        "Choisir la date",
        df["date"].tolist()
    )
    row = df[df["date"] == selected_date].iloc[0]
else:
    selected_date = today.isoformat()
    row = None

def val(col):
    return int(row[col]) if row is not None else 0

commandes_passees = st.number_input(
    "🛒 Commandes passées", min_value=0, value=val("commandes_passees")
)
commandes_livrees = st.number_input(
    "📦 Commandes livrées", min_value=0, value=val("commandes_livrees")
)
chiffre_affaire = st.number_input(
    "💰 Chiffre d'affaires (FCFA)", min_value=0, value=val("chiffre_affaire")
)
charges = st.number_input(
    "🧾 Charges (FCFA)", min_value=0, value=val("charges")
)
pub = st.number_input(
    "📢 Publicité (FCFA)", min_value=0, value=val("pub")
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
        "objectif_colis": objectif,
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

deficit_officiel = recalcul_deficit(df)

st.metric("🛒 Commandes passées", commandes_passees)
st.metric("📦 Commandes livrées", commandes_livrees)
st.metric("❌ Commandes perdues", commandes_perdues)
st.metric("📈 Taux de livraison", f"{taux_livr} %")
st.metric("💵 Bénéfice net", f"{fmt(benefice)} {MONNAIE}")
st.metric("📊 Taux bénéfice / CA", f"{taux_benef} %")

if deficit_officiel > 0:
    st.error(f"🔴 Déficit cumulatif réel : {deficit_officiel} colis")
else:
    st.success("🟢 Aucun déficit")

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
        f"📦 Pour atteindre l’objectif, vise **{colis_jour} colis par jour** "
        f"sur les **{jours_restants} jours restants**."
    )
else:
    st.success("🔥 OBJECTIF MENSUEL ATTEINT !")

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
    st.metric("🚨 Déficit final", deficit_officiel)
    st.dataframe(df)
else:
    st.info("Aucune donnée ce mois-ci")
