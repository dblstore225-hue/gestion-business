# app.py
import streamlit as st
import pandas as pd
from datetime import date
from logic import (
    calcul_benefice_net,
    taux_rentabilite,
    taux_livraison,
    objectif_colis_jour,
    calcul_deficit
)
from config import MONNAIE, BENEFICE_PAR_COLIS

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
deficit_precedent = int(df.iloc[-1]["deficit_colis"]) if len(df) > 0 else 0

# =========================
# SAISIE / MODIFICATION
# =========================
st.header("📝 Saisie / Modification du jour")

edit_mode = st.checkbox("✏️ Modifier une journée existante")

if edit_mode and len(df) > 0:
    selected_date = st.selectbox("Choisir la date", df["date"].astype(str).tolist())
    row = df[df["date"].astype(str) == selected_date].iloc[0]
else:
    selected_date = today.isoformat()
    row = None

def val(col):
    return int(row[col]) if row is not None else 0

commandes_passees = st.number_input("🛒 Commandes passées", min_value=0, value=val("commandes_passees"))
commandes_livrees = st.number_input("📦 Commandes livrées", min_value=0, value=val("commandes_livrees"))
chiffre_affaire = st.number_input("💰 Chiffre d'affaires (FCFA)", min_value=0, value=val("chiffre_affaire"))
charges = st.number_input("🧾 Charges (FCFA)", min_value=0, value=val("charges"))
pub = st.number_input("📢 Publicité (FCFA)", min_value=0, value=val("pub"))

# =========================
# CALCULS TEMPS RÉEL
# =========================
benefice, pub_reelle = calcul_benefice_net(chiffre_affaire, charges, pub)
taux_benef = taux_rentabilite(benefice, chiffre_affaire)
taux_livr = taux_livraison(commandes_livrees, commandes_passees)
commandes_perdues = max(commandes_passees - commandes_livrees, 0)
objectif = objectif_colis_jour(pub_reelle)
deficit_estime = calcul_deficit(deficit_precedent, objectif, commandes_livrees)

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
        "deficit_colis": deficit_estime
    }

    if edit_mode:
        idx = df.index[df["date"].astype(str) == selected_date][0]
        df.loc[idx] = ligne
    else:
        df = pd.concat([df, pd.DataFrame([ligne])], ignore_index=True)

    df.to_csv(file_month, index=False)
    st.success("✅ Journée enregistrée sans erreur")

# =========================
# RÉSUMÉ DU JOUR
# =========================
st.header("📌 Résumé du jour")

st.metric("🛒 Commandes passées", commandes_passees)
st.metric("📦 Commandes livrées", commandes_livrees)
st.metric("❌ Commandes perdues", commandes_perdues)
st.metric("📈 Taux de livraison", f"{taux_livr} %")
st.metric("💵 Bénéfice net", f"{benefice} {MONNAIE}")
st.metric("📊 Taux bénéfice / CA", f"{taux_benef} %")

if deficit_estime > 0:
    st.error(f"🔴 Déficit cumulatif estimé : {deficit_estime} colis")
else:
    st.success("🟢 Aucun déficit estimé")

# =========================
# 🧠 ANALYSE & RECOMMANDATIONS
# =========================
st.header("🧠 Analyse & recommandations")

if benefice < 0:
    manque = abs(benefice)
    colis = int((manque / BENEFICE_PAR_COLIS) + 1)
    st.error(
        f"🔴 TU ES EN PERTE.\n\n"
        f"➡️ Objectif minimum : **{colis} colis supplémentaires**\n"
        f"➡️ Ou viser **+{manque} {MONNAIE} de chiffre d’affaires**\n\n"
        f"⚠️ Tant que cet objectif n’est pas atteint, tu détruis ta trésorerie."
    )

elif deficit_estime > 0:
    st.warning(
        f"🟠 TU ES DANS LE VERT MAIS LE MOIS RESTE FRAGILE.\n\n"
        f"Il reste **{deficit_estime} colis à rattraper** pour sécuriser ton mois.\n"
        f"👉 Priorité : rattraper ce déficit avant toute augmentation de dépenses."
    )

elif benefice < pub_reelle:
    st.info(
        "🟡 SITUATION STABLE MAIS À RISQUE.\n\n"
        "Un retard livreur ou une annulation peut te faire replonger.\n"
        "👉 Essaie de livrer **1 à 2 colis supplémentaires** pour sécuriser la journée."
    )

elif benefice >= 2 * pub_reelle:
    st.success(
        "🔥 EXCELLENTE PERFORMANCE.\n\n"
        "Tu es très rentable aujourd’hui.\n"
        "👉 Options intelligentes :\n"
        "- augmenter la publicité\n"
        "- ou sécuriser plusieurs jours d’avance."
    )

else:
    st.success(
        "🟢 BONNE GESTION.\n\n"
        "Tu es rentable et stable.\n"
        "👉 Continue à ce rythme pour éviter un retour dans le rouge."
    )

# =========================
# VUE MENSUELLE
# =========================
st.header("📆 Vue mensuelle")

if len(df) > 0:
    st.metric("🛒 Commandes passées (mois)", int(df["commandes_passees"].sum()))
    st.metric("📦 Commandes livrées (mois)", int(df["commandes_livrees"].sum()))
    st.metric("❌ Commandes perdues (mois)", int(df["commandes_perdues"].sum()))
    st.metric("💰 CA total", int(df["chiffre_affaire"].sum()))
    st.metric("💵 Bénéfice net total", int(df["benefice_net"].sum()))
    st.metric(
        "📊 Taux bénéfice global",
        taux_rentabilite(df["benefice_net"].sum(), df["chiffre_affaire"].sum())
    )
    st.metric("🚨 Déficit final", int(df.iloc[-1]["deficit_colis"]))
    st.dataframe(df)
else:
    st.info("Aucune donnée ce mois-ci")
