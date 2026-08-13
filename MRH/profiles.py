import random
from datetime import date, timedelta
from faker import Faker

fake = Faker("fr_FR")

PROFESSIONS = [
    "salarie",
    "retraite",
    "etudiant",
    "salarie_cadre",
    "Fonction_publique_d_etat",
    "Fonction_publique_territoriale",
    "Fonction_publique_hospitaliere",
    "artisan",
    "commercant",
    "profession_liberale",
    "chef_d_entreprise",
    "enseignant",
    "agriculteur",
    "exploitant_agricole",
    "vrp",
    "visiteur_medical",
    "en_recherche_d_emploi",
    "sans_profession",
]

ASSUREURS_HABITATION = [
    "AXA", "Allianz", "Eurofil", "Thelem", "Credit Agricole",
    "Banque Populaire", "Generali", "GMF", "Groupama", "MAAF",
    "Matmut", "MAIF",
    "",  # Aucun de ces assureurs
]

TYPES_CHAUFFAGE = [
    "poele_a_bois",
    "cheminee_sans_insert",
    "cheminee_insert",
]

CHEMINEE_PROFESSIONEL = ["OUI", "NON", "NSP"]

TYPES_PISCINE = [
    "piscine_interieure",
    "piscine_exterieure_couverte",
    "piscine_exterieure_non_couverte",
]

SITUATIONS_MATRIMONIALES = [
    "celibataire", "marie", "divorce", "pacse",
    "en-concubinage", "separe", "veuf",
]

TYPES_HABITATION = ["APPARTEMENT", "MAISON"]

STATUTS_RESIDENT = [
    "LOCATAIRE_COLOCATAIRE",
    "LOCATAIRE_COLOCATAIRE_MEUBLE",
    "PROPRIETAIRE_OCCUPANT",
    "PROPRIETAIRE_NON_OCCUPANT",
]

TYPES_RESIDENCE = ["RESIDENCE_PRINCIPALE", "RESIDENCE_SECONDAIRE"]

ANCIENNETES_LOGEMENT = [
    "MOINS_DE_5_ANS", "ENTRE_5_ET_10_ANS",
    "ENTRE_10_ET_30_ANS", "PLUS_DE_30_ANS",
]

NBR_JOURS_INHABITA = [
    "MOINS_45_JRS", "ENTRE_45_ET_60_JRS",
    "ENTRE_60_ET_90_JRS", "PLUS_DE_90_JRS", "PLUS_DE_180_JRS",
]

ETAGES_APPARTEMENT = ["REZ_DE_CHAUSSEE", "AUTRE_ETG", "DERNIER_ETG"]

# Equipements individuels (format API)
EQUIPEMENTS_POSSIBLES = ["Garage", "antivol", "Veranda", "Annexes", "chauffage", "piscine"]

SURFACES = [20, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 120]

CAPITAUX_MOBILIER = [5000, 8000, 10000, 15000, 20000, 25000, 30000]

CODE_POSTAUX = [
    ("75001", "Paris"),
    ("69100", "Villeurbanne"),
    ("13001", "Marseille"),
    ("31000", "Toulouse"),
    ("33000", "Bordeaux"),
    ("59000", "Lille"),
    ("06000", "Nice"),
    ("67000", "Strasbourg"),
    ("44000", "Nantes"),
    ("34000", "Montpellier"),
]


def random_date(min_age_years: int, max_age_years: int) -> str:
    today = date.today()
    delta = random.randint(min_age_years * 365, max_age_years * 365)
    return (today - timedelta(days=delta)).strftime("%Y-%m-%d")


def random_pieces(surface: int) -> dict:
    s = int(surface)
    if s < 30:
        return {"inferieures_a_30": 1, "entre_30_40": 0, "entre_40_50": 0, "superieures_50": 0}
    elif s < 50:
        return {"inferieures_a_30": 1, "entre_30_40": 1, "entre_40_50": 0, "superieures_50": 0}
    elif s < 70:
        return {"inferieures_a_30": 1, "entre_30_40": 1, "entre_40_50": 1, "superieures_50": 0}
    else:
        nb_sup = (s - 60) // 20
        return {"inferieures_a_30": 1, "entre_30_40": 1, "entre_40_50": 1, "superieures_50": nb_sup}


def _random_equipements() -> tuple[list, str, str, str, str, str]:
    """Tire chaque équipement indépendamment. Retourne (liste, type_chauffage, cheminee_pro, type_piscine, surface_veranda, surface_annexes)."""
    equipements = [e for e in EQUIPEMENTS_POSSIBLES if random.random() < 0.2]
    type_chauffage = random.choice(TYPES_CHAUFFAGE) if "chauffage" in equipements else ""
    cheminee_pro = random.choice(CHEMINEE_PROFESSIONEL) if type_chauffage in ("cheminee_sans_insert", "cheminee_insert") else ""
    type_piscine = random.choice(TYPES_PISCINE) if "piscine" in equipements else ""
    surface_veranda = str(random.randint(5, 30)) if "Veranda" in equipements else ""
    surface_annexes = str(random.randint(5, 50)) if "Annexes" in equipements else ""
    return equipements, type_chauffage, cheminee_pro, type_piscine, surface_veranda, surface_annexes


def generate_profile() -> dict:
    cp, ville = random.choice(CODE_POSTAUX)
    civilite = random.choice(["Monsieur", "Madame"])
    prenom = fake.first_name_male() if civilite == "Monsieur" else fake.first_name_female()
    type_habitation = random.choice(TYPES_HABITATION)
    statut_resident = random.choices(
        STATUTS_RESIDENT,
        weights=[40, 10, 35, 15],
    )[0]
    nb_adultes = random.randint(1, 2)
    nb_enfants = random.randint(0, 3)
    surface = random.choice(SURFACES)
    annee_demenagement = str(random.randint(2010, date.today().year))
    date_debut_contact = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    equipements, type_chauffage, cheminee_pro, type_piscine, surface_veranda, surface_annexes = _random_equipements()

    # Etage : uniquement pour appartement
    etage = random.choice(ETAGES_APPARTEMENT) if type_habitation == "APPARTEMENT" else "AUTRE_ETG"

    enfants = {}
    for i in range(1, 10):
        enfants[f"date_naissance_enfant{i}"] = random_date(0, 18) if i <= nb_enfants else ""

    equip_label = "+".join(equipements) if equipements else "aucun"
    test_label = " | ".join([
        f"statut={statut_resident}",
        f"hab={type_habitation}",
        f"surface={surface}",
        f"equip={equip_label}",
        f"prof={random.choice(PROFESSIONS)}",
    ])

    return {
        "id_forms": 3,
        "type_habitation": type_habitation,
        "etage_appartement": etage,
        "type_residence": random.choice(TYPES_RESIDENCE),
        "fins_professionnelles": "NON",
        "deja_proprietaire_logement": "",
        "logement_proposer_a_location": "",
        "duree_location": "",
        "emmenagement_prevus": "",
        "logement_renovation": "",
        "type_chauffage": type_chauffage,
        "cheminee_professionel": cheminee_pro,
        "type_piscine": type_piscine,
        "anciennete_logement": random.choice(ANCIENNETES_LOGEMENT),
        "surface_habitable": str(surface),
        **random_pieces(surface),
        "equipent_logement": equipements,
        "surface_veranda": surface_veranda,
        "surface_annexes": surface_annexes,
        "nbr_jours_inhabita": random.choice(NBR_JOURS_INHABITA),
        "moyen_de_protection": "NON",
        "moyen_de_protection_detail": [],
        "mean_protection_other": "",
        "statut_resident": statut_resident,
        "logement_cond": "NON" if statut_resident == "PROPRIETAIRE_NON_OCCUPANT" else "OUI",
        "annee_demmenagement": annee_demenagement,
        "nbr_adultes": nb_adultes,
        "nbr_enfants": nb_enfants,
        "capital_mobilier": random.choice(CAPITAUX_MOBILIER),
        "res_3_dernieres_ann": "NON",
        "nbr_sinistres": 0,
        "type_sinistre1": "", "mois_SinDate1": "01", "annee_SinDate1": "",
        "type_sinistre2": "", "mois_SinDate2": "01", "annee_SinDate2": "",
        "type_sinistre3": "", "mois_SinDate3": "01", "annee_SinDate3": "",
        "type_sinistre4": "", "mois_SinDate4": "01", "annee_SinDate4": "",
        "date_sinistre1": "", "date_sinistre2": "", "date_sinistre3": "", "date_sinistre4": "",
        "etat_assureur": (etat_assureur := random.choice(["OUI", "NON", "jamais-assure"])),
        "assureur_habitation": random.choice(ASSUREURS_HABITATION) if etat_assureur == "OUI" else "",
        "date_debut_contact": date_debut_contact,
        "civilite": civilite,
        "nom": fake.last_name(),
        "prenom": prenom,
        "date_naissance": random_date(18, 75),
        **enfants,
        "adresse": fake.street_address(),
        "cp": cp,
        "cp_logment": cp,
        "ville": ville,
        "ville_logment": ville,
        "situation_matrimoniale": random.choice(SITUATIONS_MATRIMONIALES),
        "profession": random.choice(PROFESSIONS),
        "email": fake.email(),
        "telephone": "0" + str(random.randint(600000000, 799999999)),
        "accepte_news": False,
        "accepte_offre": False,
        "provenance": None,
        "_test_label": test_label,
    }


def generate_profiles(n: int) -> list:
    return [generate_profile() for _ in range(n)]


# ---------------------------------------------------------------------------
# Profils déterministes pour diagnostic
# ---------------------------------------------------------------------------

def _base_profile(cp: str = "75001", ville: str = "Paris") -> dict:
    """Profil de référence neutre — toutes les variables à leur valeur par défaut."""
    date_debut_contact = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    enfants = {f"date_naissance_enfant{i}": "" for i in range(1, 10)}
    return {
        "id_forms": 3,
        "type_habitation": "APPARTEMENT",
        "etage_appartement": "AUTRE_ETG",
        "type_residence": "RESIDENCE_PRINCIPALE",
        "fins_professionnelles": "NON",
        "deja_proprietaire_logement": "",
        "logement_proposer_a_location": "",
        "duree_location": "",
        "emmenagement_prevus": "",
        "logement_renovation": "",
        "type_chauffage": "",
        "cheminee_professionel": "",
        "type_piscine": "",
        "anciennete_logement": "ENTRE_5_ET_10_ANS",
        "surface_habitable": "60",
        "inferieures_a_30": 1,
        "entre_30_40": 1,
        "entre_40_50": 1,
        "superieures_50": 0,
        "equipent_logement": [],
        "surface_veranda": "",
        "surface_annexes": "",
        "nbr_jours_inhabita": "MOINS_45_JRS",
        "moyen_de_protection": "NON",
        "moyen_de_protection_detail": [],
        "mean_protection_other": "",
        "statut_resident": "LOCATAIRE_COLOCATAIRE",
        "logement_cond": "OUI",
        "annee_demmenagement": "2020",
        "nbr_adultes": 1,
        "nbr_enfants": 0,
        "capital_mobilier": 15000,
        "res_3_dernieres_ann": "NON",
        "nbr_sinistres": 0,
        "type_sinistre1": "", "mois_SinDate1": "01", "annee_SinDate1": "",
        "type_sinistre2": "", "mois_SinDate2": "01", "annee_SinDate2": "",
        "type_sinistre3": "", "mois_SinDate3": "01", "annee_SinDate3": "",
        "type_sinistre4": "", "mois_SinDate4": "01", "annee_SinDate4": "",
        "date_sinistre1": "", "date_sinistre2": "", "date_sinistre3": "", "date_sinistre4": "",
        "etat_assureur": "NON",
        "assureur_habitation": "",
        "date_debut_contact": date_debut_contact,
        "civilite": "Monsieur",
        "nom": "Dupont",
        "prenom": "Jean",
        "date_naissance": "1985-06-15",
        **enfants,
        "adresse": "12 rue de la Paix",
        "cp": cp,
        "cp_logment": cp,
        "ville": ville,
        "ville_logment": ville,
        "situation_matrimoniale": "celibataire",
        "profession": "salarie",
        "email": "jean.dupont@test.fr",
        "telephone": "0612345678",
        "accepte_news": False,
        "accepte_offre": False,
        "provenance": None,
    }


def _label(base: dict, **overrides) -> dict:
    p = {**base, **overrides}
    p["_test_label"] = " | ".join(f"{k}={v}" for k, v in overrides.items())
    return p


def generate_deterministic_profiles() -> list[dict]:
    """
    Génère une suite de profils déterministes pour diagnostiquer le site.
    Chaque série isole une variable par rapport au profil de base neutre.
    """
    profiles = []
    base = _base_profile()

    # --- 1. statut_resident ---
    for statut in STATUTS_RESIDENT:
        profiles.append(_label(base,
            statut_resident=statut,
            logement_cond="NON" if statut == "PROPRIETAIRE_NON_OCCUPANT" else "OUI",
        ))

    # --- 2. type_habitation ---
    for hab in TYPES_HABITATION:
        overrides = {"type_habitation": hab}
        if hab == "MAISON":
            overrides["etage_appartement"] = "AUTRE_ETG"
        profiles.append(_label(base, **overrides))

    # --- 3. etage_appartement (APPARTEMENT uniquement) ---
    for etage in ETAGES_APPARTEMENT:
        profiles.append(_label(base, etage_appartement=etage))

    # --- 4. type_residence ---
    for res in TYPES_RESIDENCE:
        profiles.append(_label(base, type_residence=res))

    # --- 5. type_residence + statut PNO (combinaison utile) ---
    profiles.append(_label(base,
        type_residence="RESIDENCE_SECONDAIRE",
        statut_resident="PROPRIETAIRE_NON_OCCUPANT",
        logement_cond="NON",
    ))

    # --- 6. anciennete_logement ---
    for anc in ANCIENNETES_LOGEMENT:
        profiles.append(_label(base, anciennete_logement=anc))

    # --- 7. nbr_jours_inhabita ---
    for jours in NBR_JOURS_INHABITA:
        profiles.append(_label(base, nbr_jours_inhabita=jours))

    # --- 8. surface_habitable (seuils clés + extrêmes) ---
    for surface in SURFACES:
        pieces = random_pieces(surface)
        profiles.append(_label(base, surface_habitable=str(surface), **pieces))

    # --- 9. capital_mobilier ---
    for cap in CAPITAUX_MOBILIER:
        profiles.append(_label(base, capital_mobilier=cap))

    # --- 10. equipements : chaque équipement seul ---
    for equip in EQUIPEMENTS_POSSIBLES:
        overrides: dict = {"equipent_logement": [equip]}
        if equip == "chauffage":
            overrides["type_chauffage"] = "poele_a_bois"
        if equip == "piscine":
            overrides["type_piscine"] = "piscine_exterieure_non_couverte"
        if equip == "Veranda":
            overrides["surface_veranda"] = "15"
        if equip == "Annexes":
            overrides["surface_annexes"] = "20"
        profiles.append(_label(base, **overrides))

    # --- 11. equipements : toutes combinaisons avec chauffage ---
    for tc in TYPES_CHAUFFAGE:
        overrides = {"equipent_logement": ["chauffage"], "type_chauffage": tc}
        if tc in ("cheminee_sans_insert", "cheminee_insert"):
            for cp_val in CHEMINEE_PROFESSIONEL:
                profiles.append(_label(base, **overrides, cheminee_professionel=cp_val))
        else:
            profiles.append(_label(base, **overrides))

    # --- 12. type_piscine ---
    for tp in TYPES_PISCINE:
        profiles.append(_label(base, equipent_logement=["piscine"], type_piscine=tp))

    # --- 13. etat_assureur + assureur_habitation ---
    for etat in ["OUI", "NON", "jamais-assure"]:
        if etat == "OUI":
            for assureur in ASSUREURS_HABITATION:
                profiles.append(_label(base, etat_assureur=etat, assureur_habitation=assureur))
        else:
            profiles.append(_label(base, etat_assureur=etat, assureur_habitation=""))

    # --- 14. profession ---
    for prof in PROFESSIONS:
        profiles.append(_label(base, profession=prof))

    # --- 15. situation_matrimoniale ---
    for sit in SITUATIONS_MATRIMONIALES:
        profiles.append(_label(base, situation_matrimoniale=sit))

    # --- 16. âge (seuils critiques) ---
    for age in [18, 25, 35, 50, 60, 65, 75]:
        ddn = (date.today() - timedelta(days=age * 365)).strftime("%Y-%m-%d")
        profiles.append(_label(base, date_naissance=ddn))

    # --- 17. géographie ---
    for cp, ville in CODE_POSTAUX:
        b = _base_profile(cp=cp, ville=ville)
        profiles.append(_label(b, cp=cp, ville=ville))

    # --- 18. nb_adultes / nb_enfants ---
    for nb_a in [1, 2]:
        profiles.append(_label(base, nbr_adultes=nb_a))
    for nb_e in [0, 1, 2, 3]:
        enfants = {f"date_naissance_enfant{i}": ("2015-01-01" if i <= nb_e else "") for i in range(1, 10)}
        profiles.append(_label(base, nbr_enfants=nb_e, **enfants))

    return profiles
