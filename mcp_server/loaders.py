"""Charge les modules scraper.py de Sante/MRH/Animaux sous des noms isolés.

Les trois dossiers produit contiennent chacun un config.py/profiles.py/scraper.py
qui s'importent entre eux par nom simple (`from config import ...`). Pour les
charger tous les trois dans le même process sans collision, on ajoute
temporairement le dossier du produit en tête de sys.path le temps de l'import,
puis on le retire.
"""

import importlib
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent

PRODUCT_DIRS = {
    "sante": ROOT / "Sante",
    "mrh": ROOT / "MRH",
    "animaux": ROOT / "Animaux",
}

_cache: dict[str, ModuleType] = {}


def load_product_scraper(product: str) -> ModuleType:
    """Importe scraper.py (et ses dependances config/profiles) pour un produit donne."""
    if product in _cache:
        return _cache[product]

    product_dir = PRODUCT_DIRS[product]
    if not product_dir.is_dir():
        raise FileNotFoundError(f"Dossier produit introuvable : {product_dir}")

    # Purge les modules "generiques" (config, profiles, scraper, load_excel)
    # laisses par un chargement precedent d'un autre produit.
    for name in ("config", "profiles", "scraper", "load_excel"):
        sys.modules.pop(name, None)

    sys.path.insert(0, str(product_dir))
    try:
        scraper = importlib.import_module("scraper")
        importlib.reload(scraper)
    finally:
        sys.path.remove(str(product_dir))

    _cache[product] = scraper
    return scraper
