import csv
import json
import logging
import random
import time
from pathlib import Path

import requests

from config import (
    BASE_URL,
    DELAY_BETWEEN_PROFILES,
    DELAY_BETWEEN_REQUESTS,
    HEADERS,
    PROVENANCE,
    SLUGS_ASSUREURS,
)
from profiles import generate_profiles

OUTPUT_DIR = Path("output")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def get_session() -> requests.Session:
    """Ouvre une session et récupère les cookies Laravel (XSRF + session)."""
    session = requests.Session()
    session.headers.update(HEADERS)

    log.info("Initialisation de la session...")
    resp = session.get(f"{BASE_URL}/app/animaux", timeout=15)
    resp.raise_for_status()

    xsrf = session.cookies.get("XSRF-TOKEN")
    if xsrf:
        # Laravel attend le token décodé dans le header
        from urllib.parse import unquote
        session.headers["x-xsrf-token"] = unquote(xsrf)
        log.info("XSRF-TOKEN récupéré ✓")
    else:
        log.warning("XSRF-TOKEN absent — la session pourrait être rejetée")

    return session


def create_lead(session: requests.Session, profile: dict) -> int | None:
    """Envoie le profil et retourne le devis_id."""
    payload = {**profile, "provenance": PROVENANCE}

    log.info(f"Création du devis pour {profile['prenom']} {profile['nom']} "
             f"({profile['type_animal']} - {profile['race_un']})...")

    resp = session.post(
        f"{BASE_URL}/app/api/animaux/insert-lead",
        json=payload,
        timeout=15,
    )

    log.info(f"insert-lead → HTTP {resp.status_code}")
    log.info(f"insert-lead → Réponse brute : {resp.text[:500]}")

    if resp.status_code != 200:
        log.error(f"insert-lead → ÉCHEC HTTP {resp.status_code}")
        return None, []

    try:
        data = resp.json()
    except Exception:
        log.error(f"insert-lead → Réponse non-JSON : {resp.text[:300]}")
        return None, []

    lead = data.get("lead", {})
    devis_id = lead.get("id")
    slugs = data.get("clients_animaux", SLUGS_ASSUREURS)

    if devis_id:
        log.info(f"Devis créé → id={devis_id}, assureurs={slugs} ✓")
    else:
        log.error(f"Pas d'id dans la réponse JSON : {data}")
    return devis_id, slugs


def get_offers(session: requests.Session, devis_id: int, slugs: list = None) -> dict:
    """Récupère les offres de chaque assureur pour ce devis."""
    offers = {}

    for slug in (slugs or SLUGS_ASSUREURS):
        delay = random.uniform(*DELAY_BETWEEN_REQUESTS)
        log.info(f"  [{slug}] attente {delay:.1f}s...")
        time.sleep(delay)

        url = f"{BASE_URL}/app/tarif-animaux/{devis_id}/{slug}"
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                offers[slug] = data
                nb = len(data.get("data", data if isinstance(data, list) else []))
                log.info(f"  [{slug}] {nb} offre(s) ✓")
            else:
                log.warning(f"  [{slug}] HTTP {resp.status_code}")
                offers[slug] = None
        except Exception as e:
            log.error(f"  [{slug}] Erreur : {e}")
            offers[slug] = None

    return offers


def flatten_for_csv(profile: dict, devis_id: int, slug: str, offer_data) -> list[dict]:
    """Aplatit les offres d'un assureur en lignes CSV."""
    rows = []
    od = offer_data if isinstance(offer_data, dict) else {}
    base = {
        "devis_id": devis_id,
        "type_animal": profile["type_animal"],
        "race": profile["race_un"],
        "sexe_animal": profile["sexe_animal"],
        "animal_date_naissance": profile["animal_date_naissance"],
        "cp": profile["cp"],
        "assureur": od.get("Nom_compagne", slug),
        "promo": od.get("promo_text", ""),
    }

    if offer_data is None:
        rows.append({**base, "formule": "ERREUR", "tarif_mensuel": "", "tarif_annuel": "",
                     "plafond": "", "franchise": "", "chirurgicaux_accident_%": "",
                     "medicaux_accident_%": "", "chirurgicaux_maladie_%": "",
                     "medicaux_maladie_%": ""})
        return rows

    items = offer_data.get("data", []) if isinstance(offer_data, dict) else offer_data

    if not items:
        rows.append({**base, "formule": "AUCUNE OFFRE", "tarif_mensuel": "", "tarif_annuel": "",
                     "plafond": "", "franchise": "", "chirurgicaux_accident_%": "",
                     "medicaux_accident_%": "", "chirurgicaux_maladie_%": "",
                     "medicaux_maladie_%": ""})
        return rows

    for item in items:
        g = item.get("garanties", {})
        tarif = item.get("tarif", "")
        try:
            tarif_annuel = round(float(tarif) * 12, 2) if tarif else ""
        except (ValueError, TypeError):
            tarif_annuel = ""

        row = {
            **base,
            "formule": item.get("formule_affichage") or item.get("formule", ""),
            "tarif_mensuel": tarif,
            "tarif_annuel": tarif_annuel,
            "plafond": g.get("Plafond", ""),
            "franchise": g.get("Franchise", ""),
            "chirurgicaux_accident_%": g.get("Chirurgicaux_Accident", ""),
            "medicaux_accident_%": g.get("Medicaux_Accident", ""),
            "chirurgicaux_maladie_%": g.get("Chirurgicaux_Maladie", ""),
            "medicaux_maladie_%": g.get("Medicaux_Maladie", ""),
        }
        rows.append(row)

    return rows


def save_results(results: list, output_dir: Path):
    output_dir.mkdir(exist_ok=True)

    # JSON brut complet
    json_path = output_dir / "results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    log.info(f"JSON sauvegardé → {json_path}")

    # CSV aplati
    csv_path = output_dir / "results.csv"
    csv_rows = []
    for r in results:
        if not r.get("devis_id"):
            continue
        for slug, offer_data in r["offers"].items():
            csv_rows.extend(flatten_for_csv(r["profile"], r["devis_id"], slug, offer_data))

    if csv_rows:
        fieldnames = list(csv_rows[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
        log.info(f"CSV sauvegardé → {csv_path} ({len(csv_rows)} lignes)")


def run(n_profiles: int = 5):
    OUTPUT_DIR.mkdir(exist_ok=True)
    results = []

    profiles = generate_profiles(n_profiles)
    log.info(f"=== Démarrage : {n_profiles} profils à traiter ===")

    for i, profile in enumerate(profiles, 1):
        log.info(f"\n--- Profil {i}/{n_profiles} ---")

        session = get_session()
        devis_id, slugs = create_lead(session, profile)

        result = {"profile": profile, "devis_id": devis_id, "offers": {}}

        if devis_id:
            result["offers"] = get_offers(session, devis_id, slugs)

        results.append(result)

        # Sauvegarde intermédiaire après chaque profil
        save_results(results, OUTPUT_DIR)

        if i < n_profiles:
            delay = random.uniform(*DELAY_BETWEEN_PROFILES)
            log.info(f"Pause {delay:.0f}s avant le prochain profil...")
            time.sleep(delay)

    log.info(f"\n=== Terminé : {len(results)} profils traités ===")
    return results


if __name__ == "__main__":
    run(n_profiles=5)
