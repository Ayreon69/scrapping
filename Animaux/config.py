BASE_URL = "https://www.mongustave.fr"

SLUGS_ASSUREURS = [
    "ecaAnimaux",
    "GoodFlair",
    "lovys_animaux",
]

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "fr-FR,fr;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/json;charset=UTF-8",
    "origin": "https://www.mongustave.fr",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.mongustave.fr/app/animaux",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}

DELAY_BETWEEN_PROFILES = (15, 45)
REQUEST_TIMEOUT = 15

CSV_DELIMITER = ";"
CSV_ENCODING = "utf-8-sig"
EXPORT_DATE_FORMAT = "%d/%m/%Y"
DEFAULT_N_PROFILES = 5
ENABLE_XLSX_EXPORT = True

PROVENANCE = "Acces-direct_Mon Gustave Animaux.Ghalem_Visuel"
