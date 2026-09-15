"""Serveur MCP exposant l'API interne de mongustave.fr (Sante, MRH, Animaux).

Reutilise directement get_session/create_lead/get_offers des scrapers existants
(Sante/, MRH/, Animaux/) : chaque outil MCP soumet un profil au formulaire du
site et renvoie les tarifs bruts retournes par l'API, assureur par assureur.

Usage prevu : tests/diagnostics sur le projet de scraping lui-meme (cf.
DOCUMENTATION_SCRAPING.md). Ne pas utiliser pour generer des leads en masse.
"""

import logging
import sys
from datetime import date, timedelta
from pathlib import Path

from mcp.server.mcpserver import MCPServer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loaders import load_product_scraper  # noqa: E402

logging.basicConfig(level=logging.WARNING)

mcp = MCPServer("mongustave-devis")


def _date_naissance(age_annees: int) -> str:
    return (date.today() - timedelta(days=age_annees * 365)).strftime("%Y-%m-%d")


@mcp.tool()
def obtenir_devis_sante(
    age: int = 40,
    code_postal: str = "75001",
    ville: str = "Paris",
    regime: str = "REGIME_GENERAL",
    profession: str = "salarie",
    autre_profession: str = "salarie_cadre",
    who_assure: str = "ADULT",
    age_conjoint: int | None = None,
    nb_enfants: int = 0,
    niveau_garantie: str = "Moyen",
) -> dict:
    """Simule un devis Sante sur mongustave.fr et retourne les tarifs par assureur.

    who_assure: ADULT, COUPLE, ADULT_KIDS ou COUPLE_KIDS.
    niveau_garantie s'applique a soins_medicaux/hospitalisation/optique/dentaire/auditives.
    """
    scraper = load_product_scraper("sante")
    from profiles import _base_profile  # module isole charge par le loader

    profile = _base_profile(cp=code_postal, ville=ville)
    avec_conjoint = who_assure in ("COUPLE", "COUPLE_KIDS")
    avec_enfants = who_assure in ("ADULT_KIDS", "COUPLE_KIDS")
    enfants = {f"date_naissance_enfant_{i}": (_date_naissance(5) if i <= nb_enfants and avec_enfants else None) for i in range(1, 6)}

    profile.update(
        date_naissance=_date_naissance(age),
        regime=regime,
        profession=profession,
        autre_profession=autre_profession,
        who_assure=who_assure,
        conjoint="OUI" if avec_conjoint else "NON",
        conjoint_date_naissance=_date_naissance(age_conjoint) if avec_conjoint and age_conjoint else None,
        nb_enfant=nb_enfants if avec_enfants else 0,
        soins_medicaux=niveau_garantie,
        hospitalisation=niveau_garantie,
        optique=niveau_garantie,
        dentaire=niveau_garantie,
        auditives=niveau_garantie,
        **enfants,
    )

    session = scraper.get_session()
    devis_id, slugs = scraper.create_lead(session, profile)
    if not devis_id:
        return {"erreur": "Echec de creation du devis (insert-lead)", "profile": profile}

    offers = scraper.get_offers(session, devis_id, slugs)
    return {"devis_id": devis_id, "offers": offers}


@mcp.tool()
def obtenir_devis_mrh(
    age: int = 40,
    code_postal: str = "75001",
    ville: str = "Paris",
    type_habitation: str = "APPARTEMENT",
    surface_habitable: str = "60",
    statut_resident: str = "LOCATAIRE_COLOCATAIRE",
    profession: str = "salarie",
    nbr_adultes: int = 1,
    nbr_enfants: int = 0,
    capital_mobilier: int = 15000,
) -> dict:
    """Simule un devis assurance habitation (MRH) sur mongustave.fr et retourne les tarifs par assureur.

    type_habitation: APPARTEMENT ou MAISON.
    statut_resident: LOCATAIRE_COLOCATAIRE ou PROPRIETAIRE (valeurs du formulaire).
    """
    scraper = load_product_scraper("mrh")
    from profiles import _base_profile

    profile = _base_profile(cp=code_postal, ville=ville)
    profile.update(
        date_naissance=_date_naissance(age),
        type_habitation=type_habitation,
        surface_habitable=surface_habitable,
        statut_resident=statut_resident,
        profession=profession,
        nbr_adultes=nbr_adultes,
        nbr_enfants=nbr_enfants,
        capital_mobilier=capital_mobilier,
        cp_logment=code_postal,
        ville_logment=ville,
    )

    session = scraper.get_session()
    devis_id, slugs = scraper.create_lead(session, profile)
    if not devis_id:
        return {"erreur": "Echec de creation du devis (insert-lead-v2)", "profile": profile}

    offers = scraper.get_offers(session, devis_id, slugs)
    return {"devis_id": devis_id, "offers": offers}


@mcp.tool()
def obtenir_devis_animaux(
    type_animal: str = "Chat",
    race: str = "Européen",
    age_animal: int = 3,
    sexe_animal: str = "Male",
    formule_souhaitee: str = "Formule Confort",
    age_proprietaire: int = 40,
    code_postal: str = "75001",
    ville: str = "Paris",
) -> dict:
    """Simule un devis assurance animaux sur mongustave.fr et retourne les tarifs par assureur.

    type_animal: Chien ou Chat. formule_souhaitee: Formule Accident/Confort/Premium.
    """
    scraper = load_product_scraper("animaux")
    from profiles import _base_profile

    profile = _base_profile(cp=code_postal, ville=ville)
    profile.update(
        type_animal=type_animal,
        race_un=race,
        sexe_animal=sexe_animal,
        formule_souhaitee=formule_souhaitee,
        animal_date_naissance=_date_naissance(age_animal),
        date_naissance=_date_naissance(age_proprietaire),
    )

    session = scraper.get_session()
    devis_id, slugs = scraper.create_lead(session, profile)
    if not devis_id:
        return {"erreur": "Echec de creation du devis (insert-lead)", "profile": profile}

    offers = scraper.get_offers(session, devis_id, slugs)
    return {"devis_id": devis_id, "offers": offers}


if __name__ == "__main__":
    mcp.run()
