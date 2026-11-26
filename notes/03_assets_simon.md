# Assets du boss Simon (Clair Obscur: Expedition 33)

Source : `E:\Games\Clair Obscur - Expedition 33\Manifest_UFSFiles_Win64.txt`
(256 011 lignes, format `chemin<TAB>horodatage`).

## Faits vérifiés

Racine UE des assets de Simon :

```
Sandfall/Content/Characters/Enemies/HumanEnnemies/Simon/
```

### Maillage principal (le boss)

| Asset | Rôle |
|---|---|
| `SK_Simon.uasset` | **skeletal mesh du boss** (cible de la phase 1) |
| `SK_Simon_Physics.uasset` | physique (cloth/collisions) |
| `SM_Simon_Sword_UE5_2.uasset` | épée (static mesh) |
| `SM_FX_Simon_SwordOptimized.uasset` | épée version FX |
| `BP_EnemyBattle_Simon.uasset` | blueprint de combat (phase 1) |
| `BP_EnemyBattle_Simon_Phase2.uasset` | blueprint de combat (phase 2) |
| `BP_EnemyBattle_Simon_ALPHA.uasset` | variante alpha |

### Cheveux (assets séparés, avec leur propre squelette)

```
Sandfall/Content/Characters/Hair/NPCs/Simon/
  Simon_hair_skl.uasset                  <- mesh des cheveux
  Simon_hair_skl_Skeleton.uasset         <- squelette
  T_Hair_Simon_Color / _Alpha / _Depth / _ID   <- textures
  MI_Hair_Simon / _Black / _Alpha / _Custo
```

### Textures du corps (`.../Simon/Textures/`)

Une famille par pièce : `BaseColor`, `Normal`, `OcclusionRoughnessMetallic`
(+ `BC_alpha` pour les pans de tissu).

```
Simon_Bottom_BaseColor / _Normal / _OcclusionRoughnessMetallic / _BC_alpha
Simon_Coat_*          (idem)
Simon_Top_*           (idem)
Simon_Head_BaseColor / _BaseColor_Alpha / _BaseColor_Emissive_Alpha / _Normal / _OcclusionRoughnessMetallic
```

Matériaux instanciés : `MI_Simon_Bottom`, `MI_Simon_Coat`, `MI_Simon_Head`,
`MI_Simon_Top` (+ `_alpha`).

### Textures de l'épée (`.../Simon/Textures/New_Sword/`)

`Simon_Blade_BaseColor / _Normal / _OcclusionRoughnessMetallic / _Curvature / _Thickness`
`Simon_Handle_BaseColor / _Normal / _OcclusionRoughnessMetallic / _Emissive`

### Animations

`.../Simon/Animations/` (38 fichiers, ex. `Simon_Dash_in`, `Simon_Dash_Out`).
Nota : la **phase 1 ne les utilise pas** (on garde les anims d'Isshin).
Elles ne serviront qu'à comprendre les enchaînements, en phase 3.

### Autres occurrences de « Simon »

- `Sandfall/Content/Levels/CleasTower/DL_CleasTower_SimonUnleashed.uasset`
  + matériaux `AbyssSimon`, `SimonCleaTower` → **un second combat (tour de Clea,
  « Simon Unleashed »)**. À vérifier : mesh différent ou simple re-matériau.
- `Sandfall/Content/Cinematics/Simon/` (SimonIntro, SimonOutro, Finisher_Simon).

## Inconnues

- `SK_Simon` est-il unique, ou existe-t-il un variant « Unleashed » avec son
  propre mesh ? (Le manifeste ne montre qu'un `SK_Simon`.)
- Nombre de matériaux/slots réellement portés par `SK_Simon` (à voir à l'export).
