# RE4 Zombies — inventaire & architecture (M0)

> Nouveau projet : porter le mode Zombies de Black Ops 1 sur Resident Evil 4 (2005).
> Note de travail. Distingue FAIT / HYPOTHÈSE / INCONNUE.
> Dernière mise à jour : 2026-10-22 (reconnaissance initiale).

## 1. Environnement

| Élément | Valeur |
|---|---|
| Dossier projet | `C:\Users\marou\Documents\Default Project` (pas de git) |
| RE4 | `E:\SteamLibrary\steamapps\common\Resident Evil 4` |
| BO1 (Plutonium T5) | `F:\Games\pluto_t5_full_game` |
| Disque C: | 4,7 Go libres seulement → builds et assets lourds sur `E:` |
| Disque E: | 82,5 Go libres → racine de travail `E:\re4z` |
| Python | 3.14.5 |
| MSYS2 | `C:\msys64` (UCRT64, GCC 16.2) — **pas de toolchain i686 installée** |
| Absents | git, Rust, CMake, Visual Studio, Blender, Ghidra/IDA |

## 2. FAITS vérifiés (preuves incluses)

### 2.1 RE4

- Version classique 2005 : `Bin32\bio4.exe`, **9 139 840 octets**,
  `FileVersion = 1.0.0RELEASE_DEV.0`,
  SHA-256 = `19AED4AF0AB06A748FF8744D45AC5580FCD6BE6B6B7E944B1AB8822A00C8EE4A`.
- Loader ASI : `Bin32\dinput8.dll` = **Ultimate ASI Loader 9.7.4** (ThirteenAG).
- Le jeu tourne déjà avec `dgVoodoo` (`D3D9.dll`), ReShade (`dxgi.dll`/`ReShade.ini`),
  `re4_tweaks`, et le mod **MW2RE4 v32** (`Bin32\MW2RE4.asi`, SHA-256
  `DFFEDC84669BC82292BE952B702652F9D5C8F330E166063D5414DD0F45813BD2`).
- Données : `BIO4\St0` … `St7` en archives `.lfs` (LFS = archive maison du port PC).
  `BIO4\St4` contient les arènes Mercenaires : **`r400` (village), `r402`, `r403`, `r404`**
  (+ r405/r406/r40a…r411).
- `MW2RE4.log` donne les adresses exactes sur **cet** exe (mêmes 9 139 840 octets) :
  - `pG = 0x01756F3C`, `pPL = 0x017A7054`, `SatMgr = 0x01749A7C`
  - `CameraQuasiFPS::hitCheck` à `bio4.exe+0x19E213`, set camera à `+0x2F70FB`
  - `BulletHit` à `+0x286C40`, `LifeDownSet2` à `+0x1B5AF0`, `MesSet` à `+0x375BA4`
  - `ItemMgr` à `+0x2FEA2`, `EmMgr` à `+0x1CD119`, `PadRead` à `+0x254B80`.

### 2.2 Ce que fait réellement MW2RE4 (et ce qu'il ne fait pas)

C'est un **pont**, pas un portage de jeu :

- un **hôte ASI 32 bits** dans `bio4.exe` (hooks D3D9, caméra, souris, items,
  collision, dégâts, sous-titres, QTE) ;
- un **invité 64 bits** `iw4l-re4.exe` (runtime MW2) rendu dans une texture
  (960×540 par défaut) et composité en chroma key sur RE4 ;
- RE4 reste le monde : la collision proche de Leon est envoyée à l'invité
  (« collision: N triangles near Leon »), Leon est téléporté/caméra première personne,
  et **les tirs MW2 sont renvoyés à `BulletHit` de RE4** (`shots to RE4=…`).

**Conséquence capitale** : MW2RE4 ne fait **aucune IA, aucun ennemi, aucune manche**.
Les ennemis restent les ganados de RE4 ; MW2 ne fournit que les armes, le HUD et la vue FPS.
Donc « le même mod mais avec BO1 » ne donnerait **pas** le mode zombies : il donnerait
des armes BO1 par-dessus RE4. Le mode zombies doit être construit.

### 2.3 IW4L (le runtime de l'invité) est open source

- `https://github.com/vladtrc/iw4L`, **Apache-2.0**, Rust + Bevy/wgpu, ~1,1 k★.
- Runtime CoD expérimental : charge les assets d'une install MW2 possédée,
  a un **runtime GSC**, des bots, un rendu, un réseau, des démos.
- Les **lanes d'assets couvrent aussi T5 (Black Ops 1) et T6** (`docs/FAMILIES.md`,
  `docs/MAP-LOAD.md`). Ce n'est pas encore un « T5 complet », mais la lecture des
  fastfiles/armes/matériaux BO1 existe.
- Le code du **pont RE4** (MW2RE4) est **privé** (PDB : `F:\ModProjects\MW2-RE4\...`),
  mais la partie iw4L est publique et la technique est reproductible.

### 2.4 RE4 est décompilé (GameCube, debug) — mine d'or

`https://github.com/adonis-singh/re4` (téléchargé dans `E:\re4z\refs\re4-decomp`),
décompilation byte-identique du build debug GameCube. Le port PC reprend la même logique.

Points directement exploitables :

- `cEmMgr` = `cManager<cEm>` : pool de travaux de **`EM_WORK_SIZE = 0xDE0`** octets.
  La taille du pool vient de la room : `EmMgr.arrayAlloc(ConsGetRoomValue(CONS_R_NEM))`
  (`src/game/game.cpp:399`). **On peut donc augmenter le nombre d'ennemis** en hookant
  `CONS_R_NEM` (ou en l'écrivant dans les données de room).
- `EmSetFromList2(no, flag)` (`src/game/em_set.cpp`) crée **un ennemi à la demande**
  depuis `pG->Em_list[no]` (256 entrées : id, position, rotation, hp, flags, room).
  C'est le point d'entrée naturel pour un spawner de zombies.
- `EmSetFromList()` peuple la room au chargement à partir de la même liste.
- `RouteCkToEm()` / `RouteCkToPos()` (`src/game/route_ck.cpp`) : pathfinding A*
  sur les **RTP** de la room (points + liens + table de next-hop). Les arènes
  Mercenaires ont ces données, donc les ennemis savent poursuivre le joueur.
- `SatMgr.getFloor(...)` et `rckLineHitCheck(...)` : requêtes de collision/raycast
  utilisées par le jeu — réutilisables pour un contrôleur FPS.
- `cEm` : `hp/hp_max` en `0x320`, `dmg` en `0x324`, `pos`, `ang`, `emset_no`,
  `status`, `flag`, `Guard_r`, drop d'item… (offsets documentés dans `include/em.h`).
- **Mercenaires** (`src/game/mercenaries.cpp`) : arènes `r400` (village), `r402`,
  `r403`, `r404`, mode horde avec spawns continus, score, combo, temps bonus.
  C'est la **meilleure base** pour un mode manches : une room unique, déjà équipée
  en points de spawn et en route data.
- `em10` (ganado) : variantes 0x10..0x1F, IA de poursuite/attaque/coup,
  points de vie et « Omake » (score Mercenaires). Les ganados du village
  ont déjà une démarche traînante proche d'un zombie.

### 2.5 BO1 (T5) installé

- `zone\Common\common_zombie.ff` (51 Mo) contient le mode zombies (GSC, HUD, sons, etc.).
- Cartes zombies présentes : `zombie_coast`, `zombie_theater`, `zombie_pentagon`,
  `zombie_temple`, `zombie_cosmodrome`, `zombie_moon`, + remakes WaW
  (`zombie_cod5_asylum/factory/prototype/sumpf`) et `zombietron`.
- Assets extractibles avec **Wraith Archon** (DTZxPorter) : xmodels, matériaux/images,
  sons. Les scripts T5 se décompilent avec `gsc-tool` (xensik) ou équivalent.
- Plutonium T5 est installé (`%LOCALAPPDATA%\Plutonium`), mais **pas de dossier `mods`**
  dans le jeu : à créer si on veut un jour charger du contenu T5 custom.

### 2.6 Outils/état de la machine

- Python 3.14 OK ; `py7zr`, `psutil`, `openpyxl` installés ; pas de numpy/Pillow.
- MSYS2 UCRT64 (GCC 64 bits) ; **pas de GCC 32 bits** → à installer
  (`mingw-w64-i686-gcc`) pour une ASI 32 bits.
- Pas de Blender (nécessaire pour le pipeline modèles), pas de Ghidra/IDA.
- Pas de git : utiliser les ZIP GitHub ou installer git.

## 3. HYPOTHÈSES de travail (à valider par des tests)

| # | Hypothèse | Test de validation |
|---|---|---|
| H1 | On peut porter `CNS_R_NEM` de r400 à 32–40 sans crash | hook + spawn de 30 ganados |
| H2 | `EmSetFromList2` accepte des entrées ajoutées à chaud dans `pG->Em_list` | spawn à une position arbitraire |
| H3 | Les RTP de r400 couvrent toute l'arène | zombie envoyé à l'autre bout |
| H4 | Un contrôleur FPS maison sur `SatMgr` fonctionne (gravité, murs, sol) | déplacement + saut dans r400 |
| H5 | On peut remplacer les textures des ganados par des textures zombies | remplacement `.lfs`/TEX |
| H6 | On peut importer un modèle BO1 (xmodel → PMD) sur le squelette ganado | 1 modèle de zombie animé |
| H7 | Le HUD BO1 peut être dessiné en D3D9 sans conflit avec dgVoodoo/ReShade | overlay stable |

## 4. Architecture recommandée

### Option A — « RE4 héberge le mode zombies » (recommandée)

`bio4.exe` + une ASI 32 bits `RE4Z.asi` :

- **Monde/joueur** : RE4 (room Mercenaires ou room histoire), collision, lumières, sons.
- **Contrôleur FPS** : caméra première personne, souris, WASD, sprint, saut,
  via les hooks caméra/souris et les requêtes `SatMgr` (précédent MW2RE4).
- **Zombies** : ennemis RE4 (`cEm10`) spawnés par notre director,
  pool augmenté, pathfinding RTP natif, modèles/textures zombies (V1 = ganados
  retexturés, V2 = modèles BO1).
- **Manches/points/perks/box/PaP/power-ups** : logique C++ dans l'ASI,
  paramètres extraits du GSC BO1 (formules exactes).
- **Arsenal** : V1 armes RE4 remappées sur les stats/noms/icônes BO1
  (comme MW2RE4 mappe les armes MW2) ; V2 viewmodels BO1.
- **HUD/UI** : rendu D3D9 avec les assets BO1 extraits (compteur de manche,
  points, munitions, perks, power-ups, hitmarkers, écran de fin).
- **Audio** : mixeur XAudio2/DirectSound, sons BO1 extraits.

Avantages : monde RE4 authentique, pas de conversion de map, offline, pas de
dépendance à Plutonium, itérations rapides, précédent technique prouvé (MW2RE4).
Limites : IA/anims « RE4 » au départ, pas de co-op (RE4 n'a pas de netcode),
contrôleur FPS à écrire.

### Option B — « T5L » : moteur BO1 réimplémenté + maps RE4 converties

Fork d'IW4L avec lane T5 complète, GSC zombies, maps RE4 converties en zones T5.
Authenticité maximale, co-op possible via le réseau d'IW4L, mais :
conversion RE4 → BSP/zones/navmesh, rendu BO1 (on perd le rendu RE4), et IW4L
est un moteur expérimental incomplet. **Mois de travail avant la première manche.**

### Option C — « pont invité » : T5/BO1 comme cerveau, RE4 comme corps

Étendre le schéma MW2RE4 : l'invité gère les armes/HUD, voire l'IA, RE4 fournit
le monde et la collision. Séduisant, mais il faut nourrir l'invité en collision
et navmesh, composer les zombies, et synchroniser deux simulations.
**Risque maximal, à garder comme évolution V3.**

### Verdict

**Option A**, avec le mode **Mercenaires** comme hôte (room `r400` village),
puis les 3 autres arènes. On obtient une boucle jouable vite, et on ajoute
l'authenticité BO1 par couches (HUD → sons → modèles → armes → perks).

## 5. Plan par sprints (proposition)

### Sprint 0 — Preuves (2–4 jours)

1. Installer le toolchain **i686** (MSYS2) et créer `E:\re4z\game` (copie légère
   avec junction vers `BIO4`), pour ne pas casser l'install MW2RE4.
2. ASI squelette : pattern scanner, log de `pG/pPL/EmMgr/SatMgr`, hook D3D9,
   rectangle de debug.
3. Lancer une partie Mercenaires village, logger `room_id`, `CNS_R_NEM`,
   `pG->Em_list`, `RTP` (nb points/liens), positions.
4. **Test horde** : porter le pool à 32 et spawner 30 ganados autour du joueur.
5. **Test FPS** : caméra première personne + déplacement capsule sur `SatMgr`.

Critère de sortie : 30 zombies qui poursuivent le joueur en FPS dans le village,
sans crash, avec une boucle stable.

### Sprint 1 — Boucle zombies (1–2 semaines)

- Director de manches (formules BO1), points, spawn budget, max alive.
- HUD minimal (manche, points, munitions) en D3D9.
- Armes RE4 + dégâts/headshots, hitmarkers.
- Menu de debug (F1) : manche, spawn, perks, noclip.

Critère : survivre jusqu'à la manche 10 avec des ganados, HUD lisible, Game Over.

### Sprint 2 — Habillage BO1 (2–3 semaines)

- HUD BO1 complet (assets T5), polices, icônes, transitions de manche.
- Textures zombies, variantes (walker/runner/crawler), sang/gibs.
- Audio BO1 (grognements, stingers, perks, box).
- Perks (4), Mystery Box, power-ups (Max Ammo, Insta-Kill, Double Points).
- 4 arènes Mercenaires.

### Sprint 3 — Arsenal & finition (3–4 semaines)

- Viewmodels/armes BO1 (renderer dédié ou conversion), PaP.
- Modèles BO1 (xmodel → PMD) et animations.
- Menus, options, sauvegarde, équilibrage.
- Recherche co-op (hors scope V1).

## 6. Risques principaux

1. **Nombre d'ennemis / perf** : pool RE4 limité par `CNS_R_NEM` ; 24–32 zombies
   simultanés à 30 fps est l'inconnue n°1. Test Sprint 0.
2. **Contrôleur FPS** : Leon est animation-driven ; téléport + caméra FPS marche
   (MW2RE4), mais il faut gérer collisions, pentes, escaliers, portes.
3. **Viewmodel/armes BO1** : le plus gros sous-projet visuel ; V1 avec armes RE4.
4. **Import modèles/animations BO1** : format PMD + squelette ; pipeline Blender
   à construire, retargeting à valider.
5. **Rooms histoire multi-room** : streaming/portes ; les arènes Mercenaires
   contournent le problème pour V1.
6. **Co-op** : impossible nativement dans RE4 ; nécessiterait un netcode complet
   ou l'option B.
7. **Conflit avec MW2RE4** : les deux ASI hookent caméra/D3D9 → développer dans
   une copie du jeu, ne pas empiler les deux.

## 7. Ressources

| Ressource | Usage |
|---|---|
| `E:\re4z\refs\re4-decomp` | décompilation RE4 (GameCube) : structures, IA, spawn, routes |
| `https://github.com/vladtrc/iw4L` | runtime CoD Rust, lanes T5/T6, GSC |
| `MW2RE4.log` | adresses et patterns validés sur notre `bio4.exe` |
| `F:\Games\pluto_t5_full_game\zone\Common\*.ff` | assets/GSC BO1 |
| Wraith Archon | extraction xmodels/textures/sons BO1 |
| `gsc-tool` (xensik) | décompilation GSC T5 (formules de manches) |
| REA (`morluto/rea`) | reverse engineering assisté du binaire PC si besoin |

## 8. Décisions en attente

1. **Direction** : Option A (native, recommandée) / B (T5L) / C (pont).
2. **Caméra** : FPS façon BO1 (recommandée) / troisième personne RE4.
3. **Armes V1** : arsenal RE4 remappé BO1 (rapide) / arsenal BO1 complet (long).
4. **Multijoueur** : solo V1 (recommandé) / co-op exigé (change l'architecture).
5. **Première map** : arène Mercenaires village `r400` (recommandée) / village
   histoire `r100` (multi-room, plus dur).
