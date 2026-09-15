# Plan d'audit — recherche de fuite de données (PII)

> Objectif : déterminer, preuve à l'appui, **si des données personnelles**
> (nom, email, téléphone, adresse, et pour les produits financiers : revenus,
> capital, données de santé) **fuient** de l'écosystème mongustave / wee-do-it,
> et documenter chaque défaut avec une reproduction bornée.
>
> Cadre : mandat / site propre. **wee-do-it.net = mongustave (même entité
> juridique)** — le mandat couvre donc les deux domaines.

---

## Principe éthique directeur (s'applique à TOUS les axes)

**Ne jamais lire, stocker ni exfiltrer le PII d'un vrai prospect.**

Prouver un défaut d'autorisation ne nécessite pas de voler la donnée d'un tiers.
Méthode : on crée **nos propres** leads / comptes de test (données Faker), on
note leurs `id`, et on démontre l'accès non autorisé **en lisant uniquement des
id qu'on a soi-même créés depuis un autre compte / une session anonyme**. Le
défaut est prouvé (« la session X lit la ressource de la session Y sans
contrôle »), sans qu'aucune donnée réelle ne soit consultée.

Si un id voisin non créé par nous renvoie du PII, on **constate le fait**
(« HTTP 200 + champs PII présents »), on **ne journalise pas** le contenu, et on
consigne seulement : endpoint, statut, types de champs exposés, nombre.

---

## Axe A — Cartographie exhaustive de la surface PII (PASSIF)

**But :** inventaire complet des endpoints touchant au PII, au-delà du flux
devis déjà connu. Base de tous les tests actifs suivants.

**Source :** bundle JS déjà capturé localement
(`Animaux/Pages_Devis/..._files/*.js`), plus captures à compléter pour
Santé/MRH/produits financiers si absentes.

**À extraire :**
- Toute route `espace-client/*`, `monCompte/*`, `getSante/getMrh/getAnimaux/...`
- Tout `POST` dont le corps contient `email` / `telephone` / `nom` / `adresse`
- Endpoints SMS : `validate-sms-cipher`, `re-send-sms-cipher`
- Tous les appels vers un domaine tiers (dont `apileadmarket.wee-do-it.net`)
- Clés / tokens / secrets en clair dans le JS

**Livrable :** `SURFACE_PII.md` — tableau { endpoint, méthode, champs PII,
auth requise: oui/non/à tester }.

**Risque :** nul (fichiers locaux). **Requête active : aucune.**

---

## Axe B — IDOR en zone authentifiée (test le PLUS important)

**Hypothèse :** `espace-client/monCompte/getSante/{id}` (et équivalents) renvoie
la coquille SPA en anonyme, mais **avec une session client authentifiée**,
peut-on lire le `{id}` d'un **autre** utilisateur → PII complète.

**Méthode bornée :**
1. Créer 2 comptes de test à nous (compte A, compte B), données Faker.
2. Depuis chaque compte, créer un devis → noter `id_A`, `id_B`.
3. Authentifié comme A, appeler `getSante/{id_B}`.
   - Si 200 + données de B → **IDOR authentifié confirmé** (les deux ids sont à
     nous, aucune donnée tierce lue).
4. Ne tester des id voisins non créés par nous **que** pour constater le statut
   HTTP (pas le contenu), cf. principe éthique.

**Gravité si confirmé :** critique — fuite PII complète, pas juste tarifs.

**Risque :** modéré (crée comptes + leads réels sur site sous mandat).

---

## Axe C — Étendre l'IDOR tarif aux produits financiers

**Cibles :** Auto, Emprunteur, Crédit conso — non testés faute de payload.
Emprunteur/Crédit sont les plus sensibles (revenus, capital, santé emprunteur).

**Méthode :**
1. Reverse des payloads `insert-lead` de ces produits (via capture réseau du
   formulaire réel, comme fait pour Santé/MRH/Animaux).
2. Ajouter un outil MCP par produit (réutilise `mcp_server/`).
3. Confirmer l'IDOR `/app/tarif-*/{id}/{slug}` sur id auto-créés.
4. **Clé :** inspecter la réponse tarif — expose-t-elle plus que des tarifs ?
   (revenu, capital, montant emprunté, état de santé déclaré ?)

**Gravité si PII financière exposée :** critique.

**Risque :** modéré (leads réels, site sous mandat).

---

## Axe D — Marketplace leads `apileadmarket.wee-do-it.net`

**Contexte révisé :** wee-do-it = mongustave (même entité) → **couvert par le
mandat**. La clé API en clair côté client est donc leur **propre** secret
exposé, pas celui d'un tiers.

**Hypothèses à tester :**
- La clé `search-tag?key=…` permet-elle de **lister** des leads ? de les **lire** ?
- Si oui : identité des prospects + fait qu'ils sont revendus → fuite PII majeure
  + exposition d'un flux commercial.

**Méthode bornée :**
1. (Passif d'abord) documenter la clé, le flux, les paramètres depuis le JS.
2. (Actif) sonder l'API **uniquement** pour prouver le contrôle d'accès :
   requête minimale, et si elle retourne des leads, **constater volume + types
   de champs sans journaliser le PII réel**.
3. Chercher si nos propres leads de test y apparaissent (preuve de bout en bout
   sans lire de tiers).

**Gravité si la clé donne accès aux leads :** critique (la pire du lot).

**Risque :** élevé côté sensibilité même sous mandat — borne éthique stricte.

---

## Critères de preuve (pour chaque défaut)

Un défaut n'est « confirmé » que si on a :
- l'endpoint exact + méthode,
- une reproduction bornée aux id/comptes qu'on a créés,
- le statut HTTP + la **liste des types** de champs exposés (jamais les valeurs
  réelles d'un tiers),
- la distinction claire : anonyme vs authentifié, propre-ressource vs
  ressource-d'autrui.

## Livrables finaux
- `SURFACE_PII.md` (axe A)
- Mise à jour de `DOCUMENTATION_SCRAPING.md` §4.6 avec les résultats B/C/D
- Outils MCP supplémentaires (axe C) dans `mcp_server/`
- Section « fuite PII : confirmée / écartée » avec le niveau de preuve atteint

---

## Ordre d'exécution proposé
1. **Axe A** (passif, immédiat) → produit la carte.
2. **Axe C** (réutilise le MCP, borné) → étend un défaut déjà connu.
3. **Axe B** (nécessite comptes de test) → le test à plus forte valeur.
4. **Axe D** (le plus sensible) → en dernier, avec bornes strictes.
