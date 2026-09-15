# Documentation — Comment fonctionne le scraping de Mon Gustave

> Objectif de ce document : décrire **précisément** la méthode de scraping utilisée
> par ce projet, et **cartographier les faiblesses du site** qui la rendent possible.
> Il sert de base au volet défensif : une fois qu'on sait par où ça passe, on saura
> quoi renforcer côté site.

Cible : `https://www.mongustave.fr` — comparateur d'assurance (Santé, MRH, Animaux).

---

## 1. Vue d'ensemble

Le site est une **SPA (single page application)** : le formulaire de devis est une
interface JavaScript qui, en réalité, ne fait que discuter avec une petite série
d'**endpoints API JSON internes**. Le scraper **n'automatise pas le navigateur** ni
ne parse du HTML : il **parle directement à l'API**, exactement comme le fait le
front-end du site, en rejouant les mêmes requêtes.

C'est la nature même du projet : on n'extrait pas du *contenu* (HTML → texte), on
**pilote un flux fonctionnel** formulaire → API → tarifs.

Trois produits, trois scrapers quasi identiques (`Sante/`, `MRH/`, `Animaux/`),
partageant le même patron.

---

## 2. Le flux en 3 étapes

Pour chaque « profil » (un assuré fictif généré), le scraper enchaîne :

### Étape 1 — Ouvrir une session et récupérer le jeton anti-CSRF

```
GET /app/sante/            (ou /app/mrh/ , /app/animaux)
```

- Un simple `GET` sur la page produit. Le serveur répond en posant un cookie de
  session **et** un cookie `XSRF-TOKEN`.
- Le scraper lit `XSRF-TOKEN` dans les cookies, le décode (`urllib.parse.unquote`)
  et le **recopie dans l'en-tête `x-xsrf-token`** des requêtes suivantes.
- C'est **la seule barrière d'entrée**, et elle est franchie automatiquement :
  le token est distribué à n'importe quel visiteur anonyme sans authentification.

Code : `Sante/scraper.py` → `get_session()`.

### Étape 2 — Créer un lead (soumettre le formulaire)

```
POST /app/api/sante/insert-lead          (Santé)
POST /app/api/mrh/insert-lead-v2         (MRH)
POST /app/api/animaux/insert-lead        (Animaux)
```

- Corps = **un gros JSON** reproduisant tous les champs du formulaire (âge, régime,
  code postal, garanties souhaitées, conjoint, enfants, coordonnées de contact…).
- Les coordonnées « client » (nom, prénom, email, téléphone) sont **entièrement
  fabriquées** avec la bibliothèque Faker — le site les accepte sans vérification.
- Réponse JSON → contient `lead.id` (l'identifiant du devis) et `clients_sante`
  (la liste des slugs d'assureurs à interroger).

Code : `create_lead()`.

### Étape 3 — Récupérer les tarifs, assureur par assureur

```
GET /app/tarif/{devis_id}/{slug}          (Santé)
GET /app/tarif-mrh/{devis_id}/{slug}      (MRH)
GET /app/tarif-animaux/{devis_id}/{slug}  (Animaux)
```

- Le back-end calcule les tarifs de manière asynchrone. Le scraper **attend ~5 s**
  puis interroge chaque assureur.
- Les assureurs sont interrogés **en parallèle** (`ThreadPoolExecutor`, 3 workers),
  avec **retry ×3** en cas de réponse vide.
- Chaque réponse JSON = les formules et leurs prix pour cet assureur, aplaties en
  lignes CSV/XLSX.

Code : `get_offers()` + `fetch_slug()`.

### Schéma

```
  ┌─ GET /app/sante/ ───────────────► cookie session + XSRF-TOKEN
  │
  ├─ POST /app/api/sante/insert-lead ► { lead.id, [slugs assureurs] }
  │      (profil JSON fabriqué)
  │
  └─ GET /app/tarif/{id}/{slug} ×N ──► { formules, tarifs, garanties }
         (en parallèle, retry ×3)
```

---

## 3. Détails techniques exploités

| Élément | Ce que fait le scraper |
|---|---|
| **En-têtes HTTP** | Copie fidèle d'un vrai Chrome : `user-agent`, `sec-ch-ua`, `referer`, `origin`, `x-requested-with: XMLHttpRequest`. Le site ne peut pas distinguer le scraper d'un navigateur réel sur la seule base des en-têtes. |
| **Session** | Réutilisée pour tout le run ; renouvelée seulement si le `XSRF-TOKEN` disparaît (`_refresh_session_if_needed`). |
| **Cadence** | Délai aléatoire entre profils, volontairement réduit au fil du projet : Santé `(0-1s)`, MRH `(5-10s)`, Animaux `(15-45s)`. Attente de calcul serveur réduite de 10 s → 5 s. |
| **Robustesse** | Retry ×3, reprise sur crash (`pending_profiles.json` + `results.json`), archivage automatique des runs précédents. |
| **Volume observé** | Plusieurs milliers de leads créés (16 195 lignes sur un seul run senior), **sans jamais rencontrer 429, CAPTCHA, ni blocage IP**. |

---

## 4. Faiblesses du site (surface d'attaque)

C'est le cœur du sujet. Classées de la plus structurante à la plus fine.

### 4.1 — API interne exposée et non authentifiée ⚠️ **critique**
Les trois endpoints (`insert-lead`, `tarif/*`) sont accessibles à tout visiteur
anonyme. Aucune authentification, aucune clé d'API. Le front-end les appelle « en
clair », donc n'importe qui peut les rejouer. **C'est ce qui rend tout le reste
possible.**

### 4.2 — Jeton XSRF distribué librement
Le `XSRF-TOKEN` est censé prouver qu'une requête vient d'une vraie page. Mais il
est **remis à tout GET anonyme** sur la page produit, sans lien avec une session
authentifiée. Il ne protège donc que contre le CSRF « aveugle », **pas contre un
client qui va le chercher lui-même** — ce que fait le scraper en une ligne.

### 4.3 — Aucune limitation de débit (rate limiting)
Le point le plus exploité. Des milliers de `insert-lead` en rafale, avec des
délais tombés jusqu'à 0-1 s, **n'ont déclenché aucun 429 ni ralentissement**. Le
site ne compte visiblement pas les requêtes par IP / session / empreinte.

### 4.4 — Aucune détection de bot
Pas de CAPTCHA, pas de challenge JS, pas d'analyse comportementale, pas
d'empreinte navigateur (canvas, timing, ordre des en-têtes). Un `requests.Session`
Python passe pour un Chrome sans effort.

### 4.5 — Données de lead non validées
Nom, prénom, email et téléphone sont **fabriqués** (Faker) et acceptés tels quels.
Conséquences : (a) le scraping est indétectable via la qualité des leads ;
(b) le site **génère de faux leads en masse** — pollution de la base commerciale,
potentiel coût réel si ces leads sont refacturés aux assureurs partenaires.

### 4.6 — Identifiants de devis séquentiels → IDOR ⚠️ **confirmé (gravité moyenne)**
`lead.id` est un entier **incrémental** renvoyé en clair. Test réalisé le
2026-08-27 : en interrogeant `/app/tarif/{id}/{slug}` sur des ids **non créés par
nous** (id−1, id−2, id−137), le serveur répond `HTTP 200` avec **5 offres à des
tarifs différents des nôtres** → **aucun contrôle de propriété**. N'importe qui
peut lire le devis de n'importe quel utilisateur en énumérant les ids.
**Portée limitée** : cet endpoint expose les **tarifs calculés + métadonnées
assureur** (nom compagnie, orias, rappel), mais **pas** le nom/email/téléphone du
prospect (scan PII = 0 sur les réponses testées).

**Recherche d'autres vecteurs (2026-08-27) — rien d'autre exposé en anonyme :**
analyse du JavaScript front + tests sur notre propre lead.
- Le pré-remplissage « Recalculer » ne passe **pas** par le serveur : le lead est
  mis en `localStorage` (`lead_sante`) puis relu par la SPA (`?update_profile=true`).
  Aucun endpoint serveur ne renvoie le PII d'un lead par son id.
- Les données personnelles ne sont accessibles que via `espace-client/monCompte/
  getSante/{id}`, **zone authentifiée** (renvoie la coquille SPA en anonyme).
- **Conclusion : l'IDOR sur `/tarif` reste la seule fuite, limitée aux tarifs.**
  L'identité des prospects n'est pas récupérable par énumération.

**Généralisation aux autres produits (2026-08-27) — IDOR structurel, pas
propre à la Santé :** test rejoué sur MRH et Animaux.
- **MRH** (`/app/tarif-mrh/{id}/{slug}`) : ids voisins non créés → `HTTP 200` +
  4 offres → aucun contrôle d'accès. Séquence d'ids **séparée** (~83 000).
- **Animaux** (`/app/tarif-animaux/{id}/{slug}`) : voisin → 3 offres, tarifs
  différents des nôtres → devis d'un autre profil lu. Aucun PII.
- **Découverte** : Santé et Animaux **partagent le même compteur d'ids global**
  (~1 711 000) et l'endpoint tarif **ne vérifie pas** que le produit du lead
  correspond au slug demandé.
- Non testés faute de générateur de payload : Auto, Emprunteur, Crédit conso —
  mais ils suivent le même patron `/app/tarif-*`, donc vraisemblablement affectés.

**Conclusion : le défaut d'autorisation touche toute la famille d'endpoints
`/app/tarif*`, sur tous les produits, et se limite aux tarifs (jamais de PII).**

**Observations annexes (dans le bundle JS) :**
- Mécanisme de vérification SMS présent mais **non appliqué** : `POST api/
  validate-sms-cipher` / `re-send-sms-cipher` (token `SHA512(email+telephone)`).
  Défense latente activable pour contrer les faux leads (cf. 4.5).
- Clé d'API tierce **en clair** côté client : `apileadmarket.wee-do-it.net/api/
  search-tag?key=…` (marketplace de leads). Non sondée (cible externe).

### 4.7 — Logique tarifaire reconstituable
Le tarif est **déterministe** et dépend d'un petit nombre de variables (âge,
qui-assurer, régime, formule). Le projet a montré qu'on peut **reconstruire la
grille tarifaire par régression** (R² ≈ 0,92–0,96). Autrement dit, l'API expose
assez d'information pour **répliquer le moteur de prix d'un partenaire**.

---

## 5. Ce que le site *fait déjà* (le peu de défenses présentes)

- Jeton XSRF requis (mais trivialement contournable, cf. 4.2).
- Certains assureurs Santé renvoient « 0 offre en ligne » et basculent en rappel
  commercial — non pas une protection, mais cela **limite ce qui est scrapable** en
  API pure pour ces partenaires.
- Rejet des numéros surtaxés (`SURTAXED_PHONE`) — validation cosmétique.

---

## 6. Pistes de renforcement (préparation du volet défensif)

À traiter dans un document séparé, mais listées ici en regard des faiblesses :

| Faiblesse | Contre-mesure envisageable |
|---|---|
| 4.3 Pas de rate limit | Limitation par IP + par empreinte de session (seuils sur `insert-lead`). |
| 4.4 Pas de détection bot | CAPTCHA invisible / challenge JS sur `insert-lead`, analyse comportementale. |
| 4.2 XSRF trop permissif | Lier le token à une session horodatée + preuve d'exécution JS (token à durée de vie courte, usage unique). |
| 4.5 Leads non validés | Validation email/téléphone (OTP), scoring de cohérence des leads. |
| 4.6 IDs séquentiels | IDs non devinables (UUID) + contrôle d'autorisation sur `/tarif/{id}`. |
| 4.7 Grille reconstituable | Bruit/arrondi, plafonnement du nombre de simulations, obfuscation du calcul. |
| 4.1 API exposée | Signature de requête côté client, quotas, WAF. |

---

*Document généré à partir du code (`Sante/`, `MRH/`, `Animaux/`) et du `JOURNAL.md`.
Aucune donnée réelle d'utilisateur n'est manipulée : tous les profils sont fictifs.*
