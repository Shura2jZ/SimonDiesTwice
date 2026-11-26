# Test « rigide sur os 2 (Pelvis) » — 2026-10-18

## Pourquoi ce test

Après élimination (voir `notes/10_*.md` et `notes/11_*.md`), il ne reste plus
aucun suspect **hors du skinning** :

- la géométrie de nos 5 maillages, relue dans le fichier, est saine :
  personnage de **2,21 m**, pieds à Y = 0, tête à Y = 2,21, largeurs 0,4–1,0 m ;
- la table des facesets (196 × 32 o) suit **la même convention** que la vanille
  (offsets relatifs à `DataOffset`, taille en octets, index 16 bits, alignement 16) ;
- la zone GX et la table des matériaux sont **identiques octet pour octet** ;
- le descripteur de maillage ne peut pas être la cause : le code d'import de
  FLVER Editor (`_work/tools/FLVER_Editor_src/MySFformat/src/ProgramFbxImport.cs`
  l. 223-486) produit **exactement notre structure** (6 facesets portant la même
  liste, `Dynamic = 1`, même layout, `UseBoneWeights`) tout en s'écartant de la
  vanille sur **tous** les champs déjà éliminés (couleur blanche, `NormalW = -1`,
  `tangentW = -1`, `Unk06 = 1`, palette `BoneIndices = [0,1]`, `NodeIndex = 0`,
  boîte = min/max réels). Ses modèles s'affichent dans Sekiro.

⇒ Aucun champ du maillage ne peut expliquer un rendu cassé.

## Le point qui invalide l'ancien test « rigide »

`simon_export.py --rigide` lie **tout** à `index_isshin["Root"]` = **os 1**.
Or la vanille n'utilise **jamais** les indices d'os 0 et 1 (union des 33 maillages
vanille = 2…183). L'espace de peau commence donc à 2.

L'ancien build « rigide » pointait sur un indice sans matrice de peau valide :
même symptôme possible, mais pour une raison **différente** du skinning multi-os.
**Ce test n'a rien prouvé.**

## Le build installé

- `_work/rigide_os2.py` : repointe tous les sommets de `_work/simon_rigide.bin`
  (os 1) vers l'**os 2 (Pelvis)**. Format SMPORT décodé et vérifié
  (0 octet restant en fin de parcours, 64 793 sommets, 5 maillages, 284 os).
- `_work/simon_rigide2.bin` (7 564 177 o) → `_work/simon_rigide2.flver`.
- Injection : `FlverInject.exe <vanille> simon_rigide2.bin simon_rigide2.flver
  --remplacer --slots 6,7,3,5,0 --boite-origine`.
- Vérifications hors jeu : poids = **1,000** exactement, indice d'os max = **2**,
  **0 orphelin**, positions identiques à l'octet après relecture.
- Build : `make_mod.py --sans-clm2 --install` → BND4 12 762 512 o,
  DCX 3 652 656 o.
- Sauvegarde de l'état précédent : `_work/mod_backup/c5400.avant_rigide2.dcx`
  (sha256 `EB3F9869…`). Fichier installé : sha256 `1BAF56BB…`.

## Ce qui change par rapport au build précédent

Le mode `--rigide` change **deux choses d'un coup** (c'est inhérent au mode) :

1. **liaison** : mélange de 4 os → un seul os (2) ;
2. **positions** : re-pose dans la liaison d'Isshin → **pose propre de Simon
   tournée 180°** (non re-posée).

À la pose de liaison, un maillage lié à un seul os se dessine **exactement comme
ses sommets sont écrits** ⇒ on doit voir une **statue de Simon d'environ 2,2 m,
debout, immobile**, sans déformation.

## Lecture du résultat

| Observation | Conclusion |
|---|---|
| Statue de Simon (~2 m, immobile) | géométrie, matériaux, conteneur, moteur : **bons**. Coupable = **mélange multi-os**. Palier 1A atteint (Simon visible), même rigide. |
| Encore la masse brune / boss invisible | skinning **innocent**. Il ne reste que la **taille du fichier** ou l'**environnement de jeu** ⇒ tester un build minuscule. |

## Leviers suivants (dans l'ordre)

1. Si statue OK : chercher pourquoi le mélange multi-os casse (espace d'indices,
   `Unk06`, palette) — la re-pose hors jeu est déjà prouvée correcte.
2. Si statue cassée : build de contrôle « une seule modification minuscule de la
   vanille » (décaler les sommets d'un maillage vanille) pour séparer
   *écriture/chargement* de *choix de contenu*.
3. Non testés : `CullBackfaces` des emplacements 3 et 6 (vanille *False* → nous
   *True*, valeur prise au gabarit), signe du 4ᵉ octet de tangente (+1 partout
   au lieu de ±1).
