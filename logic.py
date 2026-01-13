# logic.py
from config import TAXE_PUB

# =========================
# CALCULS DE BASE
# =========================
def calcul_pub_reelle(pub):
    return int(pub * (1 + TAXE_PUB))

def calcul_benefice_net(ca, charges, pub):
    pub_reelle = calcul_pub_reelle(pub)
    benefice = ca - charges - pub_reelle
    return int(benefice), int(pub_reelle)

def taux_rentabilite(benefice, ca):
    if ca == 0:
        return 0
    return round((benefice / ca) * 100, 2)

def taux_livraison(livrees, passees):
    if passees == 0:
        return 0
    return round((livrees / passees) * 100, 2)

# =========================
# OBJECTIF COLIS (BASÉ SUR PUB)
# =========================
def objectif_colis_jour(pub_reelle):
    if pub_reelle <= 0:
        return 4
    objectif = (pub_reelle / 6850) * 4
    return max(4, int(objectif + 0.999))

# =========================
# DÉFICIT MENSUEL UNIQUE
# =========================
def calcul_deficit_mensuel(df):
    """
    Recalcule le déficit mensuel OFFICIEL
    à partir de TOUT l'historique enregistré.
    """
    deficit = 0
    for _, row in df.iterrows():
        deficit += row["objectif_colis"] - row["commandes_livrees"]
        deficit = max(deficit, 0)
    return int(deficit)
