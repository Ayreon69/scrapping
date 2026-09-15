# Surface PII — inventaire des endpoints (Axe A, passif)

> Produit de l'axe A du [PLAN_AUDIT_PII.md](PLAN_AUDIT_PII.md). Analyse **100 %
> passive** du bundle JS déjà capturé
> (`Animaux/Pages_Devis/..._files/app.js`), aucune requête active émise.
>
> But : lister **tous** les endpoints qui touchent au PII, au-delà du flux
> devis déjà connu, pour cibler les tests actifs (axes B, C, D).

Date d'analyse : 2026-09-15. Source principale : `app.js` (bundle Vue/webpack).

---

## 1. Endpoints « espace client » — lecture d'un lead par id ⚠️ candidats IDOR PII

Tous appelés en **`GET`**, l'id étant **concaténé en fin d'URL** (`.concat(n)`),
sans aucun paramètre d'autorisation côté client. L'auth repose uniquement sur le
**cookie de session** (`withCredentials`, pas de Bearer/JWT — voir §4). Le code
front ne fait que tester `status === 500` → aucune vérification de propriété
côté client.

| Endpoint | Méthode | Produit | Champs PII attendus | Auth |
|---|---|---|---|---|
| `espace-client/monCompte/getSante/{id}` | GET | Santé | profil complet du lead (identité + santé) | session |
| `espace-client/monCompte/getMrh/{id}` | GET | Habitation | identité + logement | session |
| `espace-client/monCompte/getAnimaux/{id}` | GET | Animaux | identité + animal | session |
| `espace-client/monCompte/getAuto/{id}` | GET | Auto | identité + véhicule/conducteur | session |
| `espace-client/monCompte/getEmprunteur/{id}` | GET | Emprunteur | identité + **revenus/capital/santé** | session |
| `espace-client/monCompte/getCreditConsoTarifs/{id}` | GET | Crédit conso | identité + **situation financière** | session |

**À tester (axe B)** : avec une session cliente légitime à nous, lire un `{id}`
créé par un **autre** de nos comptes → si 200 + données de l'autre compte, IDOR
PII authentifié confirmé. Les produits Emprunteur / Crédit conso sont les plus
sensibles (données financières, potentiellement de santé).

---

## 2. Pages front « Recalculer » — id de lead exposé en clair

Liens HTML (pas des API JSON) ouverts dans l'espace client, avec l'id du lead
directement dans l'URL :

| Pattern | Produit |
|---|---|
| `espace-client/sa/i/{leadSante.id}` | Santé |
| `espace-client/an/i/{leadAnimaux.id}` | Animaux |
| `espace-client/au/i/{id}` | Auto |
| `espace-client/em/i/{id}` | Emprunteur |
| `espace-client/mr/i/{id}` | Habitation |

Confirme que **l'id de lead est manipulé en clair côté front** (déjà connu :
ids séquentiels, cf. DOCUMENTATION_SCRAPING §4.6). Sert d'entrée pour énumérer
les ids à passer aux endpoints du §1.

---

## 3. Vérification SMS — token dérivable, pas un secret serveur

| Endpoint | Méthode | Corps |
|---|---|---|
| `api/validate-sms-cipher` | POST | `token = SHA512(email+telephone)`, `id`, `cipher = SHA1(code)`, `id_forms` |
| `api/re-send-sms-cipher` | POST | `token = SHA512(email+telephone)`, `id`, `id_forms` |

**Observation** : le `token` n'est **pas** un secret côté serveur — il est
calculé côté client à partir de `email + telephone`, deux valeurs que
l'appelant fournit lui-même. Il ne prouve donc rien sur l'identité de
l'appelant ; c'est un simple checksum du couple email/téléphone. Défense SMS
présente mais **non contraignante** en l'état.

---

## 4. Marketplace de leads tierce — clé « private » exposée en clair ⚠️

```
GET https://apileadmarket.wee-do-it.net/api/search-tag?key=<CLE>&nom_tag=<tag>
réponse : { isExistent: ... }
```

- Clé (base64 dans le bundle) : `c2VhcmNoX3RhZ19hcGlfbGVhZF9tYXJrZXRfcHJpdmF0ZV9kTDg1MkdOS3dJ`
- **Décodée** : `search_tag_api_lead_market_private_dL852GNKwI`
  → le mot **`private`** dans l'intitulé confirme un secret destiné au serveur,
  publié en clair dans le JavaScript front livré à tout visiteur.
- `wee-do-it.net = mongustave` (même entité juridique) → c'est **leur propre**
  secret exposé, couvert par le mandat.
- Usage vu côté front : vérifier l'existence d'un `nom_tag` (déduplication de
  leads ?). L'étendue réelle des droits de cette clé (lister / lire des leads ?)
  n'est **pas** déterminable en passif → à sonder en axe D, avec bornes strictes.

---

## 5. Mécanisme d'auth (déterminant pour l'axe B)

- **Aucun** Bearer / JWT / setToken dans le bundle (`Bearer: 0`, `setToken: 0`).
- L'`Authorization` présent = code générique axios (Basic auth optionnel), non
  utilisé par l'espace client.
- Les appels authentifiés reposent sur **cookie de session + XSRF**
  (`withCredentials`, `xsrfCookieName`).

**Conséquence** : rien, côté client, ne lie l'`{id}` demandé à l'utilisateur
connecté. Si le serveur ne vérifie pas non plus la propriété, l'IDOR PII
authentifié (§1) est direct. C'est l'hypothèse n°1 à valider en axe B.

---

## Synthèse — ce qui reste à prouver en actif

| Finding | Gravité potentielle | Axe | Statut |
|---|---|---|---|
| IDOR PII sur `getSante/getMrh/...` (6 produits) | Critique | B | **à tester** |
| IDOR tarif Auto/Emprunteur/Crédit conso | Élevée | C | à tester |
| Token SMS dérivable (défense non contraignante) | Moyenne | — | **confirmé (passif)** |
| Clé marketplace « private » en clair | Élevée→Critique | D | clé confirmée ; droits à tester |
| Ids séquentiels exposés côté front | Moyenne | — | **confirmé** |
