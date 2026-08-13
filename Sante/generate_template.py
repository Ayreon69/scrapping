from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

wb = Workbook()
ws = wb.active
ws.title = "Profils"
ws_lists = wb.create_sheet("Listes")

# ---------------------------------------------------------------------------
# Mapping profession : label affiche -> (profession, autre_profession)
# ---------------------------------------------------------------------------
PROFESSION_LABELS = [
    "Salarie cadre",
    "Fonction publique d etat",
    "Fonction publique territoriale",
    "Fonction publique hospitaliere",
    "Artisan",
    "Commercant",
    "Profession liberale",
    "Chef d entreprise",
    "Enseignant",
    "Agriculteur",
    "Exploitant agricole",
    "VRP",
    "Visiteur medical",
    "Sans profession",
    "Etudiant",
    "Retraite",
    "En recherche d emploi",
]

PROFESSION_MAP = {
    "Salarie cadre":                ("salarie",               "salarie_cadre"),
    "Fonction publique d etat":     ("salarie",               "Fonction_publique_d_etat"),
    "Fonction publique territoriale": ("salarie",             "Fonction_publique_territoriale"),
    "Fonction publique hospitaliere": ("salarie",             "Fonction_publique_hospitaliere"),
    "Artisan":                      ("salarie",               "artisan"),
    "Commercant":                   ("salarie",               "commercant"),
    "Profession liberale":          ("salarie",               "profession_liberale"),
    "Chef d entreprise":            ("salarie",               "chef_d_entreprise"),
    "Enseignant":                   ("salarie",               "enseignant"),
    "Agriculteur":                  ("salarie",               "agriculteur"),
    "Exploitant agricole":          ("salarie",               "exploitant_agricole"),
    "VRP":                          ("salarie",               "VRP"),
    "Visiteur medical":             ("salarie",               "visiteur_medical"),
    "Sans profession":              ("salarie",               "sans_profession"),
    "Etudiant":                     ("etudiant",              "etudiant"),
    "Retraite":                     ("retraite",              "retraite"),
    "En recherche d emploi":        ("en_recherche_d_emploi", "en_recherche_d_emploi"),
}

# ---------------------------------------------------------------------------
# Listes deroulantes
# ---------------------------------------------------------------------------
LISTS = {
    "Qui assurer": [
        "Moi seul",
        "Mon couple (sans enfant)",
        "Moi et mes enfants (sans conjoint)",
        "Mon couple et mes enfants",
    ],
    "Regime SS":         ["General", "TNS (independant)", "Agricole", "Alsace-Moselle"],
    "Regime conjoint":   ["General", "TNS (independant)", "Agricole", "Alsace-Moselle"],
    "Profession":        PROFESSION_LABELS,
    "Soins medicaux":    ["Faible", "Moyen", "Fort", "Max"],
    "Hospitalisation":   ["Faible", "Moyen", "Fort", "Max"],
    "Optique":           ["Faible", "Moyen", "Fort", "Max"],
    "Dentaire":          ["Faible", "Moyen", "Fort", "Max"],
    "Auditives":         ["Faible", "Moyen", "Fort", "Max"],
    "Mode remboursement": ["Medecin traitant (conseille)", "Securite sociale seule", "Acces libre", "Personnalise"],
}

list_col_map = {}
for col_idx, (field, values) in enumerate(LISTS.items(), start=1):
    col_letter = get_column_letter(col_idx)
    list_col_map[field] = (col_letter, len(values))
    ws_lists.cell(row=1, column=col_idx, value=field).font = Font(bold=True)
    for row_idx, val in enumerate(values, start=2):
        ws_lists.cell(row=row_idx, column=col_idx, value=val)

# ---------------------------------------------------------------------------
# Definition des colonnes
# (header_affiche, cle_interne, has_dropdown, commentaire)
# ---------------------------------------------------------------------------
COLUMNS = [
    # Bloc 1 : Qui assurer
    ("Qui assurer ?",               "qui_assurer",              True,
     "Moi seul / Mon couple / Moi et mes enfants / Mon couple et mes enfants"),

    # Bloc 2 : Assure principal
    ("Date de naissance",           "date_naissance",           False,
     "Format JJ/MM/AAAA  ex: 15/06/1985"),
    ("Regime secu",                 "regime",                   True,
     "Regime de securite sociale de l assure principal"),
    ("Profession",                  "profession_label",         True,
     "Choisir dans la liste"),

    # Bloc 3 : Conjoint (laisser vide si pas de conjoint)
    ("Date naissance conjoint",     "conjoint_date_naissance",  False,
     "Laisser vide si pas de conjoint  -  Format JJ/MM/AAAA"),
    ("Regime secu conjoint",        "regime_conjoint",          True,
     "Laisser vide si pas de conjoint"),

    # Bloc 4 : Enfants (laisser vide si pas d enfant)
    ("Date naissance enfant 1",     "date_naissance_enfant_1",  False,
     "Laisser vide si pas d enfant  -  Format JJ/MM/AAAA"),
    ("Date naissance enfant 2",     "date_naissance_enfant_2",  False,
     "Laisser vide si pas d enfant"),
    ("Date naissance enfant 3",     "date_naissance_enfant_3",  False,
     "Laisser vide si pas d enfant"),

    # Bloc 5 : Garanties souhaitees
    ("Soins medicaux",              "soins_medicaux",           True,
     "Niveau de remboursement souhaite pour les soins courants"),
    ("Hospitalisation",             "hospitalisation",          True,
     "Niveau de remboursement souhaite pour l hospitalisation"),
    ("Optique",                     "optique",                  True,
     "Niveau de remboursement souhaite pour l optique"),
    ("Dentaire",                    "dentaire",                 True,
     "Niveau de remboursement souhaite pour le dentaire"),
    ("Auditives",                   "auditives",                True,
     "Niveau de remboursement souhaite pour les aides auditives"),
    ("Mode remboursement",          "mode_sois",                True,
     "Medecin traitant conseille dans la plupart des cas"),

    # Bloc 6 : Localisation
    ("Code postal",                 "cp",                       False,
     "Ex: 75001  -  Laisser vide = Paris par defaut"),
    ("Ville",                       "ville",                    False,
     "Ex: Paris  -  Laisser vide = Paris par defaut"),
]

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
# Couleurs par bloc
BLOC_COLORS = {
    "qui_assurer":              "1A5276",  # bleu fonce
    "date_naissance":           "1F618D",  # bleu
    "regime":                   "1F618D",
    "profession_label":         "1F618D",
    "conjoint_date_naissance":  "117A65",  # vert
    "regime_conjoint":          "117A65",
    "date_naissance_enfant_1":  "7D6608",  # ocre
    "date_naissance_enfant_2":  "7D6608",
    "date_naissance_enfant_3":  "7D6608",
    "soins_medicaux":           "6E2F84",  # violet
    "hospitalisation":          "6E2F84",
    "optique":                  "6E2F84",
    "dentaire":                 "6E2F84",
    "auditives":                "6E2F84",
    "mode_sois":                "6E2F84",
    "cp":                       "784212",  # marron
    "ville":                    "784212",
}

CELL_DROPDOWN_ALPHA = "D6EAF8"
CELL_FREE_ALPHA     = "F2F3F4"

# Couleurs de fond cellule par bloc
BLOC_CELL_COLORS = {
    "qui_assurer":              "EBF5FB",
    "date_naissance":           "EBF5FB",
    "regime":                   "EBF5FB",
    "profession_label":         "EBF5FB",
    "conjoint_date_naissance":  "E8F8F5",
    "regime_conjoint":          "E8F8F5",
    "date_naissance_enfant_1":  "FEFBD8",
    "date_naissance_enfant_2":  "FEFBD8",
    "date_naissance_enfant_3":  "FEFBD8",
    "soins_medicaux":           "F5EEF8",
    "hospitalisation":          "F5EEF8",
    "optique":                  "F5EEF8",
    "dentaire":                 "F5EEF8",
    "auditives":                "F5EEF8",
    "mode_sois":                "F5EEF8",
    "cp":                       "FAF0E6",
    "ville":                    "FAF0E6",
}

thin  = Side(style="thin",   color="BBBBBB")
thick = Side(style="medium", color="888888")
border_normal = Border(left=thin, right=thin, top=thin, bottom=thin)

NB_ROWS = 50

# ---------------------------------------------------------------------------
# En-tetes ligne 1 : blocs colores
# ---------------------------------------------------------------------------
BLOC_LABELS = [
    ("A1:A1",  "QUI ASSURER ?",       "1A5276"),
    ("B1:D1",  "ASSURE PRINCIPAL",    "1F618D"),
    ("E1:F1",  "CONJOINT",            "117A65"),
    ("G1:I1",  "ENFANTS",             "7D6608"),
    ("J1:P1",  "GARANTIES",           "6E2F84"),
    ("Q1:R1",  "LOCALISATION",        "784212"),
]

ws.row_dimensions[1].height = 22
for cell_range, label, color in BLOC_LABELS:
    ws.merge_cells(cell_range)
    first_cell = ws[cell_range.split(":")[0]]
    first_cell.value = label
    first_cell.fill = PatternFill("solid", fgColor=color)
    first_cell.font = Font(color="FFFFFF", bold=True, size=9)
    first_cell.alignment = Alignment(horizontal="center", vertical="center")

# ---------------------------------------------------------------------------
# En-tetes ligne 2 : noms des colonnes
# ---------------------------------------------------------------------------
ws.row_dimensions[2].height = 40
for col_idx, (header, field, has_dd, comment) in enumerate(COLUMNS, start=1):
    color = BLOC_COLORS.get(field, "555555")
    cell = ws.cell(row=2, column=col_idx, value=header)
    cell.fill      = PatternFill("solid", fgColor=color)
    cell.font      = Font(color="FFFFFF", bold=True, size=9)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border    = border_normal
    cell.comment   = Comment(comment, "Guide")

# ---------------------------------------------------------------------------
# Cellules de donnees (lignes 3+)
# ---------------------------------------------------------------------------
for row in range(3, NB_ROWS + 3):
    ws.row_dimensions[row].height = 20
    for col_idx, (header, field, has_dd, _) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=row, column=col_idx)
        cell.font      = Font(size=10)
        cell.alignment = Alignment(horizontal="left", vertical="center")
        cell.border    = border_normal
        bg = BLOC_CELL_COLORS.get(field, "FFFFFF")
        cell.fill = PatternFill("solid", fgColor=bg)

# ---------------------------------------------------------------------------
# Validations deroulantes
# ---------------------------------------------------------------------------
# Mapping colonne header -> cle liste
HEADER_TO_LIST = {
    "qui_assurer":              "Qui assurer",
    "regime":                   "Regime SS",
    "regime_conjoint":          "Regime conjoint",
    "profession_label":         "Profession",
    "soins_medicaux":           "Soins medicaux",
    "hospitalisation":          "Hospitalisation",
    "optique":                  "Optique",
    "dentaire":                 "Dentaire",
    "auditives":                "Auditives",
    "mode_sois":                "Mode remboursement",
}

for col_idx, (header, field, has_dd, _) in enumerate(COLUMNS, start=1):
    list_key = HEADER_TO_LIST.get(field)
    if has_dd and list_key and list_key in list_col_map:
        col_letter, nb_vals = list_col_map[list_key]
        formula = "Listes!${}$2:${}${}".format(col_letter, col_letter, nb_vals + 1)
        dv = DataValidation(
            type="list",
            formula1=formula,
            allow_blank=True,
            showErrorMessage=True,
            errorTitle="Valeur invalide",
            error="Choisissez une valeur dans la liste deroulante.",
        )
        col_data = get_column_letter(col_idx)
        dv.sqref = "{}3:{}{}".format(col_data, col_data, NB_ROWS + 2)
        ws.add_data_validation(dv)

# ---------------------------------------------------------------------------
# Largeurs colonnes
# ---------------------------------------------------------------------------
WIDTHS = {
    "qui_assurer": 28,
    "date_naissance": 20, "regime": 22, "profession_label": 26,
    "conjoint_date_naissance": 22, "regime_conjoint": 22,
    "date_naissance_enfant_1": 22, "date_naissance_enfant_2": 22, "date_naissance_enfant_3": 22,
    "soins_medicaux": 14, "hospitalisation": 14, "optique": 12,
    "dentaire": 12, "auditives": 12, "mode_sois": 26,
    "cp": 12, "ville": 16,
}
for col_idx, (header, field, _, _) in enumerate(COLUMNS, start=1):
    ws.column_dimensions[get_column_letter(col_idx)].width = WIDTHS.get(field, 15)

ws.freeze_panes = "A3"

# ---------------------------------------------------------------------------
# Legende
# ---------------------------------------------------------------------------
ws_leg = wb.create_sheet("Legende")
ws_leg.column_dimensions["A"].width = 30
ws_leg.column_dimensions["B"].width = 65

legend = [
    ("GUIDE DE REMPLISSAGE",    ""),
    ("",                        ""),
    ("Couleur de la colonne",   "Section du formulaire"),
    ("Bleu",                    "Informations sur l assure principal"),
    ("Vert",                    "Informations sur le conjoint - laisser vide si pas de conjoint"),
    ("Ocre / jaune",            "Dates de naissance des enfants - laisser vide si pas d enfant"),
    ("Violet",                  "Niveaux de garantie souhaites"),
    ("Marron",                  "Localisation"),
    ("",                        ""),
    ("REGLES IMPORTANTES",      ""),
    ("Qui assurer ?",           "Selectionner dans la liste - determine automatiquement si conjoint / enfants"),
    ("Dates",                   "Format JJ/MM/AAAA  ex: 15/06/1985"),
    ("Code postal",             "Laisser vide = Paris (75001) par defaut"),
    ("Champs facultatifs",      "Nom, prenom, email, telephone : laisser vide = generes automatiquement"),
    ("",                        ""),
    ("LANCER LE SCRAPING",      "python scraper.py --from-excel profils_template.xlsx --no-resume"),
]

for r_idx, (a, b) in enumerate(legend, start=1):
    ca = ws_leg.cell(row=r_idx, column=1, value=a)
    cb = ws_leg.cell(row=r_idx, column=2, value=b)
    if a in ("GUIDE DE REMPLISSAGE", "REGLES IMPORTANTES", "LANCER LE SCRAPING"):
        ca.font = Font(bold=True, size=11)
    elif a == "Couleur de la colonne":
        ca.font = Font(bold=True)
        cb.font = Font(bold=True)

ws_lists.sheet_state = "hidden"

wb.save("profils_template.xlsx")
print("Fichier cree : profils_template.xlsx")
