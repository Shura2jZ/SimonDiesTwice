# Sens d'enroulement des triangles (17/10)

## Le symptôme

En jeu, avec notre `c5400` : Isshin (et Sekiro) invisibles dès qu'Isshin entre
dans le champ de vision ; grandes surfaces sombres, fines lignes claires,
textures « qui sautent à l'écran » ; HUD net ; ralentissements. Avec le `c5400`
vanille, tout est normal.

## Ce qui a été éliminé juste avant (mesuré)

* **La chaîne d'écriture est innoncente.** `tools/verif_roundtrip.py` :
  `SoulsFormats` réécrit le FLVER vanille, `tools/gx_fix.py` le recompacte, le
  patch `0x40` est appliqué → le résultat est **identique à l'octet près** au
  FLVER vanille (7 966 688 octets, 0 plage différente). Donc le fichier est écrit
  au bon endroit, dans le bon format, et le jeu lit bien nos données.
* **La cible est la bonne** : `mods\chr\c5400.chrbnd.dcx`, 4 entrées
  (`c5400.flver`, `c5400.hkx`, `c5400_c.hkx`, `c5400_c.clm2`), les 3 non-FLVER
  identiques à la vanille (vérifié par `tools/verif_installe.py` et
  `tools/check_installed.py`).
* **Indices d'arêtes** : 0 groupe dans tous les maillages, vanille comme nous
  (`FlverEdges.exe`) → piste morte, définitivement.
* **L'oracle d'animation** (`tools/oracle_anim.py`) continuait de montrer une
  silhouette humaine correcte : il ne modélise que la déformation (positions,
  poids, indices d'os). Il ne pouvait donc pas voir le défaut ci-dessous.

## Le défaut trouvé

Nouvel outil : `_work/tools/cs/FlverWinding.cs` (`FlverWinding.exe`). Pour chaque
triangle il calcule la normale géométrique (produit vectoriel du sens des
indices) et la compare à la normale stockée aux sommets.

| | `dot(face, normale)` | positifs | volume signé |
|---|---|---|---|
| **Vanille**, tous les maillages | **−0,98** | **0,0 %** | **négatif** |
| **Notre build** (slots 0/3/5/6/7) | **+0,98** | **84 à 100 %** | positifs |

La vanille enroule **tous** ses triangles dans le sens **inverse** de ses
normales de sommet : la face avant est en sens **horaire** vue de l'extérieur,
ce qui correspond à la convention **Direct3D par défaut**
(`FrontCounterClockwise = FALSE`). Le GLB de Simon suit la convention
UE/glTF (sens anti-horaire extérieur, `dot = +0,98`).

Recopiés tels quels, tous nos triangles extérieurs sont donc vus comme des faces
**arrière** par Direct3D. Avec `cull=True` le jeu les supprime :

* le personnage paraît **invisible / creux** (on ne voit plus que l'intérieur et
  les bords) ;
* les grandes surfaces intérieures non éclairées → **grandes géométries sombres** ;
* les bords de silhouette → **fines lignes claires** ;
* la géométrie corrompue masque Sekiro dès qu'Isshin est à l'écran.

Pourquoi nos contrôles hors-jeu ne l'ont jamais vu : `MySFformat.Cli.exe` est
appelé avec `"renderMode":"BothNoTex"`, c'est-à-dire **les deux faces, sans test
de face cachée**. Une inversion totale du sens des triangles y est invisible.

## La correction

Dans `tools/simon_export.py`, à l'écriture des indices : les deux derniers
indices de chaque triangle sont permutés
(`indices[t], indices[t+2], indices[t+1]`).

La position, la normale et la tangente des sommets ne changent pas ; seule
l'orientation des faces revient dans la convention de Sekiro.

Après correction, sur le FLVER **réellement installé** (`FlverWinding.exe`) :

```
maill  mat   sommets   triangles   volumeSigne      A:dot(face,norm)   A>0
   0     4     6182      11635        -0.063615           -0.9811     0.0%
   3     7    23966      39371        -0.054543           -0.8545     3.0%
   5     3     1604       2808        -0.000047           -0.9993     0.0%
   6     7    15266      24917        -0.088698           -0.7009    11.1%
   7     7    17775      30563        -0.056014           -0.7916     6.7%
```

Signes conformes à la vanille. Les quelques pourcents restants positifs
(11 % sur le manteau, 7 % sur le haut) sont des triangles que la source rendait
déjà dans l'autre sens : à surveiller (trous possibles sur les pans de tissu),
mais ils sont minoritaires.

## Écarts de champs de sommet encore connus (non corrigés, non prouvés fautifs)

Relevés par `FlverAttr.exe`, présents **uniquement** sur nos 5 maillages
(les 28 autres emplacements sont vanille à l'identique) :

| champ | vanille (tous les maillages) | notre build |
|---|---|---|
| 4e octet de la normale (`NormalW`) | 0 | 255 (`FlverInject.cs` écrit `-1`) |
| 4e octet de la tangente | ±1 (signe de la poignée de la bitangente) | 1 fixe (valeur du GLB) |
| couleur de sommet | (255, 0, 0, 255) constante | valeurs de Simon (0,24 à 1) |

Ils ne peuvent pas rendre le personnage invisible, mais ils peuvent expliquer un
**éclairage** ou une **teinte** faux. C'est le candidat suivant si le modèle
apparaît mais paraît mal ombré.

## Reste à faire

1. Test en jeu du build « enroulement corrigé ».
2. Si le modèle apparaît mais mal ombré : conformer `NormalW` à 0, la tangente
   au signe réel et la couleur de sommet à la constante de la vanille.
3. S'il reste des trous : traiter les triangles résiduels (manteau 11 %, haut 7 %).

---

# Correction du 17/10 (soir) — l'enroulement n'était corrigé qu'en partie

## Ce qui était faux dans la note ci-dessus

Le tableau « après correction » plus haut a été relevé sur un export **différent**
de celui réellement installé : les nombres de triangles n'y sont pas les mêmes
(39 371 / 24 917 / 30 563 au lieu de 38 890 / 24 643 / 30 329). Mesure refaite sur
le FLVER **réellement installé** (`FlverWinding.exe`) :

```
maill  mat   sommets   triangles   A:dot(face,norm)   A>0
   0     4     6182      11635           -0.8544      6.5 %
   3     7    23966      38890           -0.1196     43.9 %
   5     3     1604       2808           -0.9993      0.0 %
   6     7    15266      24643           -0.1605     40.2 %
   7     7    17775      30329           -0.0961     44.1 %
```

Une inversion **globale** de l'ordre des indices ne suffit donc pas : sur les
parties de tissu (manteau, haut, bas), la source contient des faces déjà
enroulées dans l'autre sens, et 40 à 44 % des triangles restaient vus comme des
faces arrière — donc supprimés par `cull=True`. C'est exactement le symptôme
observé en jeu.

## La correction retenue

Dans `tools/simon_export.py`, l'ordre des indices est maintenant choisi **face par
face** : on calcule la normale géométrique du triangle et la somme des normales
stockées de ses trois sommets ; si le produit scalaire est positif (convention
glTF/UE) les deux derniers indices sont permutés. Objectif : reproduire
l'invariant mesuré sur la vanille, `dot < 0` pour **toutes** les faces.

Nombre de triangles retournés par maillage au dernier export :

| maillage | retournés / total |
|---|---|
| `MI_Simon_Coat` | 15 404 / 25 384 |
| `MI_Simon_Top` | 17 348 / 30 918 |
| `MI_Simon_Bottom` | 22 614 / 40 112 |
| `MI_Curator_Aline_BlackPart` | 3 072 / 3 072 |
| `MI_Simon_Head` | 11 194 / 11 952 |

## Vérification (build installé)

```
maill  mat   sommets   triangles   A:dot(face,norm)   A>0
   0     4     6182      11635           -0.9553      0.0 %
   3     7    23966      38890           -0.7648      0.0 %
   5     3     1604       2808           -0.9993      0.0 %
   6     7    15266      24643           -0.6660      0.0 %
   7     7    17775      30329           -0.7078      0.0 %
```

**0,0 % de faces positives sur les 5 maillages**, comme la vanille.

## Preuve que rien d'autre n'a changé

Diff octet à octet entre le FLVER précédemment installé et le nouveau (les deux
après `gx_fix`, 12 129 840 octets) :

* en-tête `0x00..0x50` : identique ;
* **0 octet différent avant la section de données** (toutes les tables :
  matériaux, nœuds, maillages, facesets, agencements, boîte englobante) ;
* les 531 132 octets qui diffèrent sont **tous** dans les tampons d'indices.

Le nombre de triangles, les positions, normales, UV, poids et indices d'os sont
inchangés.

## Champ `0x40` : vérifié conforme

`FlverInject.exe` calcule lui-même `0x40` = somme des faces des facesets **sans**
le drapeau `MotionBlur` (règle mesurée sur la vanille). Vérification sur le FLVER
installé : `0x40 = 509 832` = exactement la somme mesurée par `FlverFacesets.exe`
(196 facesets), et `0x44 = 1 043 144` = total. Rien à corriger.

## État installé

* `E:\Games\Sekiro - Shadows Die Twice\mods\chr\c5400.chrbnd.dcx`
  — 3 805 737 octets, sha256 `2fed2103dc610c35…`
* `c5400.flver` — 12 129 840 octets, sha256 `f2236db63b0e7771…`
* l'enroulement du FLVER **extrait de l'archive installée** a été revérifié :
  0,0 % de faces positives.
* sauvegarde de l'état précédent : `_work/mod_backup/c5400.avant_enroule.dcx`.
