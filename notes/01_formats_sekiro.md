# M1 — Formats Sekiro (résultats vérifiés)

Tout ce qui suit a été **observé sur des octets réels**, principalement via
`mods\Parts\fc_m_0000.partsbnd.dcx` (un fichier Sekiro non chiffré).

## 1. Chaîne de conteneurs (VALIDÉE de bout en bout)

```
partsbnd.dcx
  └─ DCX (Oodle/Kraken)         -> décompressé par notre code (tools/oodle.py)
       └─ BND4                   -> parsé par notre code (tools/bnd4_parse.py)
            ├─ .tpf  (textures)
            ├─ .flver (modèle)
            ├─ .anibnd (BND4 imbriqué)
            │     └─ Skeleton.hkx (Havok)
            ├─ .clm2 (cloth)
            └─ .hkx  (Havok)
```

## 2. DCX — FAIT

- Entiers d'en-tête **big-endian**.
- Layout observé :
  | offset | contenu |
  |---|---|
  | 0x00 | `"DCX\0"` |
  | 0x04 | u32 = `0x00011000` |
  | 0x08 | u32 dcsOffset (= 0x18) |
  | 0x0C | u32 dcpOffset (= 0x24) |
  | 0x10 | u32 fin des en-têtes (= 0x44) |
  | 0x14 | u32 début des données compressées (= 0x4C) |
  | 0x18 | `"DCS\0"` + u32 uncompressedSize + u32 compressedSize |
  | 0x24 | `"DCP\0"` + char[4] type (`KRAK` = Oodle/Kraken) |
- Décompression via `oo2core_6_win64.dll` (fourni par le jeu).

## 3. BND4 — FAIT

En-tête (little-endian) :
| offset | contenu | valeur observée |
|---|---|---|
| 0x00 | `"BND4"` | |
| 0x0C | u32 fileCount | 5 |
| 0x10 | u64 entriesOffset | 0x40 |
| 0x18 | 8 octets | `"07D7R6\0\0"` (à élucider) |
| 0x20 | u64 entrySize | 0x24 |
| 0x28 | u64 dataOffset | 0x410 |
| 0x30 | u64 | 0x47401 (à élucider) |
| 0x38 | u64 namesEnd | 0x3C8 |

Entrée de 0x24 octets :
| offset | contenu |
|---|---|
| +0x00 | i32 flags (0x40 observé) |
| +0x04 | i32 id (-1 = absent) |
| +0x08 | u64 size |
| +0x10 | u64 size (identique → donnée NON compressée) |
| +0x18 | u32 offset absolu dans le BND4 |
| +0x1C | u32 inconnu |
| +0x20 | u32 nameOffset absolu (nom en **UTF-16LE**) |

**Validation** : `dataOffset + somme(sizes) = 5 175 890` vs taille 5 175 904 (14 octets de padding final). 
Le nom des fichiers internes est un **chemin NT d'origine** : `N:\NTC\data\Target\INTERROOT_win64\parts\Face\FC_M_0240\...`

## 4. FLVER (modèle 3D) — EN BONNE VOIE

- Magic `"FLVER\0"` (6 octets). Puis octet 0x06 = `0x4C`, 0x07 = `0x00` (non identifiés).
- **FAIT** : version = `0x0002001A` (offset 0x08), famille FLVER2 (FromSoft).
- **FAIT** : `dataOffset` (u32 @0x0C) + `dataSize` (u32 @0x10) = **taille exacte du fichier**.

  | fichier | dataOffset | dataSize | somme | taille réelle |
  |---|---|---|---|---|
  | c1240.flver | 0x134D0 = 79 056 | 0xC3700 = 800 512 | 879 568 | 879 568 ✓ |
  | c1250.flver | 0x19FC0 = 106 432 | 0x471040 = 4 657 216 | 4 763 648 | 4 763 648 ✓ |
  | c5400.flver | 0x2E700 = 190 208 | 0x76A8E0 = 7 776 480 | 7 966 688 | 7 966 688 ✓ |
  | FC_M_0240.flver | 0x23950 = 145 744 | 0x2DF410 = 3 010 576 | 3 156 320 | 3 157 344 (padding 1024) |

  ⇒ les tables (bones/meshes/matériaux) vivent **avant** `dataOffset`, les données de sommet/faces **après**.
- **DÉCOUVERTE MAJEURE : les chaînes du FLVER sont en UTF-16LE** (pas d'ASCII du tout).
  Vérifié sur `c5400.flver` : 1273 chaînes UTF-16 uniques, dont les **noms de matériaux** et les
  **chemins de MTD** :
  ```
  #20#c5400_body        #20#c5400_head        #20#c5400_hair        #20#c5400_kimono
  N:\NTC\data\Material\mtd\character\c5408_hairface.mtd
  N:\NTC\data\Material\mtd\character\c5409_body_SSS.mtd
  N:\NTC\data\Material\mtd\character\c5409_head_SSS.mtd
  N:\NTC\data\Material\mtd\character\c5409_helmet.mtd
  N:\NTC\data\Material\mtd\character\c5409_kimono_Blend_AN.mtd
  N:\NTC\data\Material\mtd\character\c5409_eyeshadow.mtd
  N:\NTC\data\Material\mtd\character\c5409_hair_e_Decal.mtd
  ```
  ⇒ **le modèle déclare lui-même son identifiant** (`c5400`) : c'est notre meilleure source
  d'identification, et ça donne accès aux noms de matériaux/MTD pour le portage.
  Préfixe `#20#` devant les noms de matériaux : rôle **inconnu** (à élucider).
- **FAIT** : aucune chaîne `.dds` ni `INTERROOT` dans le FLVER ⇒ les textures ne sont
  **pas référencées par chemin** mais par index (à décoder).
- Les noms de fichiers internes des BND4 restent, eux, en **UTF-16LE** également.

## 5. TPF (textures) — FAIT (magic)

- Magic `"TPF\0"`, contient des **DDS** (mags `DDS `, en-tête `DX10`).
- Donc les textures Sekiro = DDS (avec compression type DX10/DXGI).

## 6. HKX (Havok) — FAIT (identification)

Deux échantillons observés (`Skeleton.hkx`, `*_c.hkx` du cloth) :
- Les **4 premiers octets = taille totale du fichier en u32 big-endian**
  (0x0000F840 = 63 552 ✓ ; 0x000066F0 = 26 352 ✓).
- Section `"TAG0"` (Havok **tagfile**).
- Chaîne `"SDKV"` + `"20160200"` → **Havok SDK 2016.2.0**.
- Section `"DATA"` présente.

**Conséquence majeure** : le squelette et les animations de Sekiro sont en **Havok 2016.2.0 (format tagfile)**. 
Toute conversion d'animation devra produire/écrire ce format. **C'est le risque technique principal du projet.**

## 7. Autres formats entre-aperçus

- `CLM2` : données de cloth (296 octets pour cette pièce).
- `.anibnd` : un BND4 qui contient au minimum `Skeleton.hkx` (et probablement les clips d'animation pour un vrai personnage).

## 8. MSB (map / placements) — FAIT (partiel, via les chaînes)

Les 10 maps sont dans `map\mapstudio\m10..m25_*.msb.dcx`.

- DCX **KRAK** → magic décompressé `"MSB "` ⇒ pipeline DCX validé sur un 3e format.
- **Aucune chaîne ASCII** dans le MSB : tout est en **UTF-16LE**, comme le FLVER.
- Les noms de « parts » (placements) sont en UTF-16LE et suivent la convention
  **`cXXXX_NNNN`** = `modèle` + `index d'entité` (ex. `c5400_0000`).
  ⇒ **on peut lire le casting complet de chaque map sans parser le MSB.**
- Les noms d'entités `cXXXX` sont aussi présents en version courte (`c0000`).
- Le MSB ne contient **pas** les ids d'IA en int32 simple (recherche de 540000 / 710000 = 0 résultat)
  ⇒ le lien modèle ↔ IA passe par une autre table (à trouver).
- **Règle empirique validée** : `id IA = chrId × 100` (voir `notes/02_cible_isshin.md` pour la validation).
- Outil : `tools/msb_scan.py`.

## 9. EMEVD (événements) — CHIFFRÉ → non traité

- `event\m11_02_00_00.emevd.dcx` : DCX → magic `EVD\0` (suivi de `00 FF`).
- Corps **illisible** : 0 chaîne, 0 occurrence des ids recherchés ⇒ EMEVD **chiffré** comme dans
  DS3/Sekiro. Il faudra le déchiffrer (clé connue de la communauté) avant de le lire.
- `script\*.luabnd.dcx` = BND4 de **bytecode Lua compilé** (chaînes visibles, code non).
  L'IA de Sekiro = Lua, organisée en `goal_list.lua` / `logic_list.lua` + un fichier par id d'IA
  (`540000_battle.lua`, `540000_logic.lua`, …) **et par map**.

## 10. Ce que M1 n'a PAS encore couvert

- FLVER **complet** : table de bones, meshes, matériaux, layout de sommets, index buffers.
- Contenu réel d'un `anibnd` de boss (`c5400.anibnd.dcx` = 7,25 Mo) : combien de clips, quels HKX.
- `behbnd` (state machine Havok), `param` (parambnd), EMEVD (chiffré), ESD.
- Le format `.mtd` (`mtd\allmaterialbnd.mtdbnd.dcx`, 0,4 Mo = tous les matériaux).
- Le lien texture ↔ matériau (index) et le contenu d'un `.texbnd`.

## 11. État de l'extraction (fait)

UXM a dépaqueté **tout** dans `E:\Games\Sekiro - Shadows Die Twice\` (12,3 Go en clair) :

| dossier | fichiers | taille |
|---|---|---|
| chr | 476 | 1 558 Mo |
| parts | 135 | 370 Mo |
| map | 5 447 | 6 495 Mo |
| sound | 444 | 2 184 Mo |
| param | 255 | 1,2 Mo |
| script | 22 | 1,6 Mo |
| action | 81 | 8,7 Mo |
| event | 11 | 0,1 Mo |
| menu | 183 | 181 Mo |
| mtd | 1 | 0,4 Mo |
| _unknown | 141 | 162 Mo |

`sekiro.exe` **non modifié** par UXM (vérifié). `_backup\` ne contient que d'anciens `sound\*` en vrac.
