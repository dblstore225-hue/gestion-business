# logic.py
from config import TAXE_PUB, BENEFICE_PAR_COLIS

def calcul_pub_reelle(pub):
    return pub * (1 + TAXE_PUB)

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

def objectif_colis_jour(pub_reelle):
    if BENEFICE_PAR_COLIS == 0:
        return 0
    return int((pub_reelle / BENEFICE_PAR_COLIS) + 1)

def calcul_deficit(deficit_precedent, objectif, livres):
    deficit = deficit_precedent + objectif - livres
    return max(deficit, 0)
