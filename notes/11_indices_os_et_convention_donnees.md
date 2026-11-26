# 11 — Espace des indices d'os et convention de la section de données

Mesures faites le 2026-10-17, après le test en jeu du build « rigide ».
Tout est vérifié sur fichiers, aucun de ces points n'est une hypothèse.

## 1. L'indice d'os 1 (« Root ») n'est pas un os de peau

Relevé des indices d'os réellement référencés par les **sommets** :

| fichier | indices distincts | min | max | 0 utilisé | 1 utilisé |
|---|---|---|---|---|---|
| `c5400.flver` (Isshin, 33 maillages) | 180 | 2 | 183 | non | non |
| `c1240.flver` | 105 | 2 | 110 | non | non |
| `c1250.flver` | 127 | 2 | 129 | non | non |
| `FC_M_0240.flver` | 61 | 6 | 68 | non | non |

L'union sur les 33 maillages d'Isshin va de **2 à 183** : ni 0 (« Master ») ni 1
(« Root ») ne sont jamais utilisés, alors que ces nœuds existent bien dans le
FLVER (757 nœuds). Conclusion : l'espace d'indices utilisé par le skinning
commence à 2 (Pelvis) et les nœuds 0/1 n'en font pas partie.

Contrôle complémentaire : le casque vanille a **7362 sommets tous sur l'os 147
(Head) avec `unk06 = 1`** — donc `unk06` n'est pas une borne pour l'indice
stocké (147 ≫ 1) : l'indice est bien global et `unk06` est seulement le nombre
d'os distincts du maillage.

**Conséquence** : le build de diagnostic « rigide » (tous les sommets sur l'os
**1**) lisait une matrice hors de l'espace des os de peau. Son échec en jeu ne
dit rien de la géométrie ni du fichier — le test était faussé par construction.

Autre contrôle utile : la vanille écrit `os = 147 0 0 0` / `poids = 1 0 0 0`
pour un maillage rigide ⇒ **l'indice 0 avec poids 0 dans les emplacements
inutilisés est la convention normale** (ce n'est pas une anomalie de notre
export).

## 2. Convention de la section de données (offsets implicites)

Les tampons de sommets ne portent **ni offset ni taille** : les seuls champs
sont `EdgeCompressed`, `BufferIndex`, `LayoutIndex`. La carte de la section est
donc **déduite par accumulation**, dans cet ordre, maillage par maillage :

1. pour chaque faceset : `Pad(0x10)` puis ses indices (16 bits si le plus grand
   indice ≤ 0xFFFF) ;
2. puis pour chaque tampon : `Pad(0x10)` puis `nb_sommets × stride(agencement)`.

Vérification faite à l'octet près (`_work/carte_donnees.py`) en retrouvant les
octets de position du premier sommet de chaque maillage (`FlverSommets` donne la
pleine précision) :

| fichier | indices (octets) | sommets (octets) | total déduit | fin déduite | fin réelle | écart |
|---|---|---|---|---|---|---|
| `c5400.flver` vanille | 3 374 916 | 4 400 260 | 7 775 176 | 7 966 680 | 7 966 688 | 8 |
| `simon_canon.flver` | 6 258 864 | 5 679 644 | 11 938 508 | 12 129 896 | 12 129 904 | 8 |

Écart = 8 octets de remplissage final. **La section de données de notre fichier
suit exactement la même règle que la vanille** : aucun décalage possible côté
moteur.

Remarque : un ancien outil (`tools/flver_bilan.py`) ne comptait que 131 facesets
sur 196 et faisait croire à ~1 Mo « inexpliqué ». C'était un défaut de l'outil.

## 3. Chaîne d'écriture innocente

`tools/verif_roundtrip.py` : lecture + réécriture SoulsFormats, puis `gx_fix`
(compactage de la zone GX : 336 → 272 octets) puis correctif `0x40` ⇒ le fichier
obtenu est **identique à l'octet près** à la vanille. Deux champs que
SoulsFormats écrit « faux » et qu'il faut corriger :

* `0x40` = nombre de faces **hors motion blur** (la bibliothèque y met le total) ;
* la zone GX est recopiée en 4 listes au lieu de 2 listes + 2 sous-plages, ce qui
  décale 1093 pointeurs de chaînes et `DataOffset` de +64 octets (`gx_fix`).

## 4. État des builds testés en jeu

| build | indices d'os | fichier | verdict |
|---|---|---|---|
| 2026-10-16 23:33 | valides (2..183) | **zone GX non corrigée** (+64 octets, `DataOffset` faux) | ne dit rien : fichier défectueux |
| 2026-10-17 17:03 « rigide » | **os 1 invalide** | propre | ne dit rien : indice hors espace |
| 2026-10-17 18:56 canonique | valides (2..183) | propre | **à tester** |

Aucun build à la fois propre et à indices valides n'avait été testé en jeu.
