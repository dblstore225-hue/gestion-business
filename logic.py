# logic.py
from config import TAXE_PUB, BENEFICE_PAR_COLIS

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
# NOUVEL OBJECTIF COLIS (BASÉ SUR PUB)
# =========================
def objectif_colis_jour(pub_reelle):
    """
    - Objectif minimum : 4 colis
    - Référence : 6 850 FCFA ≈ 4 colis
    - Plus de pub = plus de colis requis
    """
    if pub_reelle <= 0:
        return 4

    objectif = (pub_reelle / 6850) * 4
    return max(4, int(objectif + 0.999))

# =========================
# DÉFICIT CUMULATIF
# =========================
def calcul_deficit(deficit_precedent, objectif, livres):
    deficit = deficit_precedent + objectif - livres
    return max(deficit, 0)
