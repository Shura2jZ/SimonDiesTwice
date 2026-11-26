# 10 — `unk06` des facesets = taille de la palette d'os du maillage

## Le symptôme

Depuis le premier build : écran envahi de géométrie texturée, Isshin **et**
Sekiro invisibles (Sekiro seulement quand Isshin est dans le champ), HUD net,
ralentissements, apparition 1–2 s avant le spawn. Avec `c5400` vanille : normal.
Symptôme **constant** quels que soient le contenu, le nombre de maillages, les
matériaux, la couleur de sommet, l'enroulement, les boîtes englobantes.

## Ce qui a été éliminé avant (mesures, pas suppositions)

- **Conteneur BND4/DCX** : diff octet par octet de l'en-tête décompressé entre
  la vanille et notre build ⇒ seules différences = tailles/offsets des entrées,
  correctement recalculés. La « table » à `0x298` (4×16 o) est **identique**.
- **DCX** : compression `KRAK` (Kraken) dans les deux cas ; taille décompressée
  cohérente (`12 762 512 = 12 129 840 + 632 672`) ; aucune limite de taille en
  cause (la vanille décompresse déjà à 8,6 Mo).
- **Notre FLVER est « canonique »** : relu puis réécrit par SoulsFormats (puis
  `gx_fix` + patch `0x40`, exactement comme `make_mod`), il redonne **le même
  fichier à l'octet près**. Rien à normaliser.
- **Notre géométrie est saine** : étendues réelles des 5 maillages dans
  `y ≈ 0 … 2,23 m`, aucun sommet aberrant (les extrêmes `y = −15` viennent des
  cordes/armes de la vanille, masquées par les animations).
- Les 28 autres maillages et leurs données sont **identiques à l'octet** à la
  vanille ⇒ ce qui casse vient **nécessairement de nos 5 maillages ou de leurs
  champs**.

## La découverte

Le champ `unk06` de chaque faceset (même valeur pour les 6 facesets d'un
maillage) est **la taille de la palette d'os du maillage** : le nombre
d'indices d'os **distincts non nuls** référencés par ses sommets.

Preuve par mesure sur la vanille (`_work/tools/cs/FlverOsCompte.cs` compare
plusieurs règles de comptage à `unk06`) :

| maillage | unk06 | os distincts (indices ≠ 0) | os distincts (poids > 0) |
|---|---:|---:|---:|
| 0 casque (rigide) | 1 | 1 | 1 |
| 3 corps | 81 | 81 | 81 |
| 4 tête | 31 | 31 | 31 |
| 5 cheveux | 27 | 27 | **25** |
| 6 kimono | 37 | 37 | **36** |
| 7 kimono_nontiling | 19 | 19 | 19 |
| 21 / 22 (même matériau 21) | 21 / **16** | 21 / 16 | 21 / 15 |

⇒ **33/33 exacts** avec la règle « indices distincts non nuls, quel que soit le
poids » (les 6 écarts de la colonne « poids > 0 » disparaissent).
⇒ Et c'est bien une propriété **du maillage**, pas du matériau : deux maillages
qui partagent le matériau 21 ont 21 et 16.

## Le défaut

`FlverInject.cs` recopiait `unk06` depuis le **gabarit du matériau** :

| emplacement | `unk06` déclaré | os réellement utilisés | verdict |
|---|---:|---:|---|
| 6 manteau (mat 7) | 19 | **26** | palette **trop courte** |
| 7 haut (mat 7) | 19 | **32** | palette **trop courte** |
| 3 bas (mat 7) | 19 | 19 | exact (coïncidence) |
| 0 tête (mat 4) | 31 | 9 | trop longue |
| 5 yeux (mat 3) | 81 | 1 | trop longue |

Une palette déclarée trop courte fait lire au moteur **au-delà** de la palette
d'os allouée : les matrices manquantes sont indéfinies ⇒ skinning explosé ⇒
géométrie géante qui couvre l'écran (et masque Sekiro, les faces écrivant dans
le tampon de profondeur). Cela explique que le symptôme soit resté **identique
sur tous les builds** : le nombre venait toujours d'un gabarit, jamais de nos
sommets.

## La correction

`_work/tools/cs/FlverInject.cs` : `unk06` est **recalculé** pour chaque
maillage = nombre d'indices d'os distincts non nuls de ses sommets. Les
drapeaux et le `cull` continuent de venir du gabarit du matériau (structure).

Vérifications sur le fichier **installé** (`_work/verif_installe.py` +
`FlverOsCompte.exe`) :

```
  [0] tête    unk06  9  os distincts  9   écart 0
  [3] bas     unk06 19  os distincts 19   écart 0
  [5] yeux    unk06  1  os distincts  1   écart 0
  [6] manteau unk06 26  os distincts 26   écart 0
  [7] haut    unk06 32  os distincts 32   écart 0
```

## Leçon

Quand un champ inconnu a une valeur **régulière** chez la vanille (ici : égale
à une quantité mesurable sur les données), il faut **trouver sa règle par
mesure** — on la trouve — au lieu de la recopier d'un voisin « qui y
ressemble ». Recopier une valeur décrite par les données elles-mêmes sur
d'autres données est le piège classique du repack.

## Outils créés dans cette étape

- `_work/tools/cs/FlverOsCompte.cs` — plusieurs comptages d'os par maillage,
  confrontation à `unk06` (la mesure qui a tranché).
- `_work/bbox_table.py` — vide la table des boîtes (33 × 36 o à `0x23BA0`).
- `_work/hash_bnd4.py` — diff de tout l'en-tête BND4 (entrées + zone `0x298`).
- `_work/roundtrip_notre.py` — notre FLVER est-il canonique (relire/réécrire).
- `_work/tableau_maillages.py` — tableau maillage → (nœud, matériau, agencement).
- `_work/compare_unk06.py` — `unk06` vs os mesurés, côte à côte.
- `_work/verif_installe.py` — taille/MD5/entrées du fichier réellement chargé,
  et extraction du FLVER pour contrôle.

## Reste ouvert

- `unk06` des emplacements 0/3/5 était **trop long** (31/19/81 au lieu de 9/19/1) :
  sans effet visible attendu (place réservée inutilisée), mais désormais exact.
- Le `cull` (faces visibles) est encore celui du gabarit matériau et non celui
  de l'emplacement : à reprendre si un maillage est vu de trop près/en double.
