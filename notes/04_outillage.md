# Outillage retenu (phase 1) — état et preuves

## Ce qui est FAIT et vérifié

### 1. Écriture DCX — validée (brique critique)

`tools/dcx_build.py` + `tools/roundtrip_test.py`.

**Fait mesuré** : l'en-tête DCX de Sekiro est un **préfixe fixe de 0x4C octets**
(vérifié sur 9 fichiers vanilla de 4 Ko à 8 Mo). Seules les 2 tailles de la
section `DCS` varient. Le flux compressé est **un seul bloc Oodle Kraken**.

Preuve : `python tools/roundtrip_test.py ...` sur 4 fichiers → **4/4 OK** :
préfixe identique à FromSoft, données identiques après recompression.

| fichier | vanilla | nous | résultat |
|---|---|---|---|
| `c5400.behbnd.dcx` | 58 528 o | 53 236 o | identique |
| `c5400.chrbnd.dcx` | 3 708 400 o | 3 151 121 o | identique |
| `c5400.anibnd.dcx` | 7 254 512 o | ~6,4 Mo | identique |
| `m11_02_00_00.msb.dcx` | — | — | identique |

Notre compression est même **meilleure** que celle de FromSoft (niveau Normal
côté Oodle). Le jeu n'exige pas une sortie bit-à-bit identique, seulement un
flux Kraken valide.

### 2. Compression Oodle — validée

`tools/oodle.py` : `OodleLZ_Compress` **fonctionne** avec la signature à 9
arguments. Exports confirmés dans `oo2core_6_win64.dll` (66 exports, dont
`OodleLZ_Compress`, `OodleLZ_Decompress`, `OodleLZ_GetCompressedBufferSizeNeeded`).

**Piège identifié** : sur cette DLL, `OodleLZ_GetCompressedBufferSizeNeeded`
ne renvoie PAS le pire cas (mesure : 282 pour 16 000 octets en entrée). S'en
servir comme taille de tampon écrase la mémoire et fait planter le process.
`compress()` alloue donc large (`raw + raw/8 + 64 Ko`).

### 3. Mappings FModel pour Clair Obscur — obtenus et validés

`tools/mappings/ClairObscur_Mappings.usmap` (587 832 o).

Preuve de validité (croisée avec le code source de CUE4Parse) :
- magic `0x30C4`, **version 3** (LargeEnums), HasVersioning = 0
- méthode de compression **3 = ZStandard**
- table de 53 850 noms en u16, lue intégralement sans erreur (longueur attendue
  par la version ≥ 2 « LongFName »)
- contenu cohérent : `SkeletalMesh`, `AnimMontage`, `Character` présents

### 4. Archives de Clair Obscur — non chiffrées

`pakchunk0-Windows.utoc` : IoStore **version 6**, `ContainerFlags = 0x09`
(Compressed + Indexed), GUID de clé AES vide, méthode de compression = `Oodle`.
→ **aucune clé AES nécessaire** pour FModel.

## Outils retenus pour la phase 1

| Étape | Outil | Pourquoi |
|---|---|---|
| Extraire les assets UE5 | **FModel** | IoStore 5.4, export glTF + PNG |
| Conversion glTF → FBX | **Blender** (gratuit) | formats acceptés en entrée par FLVER Editor |
| Injecter le mesh dans le FLVER | **FLVER_Editor** (Forsakensilver, X2.7) | « Import Model » : importe un FBX dans un FLVER existant **en gardant le squelette** ; conversion automatique des noms de bones Mixamo → Sekiro (`boneConvertion.ini`) |
| Empaqueter le DCX | **nos outils** | round-trip validé ci-dessus |
| Charger le mod | **Mod Engine 1** | `loadUXMFiles=1`, rien à patcher dans `sekiro.exe` |

Notes sur FLVER_Editor (lues dans son README officiel, dépôt mis à jour le
15/10/2026, release X2.7 du 07/10/2026) :
- supporte Sekiro explicitement ;
- `Import Model` (FBX/DAE/OBJ) avec normales, tangentes, UV ;
- conserve/édite matériaux, dummy points, et sait « fixer » les dummies Sekiro
  (`Dummy -> SekiroFix`) — utile pour les traînées d'épée ;
- sauvegarde un `.bak` automatiquement.

**Conséquence importante** : on n'a PAS besoin de savoir réécrire un FLVER
octet par octet pour la phase 1. La stratégie 1 (garder squelette + anims
d'Isshin, remplacer le mesh) est faisable avec un outil éprouvé.

## Ce qui reste à construire (nous)

1. `tools/repack_chrbnd.py` : reconstruire `c5400.chrbnd.dcx` à partir d'un
   `c5400.flver` modifié (writer BND4 + `build_dcx`, tous deux disponibles).
2. Arborescence de mod Mod Engine (`mods/` + `modengine.ini`).
3. Décodage FLVER « de contrôle » (bones/matériaux) — utile pour vérifier, plus
   bloquant pour produire.
