# Ce qu'on a trouvé, expliqué simplement

> Ce document explique, **sans aucun mot technique**, ce que notre analyse du
> site Mon Gustave a révélé. Objectif : que n'importe qui — même sans rien
> connaître à l'informatique — comprenne les problèmes et pourquoi ils comptent.

---

## D'abord, c'est quoi le contexte ?

Mon Gustave est un site qui compare des assurances (santé, habitation, animaux,
voiture, crédit…). Vous remplissez un formulaire avec vos informations, et le
site vous affiche les prix de plusieurs assureurs.

Nous avons regardé **comment ce site fonctionne à l'intérieur**, un peu comme un
contrôleur technique regarde sous le capot d'une voiture. Le but n'est pas de
nuire : c'est de **trouver les points faibles avant qu'une personne
mal intentionnée ne les trouve**, pour pouvoir les réparer.

Tout ce qu'on a fait ici est de la simple **observation** : on a lu le
« mode d'emploi » que le site envoie automatiquement à chaque visiteur (le
navigateur en a besoin pour afficher la page). On n'a forcé aucune porte.

---

## Une image pour tout comprendre : l'immeuble de bureaux

Imaginez que le site est un **grand immeuble** qui contient les dossiers de tous
les clients. Chaque dossier a un **numéro** (dossier n°1, n°2, n°3…).

Voici ce qu'on a remarqué en regardant comment l'immeuble est organisé.

---

## Problème n°1 — Les numéros de dossier se devinent (et les dossiers sont peut-être en accès libre)

Chaque client qui demande un devis reçoit un dossier avec un numéro. Le souci :
ces numéros se suivent **dans l'ordre**. Le vôtre est le 1000, votre voisin a le
1001, la personne d'avant avait le 999.

Résultat : il suffit de **compter** (999, 1000, 1001…) pour tomber sur les
dossiers des autres. Pas besoin de deviner un code compliqué.

On sait déjà (analyse précédente) qu'avec ces numéros, on peut voir **les prix**
calculés pour les autres personnes. Ce n'est pas dramatique en soi.

**Mais** on vient de repérer une porte plus importante : il existe un moyen, dans
l'immeuble, de demander **le dossier complet** d'un client à partir de son
numéro — pas juste les prix, mais potentiellement **son nom, son email, son
téléphone, son adresse**, et pour les crédits/assurances de prêt,
**ses revenus et des informations de santé**.

La question qui reste à vérifier (prochaine étape) : est-ce que le gardien de
l'immeuble **vérifie vraiment que vous êtes le propriétaire du dossier** avant de
vous le donner ? Si la réponse est non, alors n'importe qui pourrait lire les
données personnelles de n'importe qui. **C'est le point le plus important à
tester, et il n'est pas encore tranché.**

---

## Problème n°2 — Un « passe » secret est écrit sur la porte

Le site travaille avec un service partenaire qui gère les demandes de devis
(c'est en réalité la même société derrière). Pour discuter avec ce service, le
site utilise une sorte de **clé d'accès**.

Normalement, ce genre de clé doit rester **cachée**, comme le code d'un
coffre-fort qu'on ne montre à personne. Ici, la clé est **écrite en clair** dans
la page, visible par tout visiteur qui sait où regarder. Pire : le nom de la clé
contient littéralement le mot **« privé »** — c'est donc une clé qui était censée
rester secrète, et qui ne l'est pas.

On ne sait pas encore **ce que cette clé permet de faire exactement** (juste
vérifier une info ? ou lire la liste des clients ?). C'est aussi à tester dans la
prochaine étape. Mais le simple fait qu'elle soit visible est déjà un défaut.

---

## Problème n°3 — La vérification par SMS ne protège pas vraiment

Le site a un système de vérification par SMS (recevoir un code sur son
téléphone). En théorie, c'est bien : ça sert à prouver qu'on est une vraie
personne.

Sauf qu'ici, le « cachet de sécurité » qui accompagne cette vérification est
fabriqué à partir de **votre propre email et de votre propre numéro** — deux
informations que vous tapez vous-même. C'est comme un videur à l'entrée d'une
boîte qui vous demande de **prouver votre identité… en écrivant vous-même votre
nom sur un papier**. N'importe qui peut écrire n'importe quel nom. La
vérification existe, mais elle **ne bloque personne**.

---

## Problème n°4 — On peut créer des faux clients à volonté, sans limite

(Déjà établi précédemment, rappelé ici pour le tableau complet.)

Le site accepte des demandes de devis avec des **fausses coordonnées**
inventées, et **autant qu'on veut**, sans jamais dire « stop, vous en faites
trop ». C'est comme une boîte aux lettres où l'on pourrait glisser des milliers
de faux courriers sans que personne ne s'en aperçoive. Ça peut **polluer le
fichier client** et, si ces demandes sont revendues aux assureurs, **coûter de
l'argent**.

---

## En résumé (tableau simple)

| Le problème | L'image | Est-ce grave ? | Où on en est |
|---|---|---|---|
| Numéros de dossier qui se suivent | Compter 999, 1000, 1001… | Moyen (prix) → **potentiellement grave** (données perso) | Prix : confirmé. Données perso : **à vérifier** |
| Clé secrète visible | Le code du coffre écrit sur la porte | Potentiellement grave | Clé confirmée visible ; ce qu'elle ouvre : à tester |
| Vérification SMS inefficace | « Prouvez qui vous êtes en écrivant votre nom » | Moyen | Confirmé |
| Faux clients en masse | Milliers de faux courriers dans la boîte | Moyen | Confirmé |

---

## Ce qu'il faut retenir

1. **Rien n'a été volé ni cassé.** On a seulement observé comment le site est
   construit, à partir d'informations qu'il donne lui-même à tout le monde.
2. **Le point le plus sérieux n'est pas encore tranché** : on a trouvé la porte
   qui donnerait accès aux données personnelles complètes des clients, mais il
   reste à vérifier si cette porte est réellement gardée ou pas.
3. **Tout ceci sert à réparer.** Chaque problème listé a une solution simple
   (rendre les numéros impossibles à deviner, cacher la clé, vraie vérification
   d'identité, limiter le nombre de demandes). C'est justement le but de cet
   audit : trouver, pour corriger.

---

*Pour les détails techniques : voir `SURFACE_PII.md` et
`DOCUMENTATION_SCRAPING.md`. Le plan des vérifications à venir est dans
`PLAN_AUDIT_PII.md`.*
