# Journal — Audit tarifaire Mon Gustave

Mission : scraper le comparateur d'assurance Mon Gustave pour évaluer trois choses — la faisabilité du scraping,
la possibilité de reconstituer les grilles tarifaires des partenaires, et si le
site détecte l'activité.

Ce fichier trace l'avancement dans l'ordre. Chaque entrée : ce qui a été fait,
ce qu'on a trouvé, ce qui reste ouvert. Mis à jour à chaque étape significative.

---

## 2026-04-02 → 2026-04-14 — État hérité (avant reprise)

Projet repris tel quel, sans historique git. Trois scrapers indépendants déjà
fonctionnels :

- **MRH** et **Santé** : mature — session + XSRF token, retry 3x, reprise sur
  crash, parallélisme par assureur, export CSV/XLSX/JSON, profils déterministes
  pour diagnostic (`--deterministic`).
- **Animaux** : basique — pas de retry, pas de reprise, pas de parallélisme,
  logging console seulement.

Derniers runs connus avant reprise : MRH 116 profils (13 avril), Santé 78
profils (14 avril).

## 2026-08-13 — Reprise du projet

**Fait :**
- Audit complet des 3 modules, résumé des forces/faiblesses.
- `git init` + premier commit (`ca0e48f`) pour protéger le code. `.gitignore`
  ajouté (exclut `output/`, `__pycache__`, capture HTML `Pages_Devis/`).
- Refonte du module **Animaux** pour l'aligner sur le pattern MRH/Santé : retry,
  parallélisme, logging fichier, reprise, export XLSX (`7647857`).
- Ajout de profils déterministes pour Animaux (`0eec28b`), manquants jusque-là.
- Test de relance des 3 scrapers (1-2 profils chacun) : tout fonctionne,
  aucune erreur.

**Comparaison avec Firecrawl / crawl4ai :** écartés — ces outils servent à
extraire du contenu web (HTML → texte), pas à automatiser un flux
formulaire → API JSON avec session/XSRF comme ici. Le code sur-mesure existant
reste la bonne approche.

## 2026-08-13 — Collecte déterministe complète (3 modules)

**Fait :** lancement en parallèle des 3 scrapers en mode `--deterministic
--no-resume`.

**Résultats :**
- MRH : 121 profils, 1751 lignes d'offres.
- Santé : 78 profils, 2221 lignes d'offres.
- Animaux : 51 profils, 388 lignes d'offres.
- **Aucune erreur, aucun signe de détection anti-scraping** (pas de 429, pas
  de CAPTCHA) sur ~250 leads créés avec délais 5-45s.

**Analyse (rapport global 3 produits) :**
- MRH : seule la surface habitable fait bouger le prix nettement. Ancienneté
  logement et profession sans effet mesurable.
- Santé : 8 assureurs sur 12 renvoient "0 offre en ligne" (rappel commercial)
  plus de 78% du temps — invisibles au scraping API pur. Seuls 4 assureurs
  exploitables à >97%.
- Animaux : Chien plus cher que Chat, un des 3 assureurs configurés (Lovys)
  ne répond jamais sur cette collecte.
- **Découverte non prévue** : sur Santé, les 4 niveaux de garantie (soins
  médicaux, hospitalisation, optique, dentaire) n'ont **aucun effet** sur le
  prix affiché, quel que soit l'assureur.

Premier artifact publié : rapport 3-produits.

## 2026-08-13 — Focus Santé, bug de filtre trouvé et corrigé

**Demande :** creuser l'effet de l'âge sur le prix Santé (question utilisateur
directe — le premier chiffre montré semblait douteux).

**Trouvé :** un pic anormal à "41 ans" dans la courbe âge cassait la
progression. Cause : le script d'analyse filtrait les lignes avec
`.str.contains("date_naissance=")`, qui matchait à tort les lignes de test
`who_assure` (elles contiennent `conjoint_date_naissance=`). Corrigé avec
`.str.startswith()`. Deuxième occurrence du même bug trouvée sur le filtre
`nb_enfant=0`, corrigée pareil.

**Décision :** densifier la collecte Santé plutôt que de continuer sur 78
profils. Relance avec :
- Âge assuré : 8 → 32 points (tous les 2 ans, 18-80 ans).
- Âge conjoint : 4 → 13 points.
- Villes : 10 → 20.
- Nb enfants : 3 → 6 valeurs (0 à 5).

Commit `1c35b33`. Nouvelle collecte : 124 profils, 3683 lignes.

**Confirmé sur volume élargi :** 7 des 11 variables du formulaire Santé
(5 niveaux de garantie + mode de soins + profession) sans effet mesurable sur
aucun des 12 assureurs. Seuls who_assure, âge, régime et (faiblement) ville
pèsent. Rapport Santé dédié republié à la même URL.

## 2026-08-13 — Focus Selfassurance

**Demande :** isoler un seul assureur (Selfassurance) pour voir sa structure
interne en détail.

**Découverte majeure :** Selfassurance a **deux gammes de produit distinctes**,
avec un seuil net à **55 ans** :
- Moins de 55 ans → "Formule 1 W" à "Formule 5" (amplitude ×3,1).
- 55 ans et plus → "SERENISSIA ES_100" à "ES_200".

Aucun chevauchement entre 53 et 55 ans — vrai seuil produit, pas une
transition progressive.

**Limite trouvée :** la gamme SERENISSIA n'était couverte que sur la variable
âge (13 points) — who_assure, régime, ville, garanties n'avaient jamais été
testés avec un profil senior, tout le reste du dataset utilisant un profil de
base à 41 ans (donc toujours gamme Formule).

Rapport publié comme page séparée (pas de remplacement du rapport Santé
global). *Incident au passage : republication sans passer `url` a écrasé le
rapport global par erreur — restauré depuis le contenu conservé dans la
conversation avant de livrer les deux liens.*

## 2026-08-13 — Collecte senior dédiée

**Fait :**
- Ajout de `generate_senior_profiles()` dans `Sante/profiles.py` — même
  croisement de variables que le profil standard mais avec un assuré de
  65 ans, pour forcer la bascule sur la gamme SERENISSIA. 54 profils.
- Réduction de `DELAY_BETWEEN_PROFILES` de (5,10)s à (0,1)s — justifiée par
  l'absence totale de détection observée jusqu'ici sur ~370 profils.
- Nouveau flag CLI `--senior`. Commit `b9af965`.
- Collecte lancée et terminée : 54 profils, 2500 lignes, ~18 minutes.

**Résultats gamme SERENISSIA (comparés à Formule 1-5) :**
- Amplitude entrée→haut de gamme plus resserrée : ×1,65 (SERENISSIA) contre
  ×3,1 (Formule).
- Deux exclusions découvertes, propres au profil senior : régime "salarié
  agricole" et code postal de La Réunion (97400) → aucune offre. Ces critères
  passaient sans problème sur le profil standard.
- Garanties toujours sans effet, confirmé sur cette gamme aussi.

**Couverture encore incomplète côté SERENISSIA** (documenté explicitement
dans le rapport plutôt que caché) :
- Profession (17 valeurs) : jamais testée sur profil senior.
- Nombre d'enfants : jamais testé sur profil senior.
- Qui assurer : seulement 2/4 cas testés (Seul, Couple — pas les variantes
  avec enfants).

Deux pages publiées : rapport gamme Formule 1-5, rapport gamme SERENISSIA.

## 2026-08-13 — Modèle de régression (grille tarifaire estimée)

**Demande :** peut-on estimer la grille tarifaire complète et les coefficients
de chaque variable à partir des données déjà collectées ?

**Fait :** régression log-linéaire (`prix = base × coef_âge^âge × coef_who ×
coef_régime × coef_formule`) sur les 855 lignes de prix Selfassurance
(530 Formule + 325 SERENISSIA), via statsmodels OLS sur log(prix).

**Résultats :**
- Fit très bon : R²=0,967 (Formule), R²=0,953 (SERENISSIA). Erreur de
  prédiction vérifiée <3% sur un cas test.
- Coefficient âge : ×1,018/an (Formule) vs ×1,035/an (SERENISSIA) — la gamme
  senior vieillit en prix près de 2x plus vite par année d'âge.
- Coefficient qui-assurer (Couple) : ×1,75 (Formule) vs ×2,07 (SERENISSIA).
- Signal à confirmer : le régime TNS ressort légèrement moins cher que le
  régime général sur SERENISSIA (×0,90, p=0,011) — inverse de ce qui est
  observé sur Formule.

Rapport publié avec simulateur interactif (estime un prix pour une
combinaison non testée directement, ex. SERENISSIA + couple+enfants).

## 2026-08-13 — Réduction du délai de fetch (10s → 5s)

**Fait :** l'attente initiale avant de récupérer les tarifs (laisse le site
calculer côté serveur) passe de 10s à 5s sur les 3 scrapers. Le sleep entre
tentatives de retry (réponse vide/erreur) passe de 10s à 3s. Commit `1c5e436`.

**Validation :** testé sur Santé (1 profil) — les 12 assureurs répondent
normalement, offres complètes (5 formules pour Self-assurance et Mongustave,
cohérent avec les runs précédents à 10s), aucun retry déclenché.

Justifié par l'absence totale de détection observée sur ~420 profils déjà
collectés à ce stade.

## 2026-08-14 — Densification age/geo + regression avec regime general en reference

**Demande :** relancer avec encore plus de profils (âge annuel, plus de départements),
puis refaire le modèle de régression avec Régime général comme catégorie de
référence (plus interprétable qu'Alsace-Moselle).

**Fait :**
- `Sante/profiles.py` : âge assuré principal densifié de tous les 2 ans à
  **tous les ans** (18-80, 63 points). Âge conjoint : tous les 5 ans → tous
  les 2 ans (32 points). Géographie élargie de 20 à **58 codes postaux**
  (couverture départementale France métropolitaine + DOM Guadeloupe,
  Martinique, Guyane, Mayotte). Commit `3cc057e`.
- Deux collectes lancées séquentiellement (même dossier de sortie, donc pas
  en parallèle) : standard (`--deterministic`, 212 profils, 6312 lignes) puis
  senior (`--senior`, 92 profils, 4155 lignes). Les deux terminées sans
  erreur, portées par le délai réduit (5s) mis en place précédemment.

**Nouveau signal découvert :** avec la couverture géo élargie (58 codes
postaux au lieu de 20), la collecte senior révèle **6 exclusions**
(aucune offre) au lieu d'une seule trouvée avant :
- Régime "salarié agricole" (déjà connu).
- Monaco (98000).
- **Les 4 DOM testés systématiquement exclus** : Guadeloupe, Martinique,
  Guyane, Mayotte, La Réunion.

Motif net : Selfassurance semble refuser tout profil senior en outre-mer,
alors que ces mêmes codes postaux passent sans problème avant 55 ans.

**Régression mise à jour** (`REGIME_GENERAL` comme référence au lieu
d'`ALSACE_MOSELLE`) :
- Échantillon quasi doublé : 860 lignes (Formule 1-5, contre 530) et 550
  lignes (SERENISSIA, contre 325).
- Fit toujours bon : R²=0,960 (Formule) et R²=0,923 (SERENISSIA), légèrement
  plus bas qu'avant (plus de variance réelle capturée avec plus de données).
  Erreur de prédiction vérifiée ~5% sur le cas test (contre <3% avant, aussi
  attendu avec un échantillon plus large et plus varié).
- Base réinterprétée directement en régime général : 297€/an (Formule),
  102€/an (SERENISSIA).
- **Signal révisé** : le coefficient TNS qui semblait "moins cher que régime
  général" sur SERENISSIA avec le premier passage (325 lignes) **n'est plus
  significatif** avec l'échantillon élargi (p=0,30 contre p=0,011 avant) —
  confirmé comme bruit d'échantillonnage plutôt qu'un vrai effet.
- Coefficients âge, qui-assurer, formule quasi inchangés en valeur mais
  affinés (âge Formule ×1,017/an, SERENISSIA ×1,036/an).

Les 3 rapports Selfassurance (Formule 1-5, SERENISSIA, modèle de régression)
mis à jour et republiés sur leurs URLs existantes.

## 2026-08-17 — Couverture SERENISSIA complétée (profession + enfants)

**Fait :**
- `Sante/profiles.py` : `generate_senior_profiles()` complété avec les 3
  séries manquantes — who_assure ADULT_KIDS/COUPLE_KIDS, profession (17
  valeurs), nb_enfant (0 à 5). Total senior : 92 → **117 profils**.
- Collecte senior relancée (`collecte_senior_v3.out`), 209 profils traités,
  9493 lignes brutes, terminée sans erreur. Archivée
  (`output/archive/20260817_senior_v3_results.csv`).

**Résultats des séries complétées :**
- **Profession (17 valeurs testées) : aucun effet sur le prix**, même prix à
  l'euro près quelle que soit la catégorie/sous-catégorie choisie — cohérent
  avec le constat déjà fait sur la gamme Formule.
- **Nombre d'enfants** : effet net, +540€/an du 1er au 2e enfant, puis
  **plafond dès 2 enfants** (2 514€ stable de 2 à 5 enfants) — même
  comportement de plafonnement que sur Formule 1-5.
- **Qui assurer**, désormais complet sur les 4 cas : Seul (1 434€) < Seul+enfants
  (2 083€) < Couple (2 867€) < Couple+enfants (3 947€).

**Régression SERENISSIA mise à jour** avec l'échantillon complet (1 100
lignes, contre 550) : R²=0,917, coefficients who_assure/régime/formule
affinés mais stables. Un modèle "étendu" avec profession+nb_enfant en
régresseurs a aussi été testé (R²=0,932) — confirme les mêmes conclusions
(profession non significative en tant que catégorie unique, nb_enfant très
significatif, coefficient linéaire).

Les 3 rapports Selfassurance mis à jour et republiés (mêmes URLs). La
couverture SERENISSIA est désormais quasi complète — seul angle mort restant :
âge du conjoint sur profil senior (jamais testé densément, contrairement à
Formule).

---

## Pistes ouvertes / pas encore faites

- Âge du conjoint sur profil senior (SERENISSIA) — jamais testé densément,
  contrairement à la gamme Formule où l'assuré principal a 41 ans.
- Vérifier si l'exclusion des 4 DOM (Guadeloupe, Martinique, Guyane, Mayotte)
  découverte sur Selfassurance/SERENISSIA se retrouve chez d'autres assureurs
  Santé ou sur d'autres produits (MRH, Animaux).
- Volet détection sécurité : uniquement testé à rythme "poli" jusqu'ici.
  Reste à tester un rythme agressif (sans délai, requêtes en rafale) pour
  chercher le seuil réel de rate-limiting ou de blocage IP.
- Étendre l'analyse de régression aux autres assureurs Santé (actuellement
  Selfassurance seulement) et aux autres produits (MRH, Animaux).
- `requirements.txt` toujours absent.
- Code dupliqué entre les 3 modules (session, retry, save_results quasi
  identiques) — pas encore factorisé.
