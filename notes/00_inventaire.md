# Inventaire du projet — Portage de Simon (Clair Obscur: Expedition 33) vers Sekiro

> Note de travail. Distingue explicitement FAIT / HYPOTHÈSE / INCONNUE.
> Dernière mise à jour : phase M0.

## 1. Environnement

| Élément | Valeur |
|---|---|
| Dossier projet | `C:\Users\marou\Documents\Default Project` (vide au départ, pas de git) |
| Sekiro | `F:\Games\Sekiro - Shadows Die Twice` |
| Clair Obscur | `E:\Games\Clair Obscur - Expedition 33` |
| Python | 3.14.5 (`%LOCALAPPDATA%\Python\pythoncore-3.14-64`) |
| OS | Windows |

## 2. FAITS vérifiés (preuves incluses)

### Sekiro
- **Version 1.6.0.0** (= 1.06, dernier patch). Source : métadonnées de `sekiro.exe`.
- AppId Steam **814380** ; exécutable patché par un émulateur Steam (CODEX, `steam_emu.ini`) ; repack (dossier `_Redist\fitgirl.md5`).
- Modloader = **Mod Engine 1 de Katalash** (`dinput8.dll` + `modengine.ini`), pas Mod Engine 2.
  - `useModOverrideDirectory=1`, `modOverrideDirectory="\mods"`, `loadUXMFiles=0`, `cacheFilePaths=1`.
- Les données sont dans **`Data1..Data5.bdt` + `Data1..Data5.bhd`** (≈ 12,3 Go au total). Il n'y a **pas de fichiers de jeu en vrac**.
- **Les `.bhd` sont chiffrés** : entropie mesurée = **7.999 bits/octet**, 256/256 valeurs d'octets utilisées, aucun magic ASCII (`BHD5`/`BND4`) trouvable dans tout le fichier.
  → Conséquence : on ne peut pas lire l'index des archives vanilla sans clé ni outil existant.
- Le premier bloc de `Data1.bdt` commence par `DCX\0` (mais c'est probablement le premier fichier stocké, pas le conteneur).
- Le dossier `mods\` contient déjà des fichiers Sekiro **non chiffrés** (issus de mods) :
  `Parts\*.partsbnd.dcx` (dont `fc_m_*.partsbnd.dcx`, `wp_a_0300.partsbnd.dcx`), `param\gameparam`, `Sound\*.fsb`, des `.png`.
- **Format DCX (établi empiriquement sur `fc_m_0000.partsbnd.dcx`)** :
  - Entiers d'en-tête **big-endian**.
  - `0x00 "DCX\0"`, `0x04 u32 = 0x00011000`, `0x08 u32 dcsOffset=0x18`, `0x0C u32 dcpOffset=0x24`, `0x10 u32 finEnTêtes=0x44`, `0x14 u32 débutDonnées=0x4C`.
  - `0x18 "DCS\0"` + `u32 uncompressedSize` + `u32 compressedSize`.
  - `0x24 "DCP\0"` + `char[4] compressionType` → **`KRAK`** (Oodle/Kraken).
- **Décompression Oodle opérationnelle** via `oo2core_6_win64.dll` (fourni par le jeu) appelé en ctypes.
  → Résultat : `5,175,904` octets décompressés, magic **`BND4\0`**. Chaîne `DCX → Oodle → BND4` validée.

### Clair Obscur: Expedition 33
- **Unreal Engine 5**, layout standard : `Sandfall\Content\Paks\*.pak/.utoc/.ucas` (IoStore), chunks 0 à 999.
- Mods déjà présents dans `Paks\~mods\` : `SimonStartsP3_P`, `DivergentStar_NoPhase2_P`, `randomizer_P`, `Verso_Sung_JinWoo_P` → **le jeu est moddable par pak** et il existe une scène de modding active.
- **`Manifest_UFSFiles_Win64.txt`** (31 Mo, **256 011 lignes**) = liste complète des assets avec leur chemin. Très utile pour cartographier sans extraire.
- Assets de Simon identifiés sous :
  `Sandfall/Content/Characters/Enemies/HumanEnnemies/Simon/`
  - `SK_Simon.uasset` (SkeletalMesh), `SK_Simon_Physics.uasset` (PhysicsAsset)
  - `SM_Simon_Sword_UE5_2.uasset`, `SM_FX_Simon_SwordOptimized.uasset` (épée)
  - `BP_EnemyBattle_Simon.uasset`, `_ALPHA`, `_Phase2` (logique du boss)
  - `Animations/` : `ABP_Simon` (AnimBlueprint), `BS_Simon_UE5` (BlendSpace), `Simon_Idle01/02`, `walk`, `run`, `Dash_in/Out`, `Skill_1..5`, `Skill04/06/07/08`
  - `Sequences/` : `SEQ_Simon_Skill_1..12` (combos, phase switch, eject) — **c'est là qu'est la structure des attaques**
  - `PhysicsSetUp/` : `ABP_PostProcess_Simon`, `DA_Kawai_Simon`
  - `Textures/` : BaseColor/Normal/ORM pour Head/Top/Bottom/Coat + `New_Sword/` (lame + manche)
  - Cheveux : `Characters/Hair/NPCs/Simon/`
- Squelette du corps : **pas de `*_Skeleton` dans le dossier Simon**. Candidat probable = **`Sandfall/Content/Characters/UE4_Skeleton.uasset`** (squelette commun humanoïde) → **HYPOTHÈSE À VÉRIFIER** en lisant la référence dans `SK_Simon.uexp`.

## 3. HYPOTHÈSES corrigées ou en attente

| Hypothèse initiale | Statut |
|---|---|
| Sekiro PC = fichiers en vrac | **FAUX** → archives `.bdt/.bhd` |
| `.bhd` = BHD5 en clair | **FAUX** → chiffré (entropie 7.999) |
| Modèle Sekiro = FLVER2 dans `.chrbnd.dcx` | **NON VÉRIFIÉ** (à confirmer en dépaquetant un `.bnd`) |
| Animations Sekiro = Havok HKX dans `.anibnd.dcx` | **NON VÉRIFIÉ** |
| Behavior = `.behbnd.dcx`, params = `.parambnd.dcx`, events = EMEVD | **NON VÉRIFIÉ** |
| Mod Engine 2 | **FAUX** → Mod Engine 1 |

## 4. INCONNUES restantes (bloquantes ou non)

1. **Comment lire `Data*.bhd`** (index chiffré) → soit outil existant (UXM / WitchyBND), soit clé. *Bloquant pour accéder aux fichiers vanilla (Wolf, Isshin…).*
2. **Format exact des modèles/animations Sekiro** → à établir sur fichiers réels.
3. **Structure BND4** : header pas encore entièrement décodé (le magic `BND4` est vu, `fileCount` probablement 5, mais l'offset exact des champs reste à confirmer).
4. **Rig de Simon** : squelette partagé ou dédié ? nombre d'os ? compatibilité avec Sekiro ?
5. **Format des animations UE5** de Simon (AnimSequence) et **existence d'un outil de conversion** vers le format Sekiro. **C'est le risque n°1 du projet.**
6. **Mapping gameplay** : Clair Obscur est un RPG au tour par tour ; Sekiro est un action temps réel. Les "patterns" de Simon devront être **réinterprétés**, pas transposés tels quels.

## 5. Livrables produits

| Fichier | Rôle |
|---|---|
| `tools/scan_sekiro_archives.py` | Sonde les magics des archives Sekiro |
| `tools/oodle.py` | Wrapper ctypes sur `oo2core_6_win64.dll` (décompression Kraken) |
| `tools/dcx_inspect.py` | Parse + décompresse un DCX Sekiro (sortie dans `_work/extracted`) |
| `notes/00_inventaire.md` | Ce document |

## 6. Règle de travail

- On n'écrit **jamais** dans les dossiers de jeu depuis un script d'analyse. Sorties → `_work/`.
- Toute affirmation de format doit être adossée à une observation sur des octets réels.
