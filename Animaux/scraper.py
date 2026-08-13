import csv
import json
import logging
import random
import shutil
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import requests
from requests import RequestException

from config import (
    BASE_URL,
    CSV_DELIMITER,
    CSV_ENCODING,
    DEFAULT_N_PROFILES,
    DELAY_BETWEEN_PROFILES,
    ENABLE_XLSX_EXPORT,
    HEADERS,
    PROVENANCE,
    REQUEST_TIMEOUT,
    SLUGS_ASSUREURS,
)
from profiles import generate_deterministic_profiles, generate_profiles

OUTPUT_DIR = Path("output")
ARCHIVE_DIR = OUTPUT_DIR / "archive"
log = logging.getLogger(__name__)
LOG_FORMAT = "%(asctime)s  %(levelname)s  %(message)s"
PENDING_PROFILES_PATH = OUTPUT_DIR / "pending_profiles.json"
RESULTS_PATH = OUTPUT_DIR / "results.json"


def setup_logging(output_dir: Path) -> None:
    output_dir.mkdir(exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT, datefmt="%H:%M:%S")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if root_logger.handlers:
        return

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(output_dir / "scraper.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def archive_previous_results(output_dir: Path) -> None:
    """Déplace les résultats existants dans archive/ avant un nouveau run."""
    files_to_archive = [
        output_dir / "results.json",
        output_dir / "results.csv",
        output_dir / "results.xlsx",
    ]
    if not any(f.exists() for f in files_to_archive):
        return

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for f in files_to_archive:
        if f.exists():
            dest = ARCHIVE_DIR / f"{stamp}_{f.name}"
            shutil.move(str(f), str(dest))
            log.info(f"Archive -> {dest}")


def clean_cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "OUI" if value else "NON"
    return str(value)


def export_xlsx(csv_rows: list[dict], output_dir: Path) -> bool:
    if not ENABLE_XLSX_EXPORT or not csv_rows:
        return False

    try:
        from openpyxl import Workbook
    except ImportError:
        log.warning("openpyxl indisponible: export XLSX ignore")
        return False

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "resultats"

    headers = list(csv_rows[0].keys())
    sheet.append(headers)
    for row in csv_rows:
        sheet.append([row.get(header, "") for header in headers])

    xlsx_path = output_dir / "results.xlsx"
    workbook.save(xlsx_path)
    log.info(f"XLSX sauvegarde -> {xlsx_path}")
    return True


def load_existing_results(output_dir: Path) -> list:
    json_path = output_dir / "results.json"
    if not json_path.exists():
        return []

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        log.warning(f"Impossible de relire {json_path}: {exc}")
        return []

    return data if isinstance(data, list) else []


def prepare_profiles(n_profiles: int, output_dir: Path, resume: bool = True, deterministic: bool = False) -> list[dict]:
    if resume and PENDING_PROFILES_PATH.exists():
        with open(PENDING_PROFILES_PATH, "r", encoding="utf-8") as f:
            pending_profiles = json.load(f)
        log.info(f"Reprise detectee -> {len(pending_profiles)} profil(s) restant(s)")
        return pending_profiles

    if deterministic:
        profiles = generate_deterministic_profiles()
        log.info(f"Mode deterministe -> {len(profiles)} profil(s) de diagnostic generes")
    else:
        profiles = generate_profiles(n_profiles)
    with open(PENDING_PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)
    log.info(f"Nouveau lot prepare -> {len(profiles)} profil(s)")
    return profiles


def save_pending_profiles(pending_profiles: list[dict]) -> None:
    if pending_profiles:
        with open(PENDING_PROFILES_PATH, "w", encoding="utf-8") as f:
            json.dump(pending_profiles, f, ensure_ascii=False, indent=2)
    elif PENDING_PROFILES_PATH.exists():
        PENDING_PROFILES_PATH.unlink()


def get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)

    log.info("Initialisation de la session...")
    resp = session.get(f"{BASE_URL}/app/animaux", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    xsrf = session.cookies.get("XSRF-TOKEN")
    if xsrf:
        session.headers["x-xsrf-token"] = unquote(xsrf)
        log.info("XSRF-TOKEN recupere")
    else:
        log.warning("XSRF-TOKEN absent")

    return session


def _refresh_session_if_needed(session: requests.Session) -> requests.Session:
    """Vérifie que le XSRF-TOKEN est toujours présent, le renouvelle si nécessaire."""
    if session.cookies.get("XSRF-TOKEN"):
        return session
    log.info("XSRF-TOKEN expire, renouvellement de la session...")
    return get_session()


def create_lead(session: requests.Session, profile: dict) -> tuple[int | None, list]:
    payload = {**profile, "provenance": PROVENANCE}

    log.info(
        f"Creation du devis pour {profile['prenom']} {profile['nom']} "
        f"({profile['type_animal']} - {profile['race_un']})..."
    )

    try:
        resp = session.post(
            f"{BASE_URL}/app/api/animaux/insert-lead",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
    except RequestException as exc:
        log.error(f"insert-lead -> erreur reseau : {exc}")
        return None, []

    log.info(f"insert-lead -> HTTP {resp.status_code}")
    log.info(f"insert-lead -> reponse brute : {resp.text[:500]}")

    if resp.status_code not in (200, 201):
        log.error(f"insert-lead -> echec HTTP {resp.status_code}")
        return None, []

    try:
        data = resp.json()
    except ValueError:
        log.error(f"insert-lead -> reponse non JSON : {resp.text[:300]}")
        return None, []

    lead = data.get("lead") or {}
    devis_id = lead.get("id")
    slugs = data.get("clients_animaux") or SLUGS_ASSUREURS

    if devis_id:
        log.info(f"Devis cree -> id={devis_id}, assureurs={slugs}")
    else:
        log.error(f"Pas d'id dans la reponse : {data}")

    return devis_id, slugs


def fetch_slug(devis_id: int, slug: str) -> tuple[str, dict | None]:
    """Récupère les offres d'un assureur — utilisé en parallèle."""
    url = f"{BASE_URL}/app/tarif-animaux/{devis_id}/{slug}"
    session = requests.Session()
    session.headers.update(HEADERS)
    resp = None

    for attempt in range(1, 4):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            log.info(
                f"  [{slug}] tentative {attempt} - HTTP {resp.status_code} - "
                f"{len(resp.content)} bytes - {resp.text[:100]}"
            )
            if resp.status_code == 200 and resp.text.strip():
                parsed = resp.json()
                if not isinstance(parsed, dict):
                    if parsed == []:
                        log.warning(f"  [{slug}] reponse [] -> pas d'offre pour ce profil")
                        return slug, None
                    log.warning(f"  [{slug}] reponse non-dict inattendue, retry dans 10s...")
                    time.sleep(10)
                    continue
                nb = len(parsed.get("data") or [])
                if nb == 0:
                    rappel = parsed.get("rappel", 0)
                    devis = parsed.get("devis", 0)
                    if rappel or devis:
                        log.info(f"  [{slug}] 0 offre en ligne (rappel={rappel} devis={devis} -> contact commercial)")
                    else:
                        log.info(f"  [{slug}] 0 offre (profil exclu)")
                else:
                    log.info(f"  [{slug}] {nb} offre(s)")
                return slug, parsed
            else:
                log.warning(f"  [{slug}] reponse vide ou HTTP {resp.status_code}, retry dans 10s...")
                time.sleep(10)
        except RequestException as exc:
            log.error(f"  [{slug}] erreur reseau : {exc}")
            time.sleep(10)
        except ValueError as exc:
            body_preview = resp.text[:100] if resp is not None else ""
            log.error(f"  [{slug}] JSON invalide : {exc} - {body_preview}")
            time.sleep(10)

    log.warning(f"  [{slug}] aucune reponse valide apres 3 tentatives")
    return slug, None


def get_offers(session: requests.Session, devis_id: int, slugs: list) -> dict:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    log.info("  Attente initiale 10s pour le calcul des tarifs...")
    time.sleep(10)

    offers = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch_slug, devis_id, slug): slug for slug in slugs}
        for future in as_completed(futures, timeout=120):
            slug, data = future.result()
            offers[slug] = data

    return offers


def flatten_for_csv(profile: dict, devis_id: int, slug: str, offer_data, silent: bool = False) -> list[dict]:
    rows = []
    od = offer_data if isinstance(offer_data, dict) else {}

    base = {
        "devis_id": clean_cell(devis_id),
        "type_animal": clean_cell(profile.get("type_animal", "")),
        "race": clean_cell(profile.get("race_un", "")),
        "sexe_animal": clean_cell(profile.get("sexe_animal", "")),
        "animal_date_naissance": clean_cell(profile.get("animal_date_naissance", "")),
        "code_postal": clean_cell(profile.get("cp", "")),
        "ville": clean_cell(profile.get("ville", "")),
        "assureur": clean_cell(od.get("Nom_compagne") or slug),
        "promo": clean_cell(od.get("promo_text", "")),
    }

    items = od.get("data") or []

    if not items:
        rows.append(
            {
                **base,
                "formule": "AUCUNE OFFRE",
                "tarif_mensuel": "",
                "tarif_annuel": "",
                "plafond": "",
                "franchise": "",
                "chirurgicaux_accident_pct": "",
                "medicaux_accident_pct": "",
                "chirurgicaux_maladie_pct": "",
                "medicaux_maladie_pct": "",
            }
        )
        return rows

    for item in items:
        if not isinstance(item, dict):
            continue
        g = item.get("garanties", {})
        tarif = item.get("tarif", "")
        try:
            tarif_float = float(str(tarif).replace(",", ".")) if tarif not in ("", None) else ""
            tarif_annuel = round(tarif_float * 12, 2) if tarif_float != "" else ""
        except (ValueError, TypeError):
            tarif_float = ""
            tarif_annuel = ""

        rows.append(
            {
                **base,
                "formule": clean_cell(item.get("formule_affichage") or item.get("formule", "")),
                "tarif_mensuel": clean_cell(tarif_float),
                "tarif_annuel": clean_cell(tarif_annuel),
                "plafond": clean_cell(g.get("Plafond", "")),
                "franchise": clean_cell(g.get("Franchise", "")),
                "chirurgicaux_accident_pct": clean_cell(g.get("Chirurgicaux_Accident", "")),
                "medicaux_accident_pct": clean_cell(g.get("Medicaux_Accident", "")),
                "chirurgicaux_maladie_pct": clean_cell(g.get("Chirurgicaux_Maladie", "")),
                "medicaux_maladie_pct": clean_cell(g.get("Medicaux_Maladie", "")),
            }
        )

    return rows


def save_results(results: list, output_dir: Path) -> None:
    output_dir.mkdir(exist_ok=True)

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    log.info(f"JSON sauvegarde -> {RESULTS_PATH}")

    csv_rows = []
    for result in results:
        if not result.get("devis_id"):
            continue
        for slug, offer_data in result.get("offers", {}).items():
            csv_rows.extend(
                flatten_for_csv(result["profile"], result["devis_id"], slug, offer_data, silent=True)
            )

    if not csv_rows:
        log.warning("Aucune ligne CSV a exporter")
        return

    csv_path = output_dir / "results.csv"
    fieldnames = list(csv_rows[0].keys())
    with open(csv_path, "w", newline="", encoding=CSV_ENCODING) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=CSV_DELIMITER)
        writer.writeheader()
        writer.writerows(csv_rows)
    log.info(f"CSV sauvegarde -> {csv_path} ({len(csv_rows)} lignes)")

    export_xlsx(csv_rows, output_dir)


def run(n_profiles: int = DEFAULT_N_PROFILES, resume: bool = True, deterministic: bool = False):
    setup_logging(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(exist_ok=True)

    if resume:
        results = load_existing_results(OUTPUT_DIR)
    else:
        archive_previous_results(OUTPUT_DIR)
        results = []

    pending_profiles = prepare_profiles(n_profiles, OUTPUT_DIR, resume=resume, deterministic=deterministic)
    total_profiles = len(results) + len(pending_profiles)
    log.info(f"=== Demarrage Animaux : {total_profiles} profil(s) a traiter ===")

    session = get_session()

    for index, profile in enumerate(list(pending_profiles), start=len(results) + 1):
        log.info(f"--- Profil {index}/{total_profiles} ---")

        session = _refresh_session_if_needed(session)
        devis_id, slugs = create_lead(session, profile)
        result = {"profile": profile, "devis_id": devis_id, "offers": {}}

        if devis_id and slugs:
            result["offers"] = get_offers(session, devis_id, slugs)

        results.append(result)
        pending_profiles.pop(0)
        save_pending_profiles(pending_profiles)
        save_results(results, OUTPUT_DIR)

        if pending_profiles:
            delay = random.uniform(*DELAY_BETWEEN_PROFILES)
            log.info(f"Pause {delay:.0f}s avant le prochain profil...")
            time.sleep(delay)

    log.info(f"=== Termine : {len(results)} profil(s) traite(s) ===")
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scraper Animaux mongustave")
    parser.add_argument("--n", type=int, default=DEFAULT_N_PROFILES, help="Nombre de profils aleatoires")
    parser.add_argument("--no-resume", action="store_true", help="Repart de zero (archive les resultats precedents)")
    parser.add_argument("--deterministic", action="store_true", help="Mode diagnostic: profils deterministes")
    args = parser.parse_args()

    run(n_profiles=args.n, resume=not args.no_resume, deterministic=args.deterministic)
