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
