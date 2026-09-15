# MCP mongustave-devis

Serveur MCP exposant l'API interne de mongustave.fr (Sante, MRH, Animaux),
en reutilisant directement `get_session` / `create_lead` / `get_offers`
des scrapers existants (`Sante/`, `MRH/`, `Animaux/`).

Contexte et faiblesses exploitees : voir `../DOCUMENTATION_SCRAPING.md`.

## Installation

```bash
pip install -r mcp_server/requirements.txt
```

## Outils exposes

- `obtenir_devis_sante(age, code_postal, ville, regime, profession, autre_profession, who_assure, age_conjoint, nb_enfants, niveau_garantie)`
- `obtenir_devis_mrh(age, code_postal, ville, type_habitation, surface_habitable, statut_resident, profession, nbr_adultes, nbr_enfants, capital_mobilier)`
- `obtenir_devis_animaux(type_animal, race, age_animal, sexe_animal, formule_souhaitee, age_proprietaire, code_postal, ville)`

Chacun soumet un profil (Faker/valeurs par defaut sur les champs non exposes)
au flux insert-lead + tarif de mongustave.fr, et retourne les offres brutes
par slug d'assureur.

## Lancer en local (stdio)

```bash
python mcp_server/server.py
```

## Configuration client (ex. Claude Code)

```json
{
  "mcpServers": {
    "mongustave-devis": {
      "command": "python",
      "args": ["C:/Projets/Scrapping_gustave/mcp_server/server.py"]
    }
  }
}
```

## Limites connues

- Chaque appel cree un vrai lead sur mongustave.fr (donnees de contact factices,
  cf. section 4.5 de `DOCUMENTATION_SCRAPING.md`) — a n'utiliser que dans un
  contexte de test/diagnostic autorise sur ce projet.
- Pas de gestion de rate limiting cote serveur MCP : un appel = un profil,
  pas de generation en masse.
