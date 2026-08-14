import random
from datetime import date, timedelta
from faker import Faker

fake = Faker("fr_FR")

NIVEAUX_GARANTIE = ["Faible", "Moyen", "Fort", "Max"]

REGIMES = [
    "REGIME_GENERAL",
    "TNS",
    "SALARIE_AGRICOLE",
    "ALSACE_MOSELLE",
]

# (profession, autre_profession)
# profession = catégorie principale (bouton radio)
# autre_profession = sous-catégorie (select)
PROFESSIONS = [
    ("salarie", "salarie_cadre"),
    ("salarie", "Fonction_publique_d_etat"),
    ("salarie", "Fonction_publique_territoriale"),
    ("salarie", "Fonction_publique_hospitalière"),
    ("salarie", "artisan"),
    ("salarie", "commercant"),
    ("salarie", "profession_liberale"),
    ("salarie", "chef_d_entreprise"),
    ("salarie", "enseignant"),
    ("salarie", "agriculteur"),
    ("salarie", "exploitant_agricole"),
    ("salarie", "VRP"),
    ("salarie", "visiteur_medical"),
    ("salarie", "sans_profession"),
    ("etudiant", "etudiant"),
    ("retraite", "retraite"),
    ("en_recherche_d_emploi", "en_recherche_d_emploi"),
]

# who_assure → détermine conjoint + enfants
# ADULT=moi seul, COUPLE=mon couple, ADULT_KIDS=moi+enfants, COUPLE_KIDS=couple+enfants
WHO_ASSURE = ["ADULT", "COUPLE", "ADULT_KIDS", "COUPLE_KIDS"]

MODES_SOINS = ["1", "2", "3", "4"]  # 1=SS, 2=SS+médecin traitant, 3=libre, 4=personnalisé

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
    ("35000", "Rennes"),
    ("38000", "Grenoble"),
    ("21000", "Dijon"),
    ("49000", "Angers"),
    ("51100", "Reims"),
    ("42000", "Saint-Etienne"),
    ("57000", "Metz"),
    ("14000", "Caen"),
    ("20000", "Ajaccio"),
    ("97400", "Saint-Denis (La Reunion)"),
    # --- Ajouts : couverture departementale elargie ---
    ("02100", "Saint-Quentin"),          # Aisne
    ("03000", "Moulins"),                # Allier
    ("05000", "Gap"),                    # Hautes-Alpes
    ("07100", "Annonay"),                # Ardeche
    ("10000", "Troyes"),                 # Aube
    ("15000", "Aurillac"),               # Cantal
    ("17000", "La Rochelle"),            # Charente-Maritime
    ("19000", "Tulle"),                  # Correze
    ("22000", "Saint-Brieuc"),           # Cotes-d'Armor
    ("24000", "Perigueux"),              # Dordogne
    ("25000", "Besancon"),               # Doubs
    ("29200", "Brest"),                  # Finistere
    ("30000", "Nimes"),                  # Gard
    ("37000", "Tours"),                  # Indre-et-Loire
    ("40000", "Mont-de-Marsan"),         # Landes
    ("45000", "Orleans"),                # Loiret
    ("54000", "Nancy"),                  # Meurthe-et-Moselle
    ("56000", "Vannes"),                 # Morbihan
    ("62100", "Calais"),                 # Pas-de-Calais
    ("63000", "Clermont-Ferrand"),       # Puy-de-Dome
    ("64000", "Pau"),                    # Pyrenees-Atlantiques
    ("68100", "Mulhouse"),               # Haut-Rhin
    ("72000", "Le Mans"),                # Sarthe
    ("73000", "Chambery"),               # Savoie
    ("74000", "Annecy"),                 # Haute-Savoie
    ("76000", "Rouen"),                  # Seine-Maritime
    ("80000", "Amiens"),                 # Somme
    ("83000", "Toulon"),                 # Var
    ("84000", "Avignon"),                # Vaucluse
    ("86000", "Poitiers"),               # Vienne
    ("87000", "Limoges"),                # Haute-Vienne
    ("88000", "Epinal"),                 # Vosges
    ("93000", "Bobigny"),                # Seine-Saint-Denis
    ("98000", "Monaco"),                 # frontiere
    ("97110", "Pointe-a-Pitre (Guadeloupe)"),
    ("97200", "Fort-de-France (Martinique)"),
    ("97300", "Cayenne (Guyane)"),
    ("97600", "Mamoudzou (Mayotte)"),
]


def random_date(min_age_years: int, max_age_years: int) -> str:
    today = date.today()
    delta = random.randint(min_age_years * 365, max_age_years * 365)
    return (today - timedelta(days=delta)).strftime("%Y-%m-%d")


def generate_profile() -> dict:
    cp, ville = random.choice(CODE_POSTAUX)
    civilite = random.choice(["Monsieur", "Madame"])
    prenom = fake.first_name_male() if civilite == "Monsieur" else fake.first_name_female()
    profession, autre_profession = random.choice(PROFESSIONS)
    who_assure = random.choice(WHO_ASSURE)
    avec_conjoint = who_assure in ("COUPLE", "COUPLE_KIDS")
    avec_enfants = who_assure in ("ADULT_KIDS", "COUPLE_KIDS")
    nb_enfant = random.randint(1, 3) if avec_enfants else 0
    date_effet = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    enfants = {}
    for i in range(1, 6):
        enfants[f"date_naissance_enfant_{i}"] = (
            random_date(0, 18) if i <= nb_enfant else None
        )

    test_label = " | ".join([
        f"who={who_assure}",
        f"regime={random.choice(REGIMES)}",
        f"prof={autre_profession}",
    ])

    return {
        # Garanties souhaitées
        "soins_medicaux": random.choice(NIVEAUX_GARANTIE),
        "hospitalisation": random.choice(NIVEAUX_GARANTIE),
        "optique": random.choice(NIVEAUX_GARANTIE),
        "dentaire": random.choice(NIVEAUX_GARANTIE),
        "auditives": random.choice(NIVEAUX_GARANTIE),
        "mode_sois": random.choice(MODES_SOINS),
        # Assuré principal
        "civilite": civilite,
        "date_naissance": random_date(25, 65),
        "regime": random.choice(REGIMES),
        "profession": profession,
        "autre_profession": autre_profession,
        "date_effet": date_effet,
        "who_assure": who_assure,
        # Conjoint
        "conjoint": "OUI" if avec_conjoint else "NON",
        "conjoint_date_naissance": random_date(25, 65) if avec_conjoint else None,
        "regime_conjoint": random.choice(REGIMES) if avec_conjoint else "REGIME_GENERAL",
        # Enfants
        "nb_enfant": nb_enfant,
        **enfants,
        # Coordonnées
        "type_animal": "NON",
        "civilite_contact": civilite,
        "nom": fake.last_name(),
        "prenom": prenom,
        "adresse": "",
        "cp": cp,
        "ville": ville,
        "email": fake.email(),
        "telephone": "0" + str(random.randint(600000000, 799999999)),
        "accepte_news": False,
        "accepte_news2": False,
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
    """Profil de référence neutre — salarié cadre, seul, Paris, niveaux moyens."""
    date_effet = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    enfants = {f"date_naissance_enfant_{i}": None for i in range(1, 6)}
    return {
        "soins_medicaux": "Moyen",
        "hospitalisation": "Moyen",
        "optique": "Moyen",
        "dentaire": "Moyen",
        "auditives": "Moyen",
        "mode_sois": "2",
        "civilite": "Monsieur",
        "date_naissance": "1985-06-15",
        "regime": "REGIME_GENERAL",
        "profession": "salarie",
        "autre_profession": "salarie_cadre",
        "date_effet": date_effet,
        "who_assure": "ADULT",
        "conjoint": "NON",
        "conjoint_date_naissance": None,
        "regime_conjoint": "REGIME_GENERAL",
        "nb_enfant": 0,
        **enfants,
        "type_animal": "NON",
        "civilite_contact": "Monsieur",
        "nom": "Dupont",
        "prenom": "Jean",
        "adresse": "",
        "cp": cp,
        "ville": ville,
        "email": "jean.dupont@test.fr",
        "telephone": "0612345678",
        "accepte_news": False,
        "accepte_news2": False,
        "accepte_offre": False,
        "provenance": None,
    }


def _label(base: dict, **overrides) -> dict:
    """Applique les overrides et ajoute un _test_label pour traçabilité."""
    p = {**base, **overrides}
    p["_test_label"] = " | ".join(f"{k}={v}" for k, v in overrides.items() if not k.startswith("date_naissance_enfant"))
    return p


def generate_deterministic_profiles() -> list[dict]:
    """
    Génère une suite de profils déterministes pour diagnostiquer le site Santé.
    Chaque série isole une variable par rapport au profil de base neutre.
    """
    profiles = []
    base = _base_profile()

    # --- 1. who_assure (les 4 cas) ---
    # ADULT : seul
    profiles.append(_label(base, who_assure="ADULT", conjoint="NON", conjoint_date_naissance=None, nb_enfant=0))
    # COUPLE : avec conjoint, sans enfants
    ddn_c = (date.today() - timedelta(days=35 * 365)).strftime("%Y-%m-%d")
    profiles.append(_label(base, who_assure="COUPLE", conjoint="OUI", conjoint_date_naissance=ddn_c, regime_conjoint="REGIME_GENERAL", nb_enfant=0))
    # ADULT_KIDS : seul avec enfants
    enfants_1 = {f"date_naissance_enfant_{i}": ("2015-01-01" if i <= 1 else None) for i in range(1, 6)}
    profiles.append(_label(base, who_assure="ADULT_KIDS", conjoint="NON", conjoint_date_naissance=None, nb_enfant=1, **enfants_1))
    # COUPLE_KIDS : couple avec enfants
    enfants_2 = {f"date_naissance_enfant_{i}": ("2015-01-01" if i <= 2 else None) for i in range(1, 6)}
    profiles.append(_label(base, who_assure="COUPLE_KIDS", conjoint="OUI", conjoint_date_naissance=ddn_c, regime_conjoint="REGIME_GENERAL", nb_enfant=2, **enfants_2))

    # --- 2. regime ---
    for regime in REGIMES:
        profiles.append(_label(base, regime=regime))

    # --- 3. regime_conjoint (avec conjoint) ---
    for regime_c in REGIMES:
        profiles.append(_label(base,
            who_assure="COUPLE", conjoint="OUI",
            conjoint_date_naissance=ddn_c,
            regime_conjoint=regime_c,
        ))

    # --- 4. profession / autre_profession ---
    for profession, autre_profession in PROFESSIONS:
        profiles.append(_label(base, profession=profession, autre_profession=autre_profession))

    # --- 5. âge de l'assuré principal (dense, tous les ans de 18 à 80) ---
    for age in range(18, 81):
        ddn = (date.today() - timedelta(days=age * 365)).strftime("%Y-%m-%d")
        profiles.append(_label(base, date_naissance=ddn))

    # --- 6. niveaux de garantie par poste ---
    for niveau in NIVEAUX_GARANTIE:
        profiles.append(_label(base, soins_medicaux=niveau))
    for niveau in NIVEAUX_GARANTIE:
        profiles.append(_label(base, hospitalisation=niveau))
    for niveau in NIVEAUX_GARANTIE:
        profiles.append(_label(base, optique=niveau))
    for niveau in NIVEAUX_GARANTIE:
        profiles.append(_label(base, dentaire=niveau))
    for niveau in NIVEAUX_GARANTIE:
        profiles.append(_label(base, auditives=niveau))

    # --- 7. mode_sois ---
    for mode in MODES_SOINS:
        profiles.append(_label(base, mode_sois=mode))

    # --- 8. nb_enfants (ADULT_KIDS, 0 à 5) ---
    for nb_e in range(0, 6):
        enfants = {f"date_naissance_enfant_{i}": ("2015-01-01" if i <= nb_e else None) for i in range(1, 6)}
        profiles.append(_label(base, who_assure="ADULT_KIDS", conjoint="NON", conjoint_date_naissance=None, nb_enfant=nb_e, **enfants))

    # --- 9. âge conjoint (dense, tous les 2 ans de 18 à 80) ---
    for age_c in range(18, 81, 2):
        ddn_cv = (date.today() - timedelta(days=age_c * 365)).strftime("%Y-%m-%d")
        profiles.append(_label(base, who_assure="COUPLE", conjoint="OUI", conjoint_date_naissance=ddn_cv, regime_conjoint="REGIME_GENERAL", nb_enfant=0))

    # --- 10. géographie (couverture departementale elargie) ---
    for cp, ville in CODE_POSTAUX:
        b = _base_profile(cp=cp, ville=ville)
        profiles.append(_label(b, cp=cp, ville=ville))

    return profiles


def _base_profile_senior(cp: str = "75001", ville: str = "Paris") -> dict:
    """Profil de référence senior — 65 ans, pour couvrir la gamme SERENISSIA (55+)."""
    ddn_65 = (date.today() - timedelta(days=65 * 365)).strftime("%Y-%m-%d")
    p = _base_profile(cp=cp, ville=ville)
    p["date_naissance"] = ddn_65
    return p


def generate_senior_profiles() -> list[dict]:
    """
    Génère une suite de profils déterministes avec un assuré senior (65 ans)
    pour tester who_assure/régime/ville/garanties sur la gamme SERENISSIA,
    jamais couverte par le profil de base standard (41 ans -> gamme Formule).
    """
    profiles = []
    base = _base_profile_senior()

    # --- 1. who_assure (les 4 cas), conjoint aussi senior ---
    ddn_c_senior = (date.today() - timedelta(days=65 * 365)).strftime("%Y-%m-%d")
    profiles.append(_label(base, who_assure="ADULT", conjoint="NON", conjoint_date_naissance=None, nb_enfant=0))
    profiles.append(_label(base, who_assure="COUPLE", conjoint="OUI", conjoint_date_naissance=ddn_c_senior, regime_conjoint="REGIME_GENERAL", nb_enfant=0))

    # --- 2. regime ---
    for regime in REGIMES:
        profiles.append(_label(base, regime=regime))

    # --- 3. regime_conjoint (avec conjoint senior) ---
    for regime_c in REGIMES:
        profiles.append(_label(base,
            who_assure="COUPLE", conjoint="OUI",
            conjoint_date_naissance=ddn_c_senior,
            regime_conjoint=regime_c,
        ))

    # --- 4. niveaux de garantie par poste ---
    for niveau in NIVEAUX_GARANTIE:
        profiles.append(_label(base, soins_medicaux=niveau))
    for niveau in NIVEAUX_GARANTIE:
        profiles.append(_label(base, hospitalisation=niveau))
    for niveau in NIVEAUX_GARANTIE:
        profiles.append(_label(base, optique=niveau))
    for niveau in NIVEAUX_GARANTIE:
        profiles.append(_label(base, dentaire=niveau))
    for niveau in NIVEAUX_GARANTIE:
        profiles.append(_label(base, auditives=niveau))

    # --- 5. mode_sois ---
    for mode in MODES_SOINS:
        profiles.append(_label(base, mode_sois=mode))

    # --- 6. géographie (20 villes) ---
    for cp, ville in CODE_POSTAUX:
        b = _base_profile_senior(cp=cp, ville=ville)
        profiles.append(_label(b, cp=cp, ville=ville))

    return profiles
