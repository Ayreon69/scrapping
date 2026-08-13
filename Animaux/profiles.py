import random
from datetime import date, timedelta
from faker import Faker

fake = Faker("fr_FR")

RACES_CHIEN = [
    "Labrador Retriever",
    "Golden Retriever",
    "Berger Allemand",
    "Bouledogue Français",
    "Beagle",
    "Caniche",
    "American Staffordshire Terrier",
    "Chihuahua",
    "Yorkshire Terrier",
    "Husky Sibérien",
]

RACES_CHAT = [
    "Européen",
    "Maine Coon",
    "Persan",
    "Siamois",
    "Ragdoll",
    "Bengal",
    "British Shorthair",
    "Sacré de Birmanie",
    "Scottish Fold",
    "Sphynx",
]

FORMULES = [
    "Formule Accident",
    "Formule Confort",
    "Formule Premium",
]

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
    min_days = min_age_years * 365
    max_days = max_age_years * 365
    delta = random.randint(min_days, max_days)
    birth = today - timedelta(days=delta)
    return birth.strftime("%Y-%m-%d")


def generate_profile() -> dict:
    type_animal = random.choice(["Chien", "Chat"])
    races = RACES_CHIEN if type_animal == "Chien" else RACES_CHAT
    race = random.choice(races)
    sexe = random.choice(["Male", "Femelle"])
    cp, ville = random.choice(CODE_POSTAUX)
    civilite = random.choice(["Monsieur", "Madame"])
    prenom = fake.first_name_male() if civilite == "Monsieur" else fake.first_name_female()
    nom = fake.last_name()

    # Date effet = demain
    date_effet = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    return {
        "id": None,
        "id_forms": 2,
        "produit": 2,
        "type_animal": type_animal,
        "race_un": race,
        "nom_animal": fake.first_name(),
        "sexe_animal": sexe,
        "formule_souhaitee": random.choice(FORMULES),
        "animal_date_naissance": random_date(0, 8),      # animal 0-8 ans
        "date_effet": date_effet,
        "tatouage": random.choice(["OUI", "NON"]),
        "type_race": "PURE",
        "LOF": "OUI",
        "civilite": civilite,
        "nom": nom,
        "prenom": prenom,
        "adresse": fake.street_address(),
        "cp": cp,
        "ville": ville,
        "email": fake.email(),
        "telephone": "0" + str(random.randint(600000000, 799999999)),
        "date_naissance": random_date(25, 65),            # proprio 25-65 ans
        "profession": "salarie",
        "autre_profession": None,
        "accepte_offre_mg": "non",
        "accepte_offre_part_mg": "non",
        "accepte_news": False,
        "accepte_offre": False,
        "recaptcha": 1,
        "provenance": None,
    }


def generate_profiles(n: int) -> list:
    return [generate_profile() for _ in range(n)]


# ---------------------------------------------------------------------------
# Profils déterministes pour diagnostic
# ---------------------------------------------------------------------------

def _base_profile(cp: str = "75001", ville: str = "Paris") -> dict:
    """Profil de référence neutre — chat européen, 3 ans, propriétaire 40 ans, Paris."""
    date_effet = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    return {
        "id": None,
        "id_forms": 2,
        "produit": 2,
        "type_animal": "Chat",
        "race_un": "Européen",
        "nom_animal": "Felix",
        "sexe_animal": "Male",
        "formule_souhaitee": "Formule Confort",
        "animal_date_naissance": (date.today() - timedelta(days=3 * 365)).strftime("%Y-%m-%d"),
        "date_effet": date_effet,
        "tatouage": "OUI",
        "type_race": "PURE",
        "LOF": "OUI",
        "civilite": "Monsieur",
        "nom": "Dupont",
        "prenom": "Jean",
        "adresse": "12 rue de la Paix",
        "cp": cp,
        "ville": ville,
        "email": "jean.dupont@test.fr",
        "telephone": "0612345678",
        "date_naissance": (date.today() - timedelta(days=40 * 365)).strftime("%Y-%m-%d"),
        "profession": "salarie",
        "autre_profession": None,
        "accepte_offre_mg": "non",
        "accepte_offre_part_mg": "non",
        "accepte_news": False,
        "accepte_offre": False,
        "recaptcha": 1,
        "provenance": None,
    }


def _label(base: dict, **overrides) -> dict:
    p = {**base, **overrides}
    p["_test_label"] = " | ".join(f"{k}={v}" for k, v in overrides.items())
    return p


def generate_deterministic_profiles() -> list[dict]:
    """
    Génère une suite de profils déterministes pour diagnostiquer le site Animaux.
    Chaque série isole une variable par rapport au profil de base neutre.
    """
    profiles = []
    base = _base_profile()

    # --- 1. type_animal + race (Chien vs Chat) ---
    for race in RACES_CHIEN:
        profiles.append(_label(base, type_animal="Chien", race_un=race))
    for race in RACES_CHAT:
        profiles.append(_label(base, type_animal="Chat", race_un=race))

    # --- 2. sexe_animal ---
    for sexe in ["Male", "Femelle"]:
        profiles.append(_label(base, sexe_animal=sexe))

    # --- 3. formule_souhaitee ---
    for formule in FORMULES:
        profiles.append(_label(base, formule_souhaitee=formule))

    # --- 4. tatouage ---
    for tatouage in ["OUI", "NON"]:
        profiles.append(_label(base, tatouage=tatouage))

    # --- 5. âge de l'animal (seuils clés) ---
    for age in [0, 1, 2, 3, 5, 7, 8, 10]:
        ddn = (date.today() - timedelta(days=age * 365)).strftime("%Y-%m-%d")
        profiles.append(_label(base, animal_date_naissance=ddn))

    # --- 6. âge du propriétaire (seuils clés) ---
    for age in [18, 25, 35, 50, 65, 75]:
        ddn = (date.today() - timedelta(days=age * 365)).strftime("%Y-%m-%d")
        profiles.append(_label(base, date_naissance=ddn))

    # --- 7. géographie ---
    for cp, ville in CODE_POSTAUX:
        b = _base_profile(cp=cp, ville=ville)
        profiles.append(_label(b, cp=cp, ville=ville))

    return profiles
