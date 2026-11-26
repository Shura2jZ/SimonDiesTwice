# 07 — Le champ d'en-tête FLVER `0x40` (« faces hors motion blur »)

## Fait mesuré

L'en-tête FLVER contient **deux comptes de faces** juste après les boîtes englobantes :

| offset | valeur vanille c5400 | signification |
|---|---|---|
| `0x40` | **262 326** | nombre de faces **hors maillages de motion blur et faces dégénérées** |
| `0x44` | **562 486** | nombre **total** de faces |

Source (SoulsFormats, `Formats/FLVER/FLVER2/FLVER2.cs`, lecture) :

```
br.ReadInt32(); // Face count not including motion blur meshes or degenerate faces
br.ReadInt32(); // Total face count
```

## Vérification par la mesure

Outil `_work/tools/cs/FlverFacesets.exe` (drapeaux de chaque faceset + sommes) :

- `0x44 == total des faces` → **vrai** (562 486)
- `0x40 == faces hors MotionBlur` → **vrai** (262 326)
- (faux pour « LOD0 », « LOD1 », « LOD0 hors MotionBlur »)

Le drapeau est `FSFlags.MotionBlur = 0x8000_0000` : « Many meshes have a copy of each
faceset with and without this flag. If you remove them, motion blur stops working. »
Autrement dit : chaque maillage porte trois facesets doublés d'une copie marquée
MotionBlur. 562 486 − 262 326 = 300 160 faces sont les copies de motion blur.

## Le défaut du writer SoulsFormats

À l'écriture, SoulsFormats **recalcule** ces deux valeurs (`FaceSet.AddFaceCounts`) :

```csharp
else   // facesets en liste de triangles (notre cas : 0 faceset en bande)
{
    totalFaceCount += Indices.Count / 3;
    trueFaceCount  += Indices.Count / 3;   // ← aucune exclusion
}
```

L'exclusion « motion blur » n'est appliquée **que** pour les facesets en bande
(`TriangleStrip`), qui ne sont pas utilisés ici. Conséquence : pour tout FLVER
réécrit par cet outil, **`0x40` == `0x44`** au lieu de la valeur vanille.

C'est le **seul changement sémantique** de la réécriture (mesuré par
`tools/flver_ecarts.py` entre la vanille et l'aller-retour) :

- `0x0C` DataOffset : 190 208 → 190 272 (+64) ;
- `0x40` : 262 326 → 562 486 ;
- une insertion de 64 octets dans le bloc des matériaux (bloc GX doublé) — tous les
  pointeurs situés avant sont donc décalés de +64 (chaque octet modifié vaut +0x40) ;
- **rien d'autre** : au-delà de `0x2445C`, le fichier est identique à la vanille
  décalée de 64 octets.

Ce défaut est présent dans **tous** les builds produits jusque-là (5 maillages,
33 emplacements, CLM2 5 ou 33 éléments) ⇒ il explique que le symptôme en jeu ait été
**exactement identique** à chaque essai, indépendamment de la géométrie.

## Correctif

`tools/flver_040.py` pose `0x40` à la valeur voulue, sans toucher au reste.
Pour un modèle dont on connaît la valeur de référence, on recopie celle-ci ; pour un
modèle neuf, il faudra la **calculer** : somme des faces des facesets qui ne portent
pas le drapeau `0x8000_0000` (et, pour les facesets en bande, en excluant en plus les
triangles dégénérés, comme fait SoulsFormats).

## Statut

- Conteneur **innocenté** : `tools/verif_conteneur.py` montre qu'un rebuild BND4 sans
  remplacement est **byte-identique** à la vanille, et que notre DCX se relit à
  l'identique (préfixe constant identique à celui de 9 DCX vanille).
- Test en jeu en cours : **géométrie vanille pure, `0x40` corrigé** (33 maillages,
  drapeaux MotionBlur intacts). Si l'écran redevient normal → cause confirmée et
  correctif suffisant ; si le carnage persiste → le suspect suivant est le bloc GX
  de 64 octets ajouté par le writer.
