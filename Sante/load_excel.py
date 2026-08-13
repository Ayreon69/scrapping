"""
Charge des profils depuis profils_template.xlsx.
Convertit les libelles lisibles en valeurs API.
"""
import random
from datetime import date, timedelta
from faker import Faker
from openpyxl import load_workbook

fake = Faker("fr_FR")

# ---------------------------------------------------------------------------
# Tables de conversion libelle -> valeur API
# ---------------------------------------------------------------------------

QUI_ASSURER_MAP = {
    "Moi seul":                          ("ADULT",       "NON"),
    "Mon couple (sans enfant)":          ("COUPLE",      "OUI"),
    "Moi et mes enfants (sans conjoint)":("ADULT_KIDS",  "NON"),
    "Mon couple et mes enfants":         ("COUPLE_KIDS", "OUI"),
}

REGIME_MAP = {
    "General":           "REGIME_GENERAL",
    "TNS (independant)": "TNS",
    "Agricole":          "SALARIE_AGRICOLE",
    "Alsace-Moselle":    "ALSACE_MOSELLE",
}

PROFESSION_MAP = {
    "Salarie cadre":                  ("salarie",               "salarie_cadre"),
    "Fonction publique d etat":       ("salarie",               "Fonction_publique_d_etat"),
    "Fonction publique territoriale": ("salarie",               "Fonction_publique_territoriale"),
    "Fonction publique hospitaliere": ("salarie",               "Fonction_publique_hospitaliere"),
    "Artisan":                        ("salarie",               "artisan"),
    "Commercant":                     ("salarie",               "commercant"),
    "Profession liberale":            ("salarie",               "profession_liberale"),
    "Chef d entreprise":              ("salarie",               "chef_d_entreprise"),
    "Enseignant":                     ("salarie",               "enseignant"),
    "Agriculteur":                    ("salarie",               "agriculteur"),
    "Exploitant agricole":            ("salarie",               "exploitant_agricole"),
    "VRP":                            ("salarie",               "VRP"),
    "Visiteur medical":               ("salarie",               "visiteur_medical"),
    "Sans profession":                ("salarie",               "sans_profession"),
    "Etudiant":                       ("etudiant",              "etudiant"),
    "Retraite":                       ("retraite",              "retraite"),
    "En recherche d emploi":          ("en_recherche_d_emploi", "en_recherche_d_emploi"),
}

MODE_SOIS_MAP = {
    "Medecin traitant (conseille)": "2",
    "Securite sociale seule":       "1",
    "Acces libre":                  "3",
    "Personnalise":                 "4",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _str(val) -> str:
    if val is None:
        return ""
    return str(val).strip()


def _parse_date(val) -> str:
    """Accepte JJ/MM/AAAA ou AAAA-MM-JJ, retourne AAAA-MM-JJ."""
    s = _str(val)
    if not s:
        return ""
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
    return s


def _random_phone() -> str:
    return "0" + str(random.randint(600000000, 799999999))


def _random_email(prenom: str, nom: str) -> str:
    if prenom and nom:
        base = f"{prenom.lower()}.{nom.lower()}".replace(" ", "")
        return f"{base}{random.randint(1, 99)}@example.fr"
    return fake.email()


# ---------------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------------

def load_profiles_from_excel(path: str) -> list[dict]:
    wb = load_workbook(path, data_only=True)
    if "Profils" not in wb.sheetnames:
        raise ValueError(f"Feuille 'Profils' introuvable dans {path}")

    ws = wb["Profils"]

    # Les en-tetes sont en ligne 2 (ligne 1 = blocs de couleur)
    headers = [_str(cell.value) for cell in ws[2]]

    date_effet = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    profiles = []

    for row in ws.iter_rows(min_row=3, values_only=True):
        if all(v is None or _str(v) == "" for v in row):
            continue

        r = {headers[i]: _str(v) for i, v in enumerate(row) if i < len(headers)}

        # --- Qui assurer ---
        qui = r.get("Qui assurer ?", "Moi seul")
        who_assure, conjoint = QUI_ASSURER_MAP.get(qui, ("ADULT", "NON"))

        # --- Regime ---
        regime_label = r.get("Regime secu", "General")
        regime = REGIME_MAP.get(regime_label, "REGIME_GENERAL")

        regime_c_label = r.get("Regime secu conjoint", "")
        regime_conjoint = REGIME_MAP.get(regime_c_label, "REGIME_GENERAL") if regime_c_label else "REGIME_GENERAL"

        # --- Profession ---
        prof_label = r.get("Profession", "Salarie cadre")
        profession, autre_profession = PROFESSION_MAP.get(prof_label, ("salarie", "salarie_cadre"))

        # --- Mode remboursement ---
        mode_label = r.get("Mode remboursement", "Medecin traitant (conseille)")
        mode_sois = MODE_SOIS_MAP.get(mode_label, "2")

        # --- Dates ---
        date_naissance     = _parse_date(r.get("Date de naissance", ""))
        conjoint_ddn       = _parse_date(r.get("Date naissance conjoint", "")) or None
        ddn_e1             = _parse_date(r.get("Date naissance enfant 1", "")) or None
        ddn_e2             = _parse_date(r.get("Date naissance enfant 2", "")) or None
        ddn_e3             = _parse_date(r.get("Date naissance enfant 3", "")) or None

        nb_enfant = sum(1 for d in [ddn_e1, ddn_e2, ddn_e3] if d)

        # --- Identite (auto si vide) ---
        civilite  = random.choice(["Monsieur", "Madame"])
        nom       = fake.last_name()
        prenom    = fake.first_name_male() if civilite == "Monsieur" else fake.first_name_female()
        email     = _random_email(prenom, nom)
        telephone = _random_phone()

        cp    = r.get("Code postal", "") or "75001"
        ville = r.get("Ville", "")       or "Paris"

        label_parts = [qui, regime_label, prof_label]
        test_label  = " | ".join(p for p in label_parts if p)

        profile = {
            "soins_medicaux":   r.get("Soins medicaux",   "") or "Moyen",
            "hospitalisation":  r.get("Hospitalisation",  "") or "Moyen",
            "optique":          r.get("Optique",          "") or "Moyen",
            "dentaire":         r.get("Dentaire",         "") or "Moyen",
            "auditives":        r.get("Auditives",        "") or "Moyen",
            "mode_sois":        mode_sois,
            "civilite":         civilite,
            "date_naissance":   date_naissance,
            "regime":           regime,
            "profession":       profession,
            "autre_profession": autre_profession,
            "date_effet":       date_effet,
            "who_assure":       who_assure,
            "conjoint":         conjoint,
            "conjoint_date_naissance": conjoint_ddn,
            "regime_conjoint":  regime_conjoint,
            "nb_enfant":        nb_enfant,
            "date_naissance_enfant_1": ddn_e1,
            "date_naissance_enfant_2": ddn_e2,
            "date_naissance_enfant_3": ddn_e3,
            "date_naissance_enfant_4": None,
            "date_naissance_enfant_5": None,
            "type_animal":      "NON",
            "civilite_contact": civilite,
            "nom":              nom,
            "prenom":           prenom,
            "adresse":          "",
            "cp":               cp,
            "ville":            ville,
            "email":            email,
            "telephone":        telephone,
            "accepte_news":     False,
            "accepte_news2":    False,
            "accepte_offre":    False,
            "provenance":       None,
            "_test_label":      test_label,
        }
        profiles.append(profile)

    if not profiles:
        raise ValueError(f"Aucun profil trouve dans {path} (toutes les lignes sont vides)")

    return profiles
