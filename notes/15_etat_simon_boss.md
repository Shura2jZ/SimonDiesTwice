# 15 — ÉTAT : Simon boss indépendant (c5460)

Dernière MAJ : 2026-11-26. Session « passage à l'implémentation ».
Légende : **[F]** vérifié fichier · **[T]** testé/validé outil · **[G]** validé en jeu · **[H]** hypothèse.

## 1. Fait (avec preuve)

| Bloc | État | Preuve / fichier |
|---|---|---|
| ID neu fs c5460 (ni vanilla 129 chrbnd, ni LoR 31) + familles 546/25460 vierges | **[F/T]** | scan 2026-11-16 : `chr/c5460*` absent, NpcParam/Think/Behavior/Atk '546' vide |
| Règle params : NpcParam.behaviorVariationId → Think.battleGoalID = ×10 ; BehaviorParam rowID = 2e8 + var×1000 + k | **[F]** | template Isshin 54000000 : var=53200, battleGoalID=532000 ; familles 253200000…/241000100… |
| `BndPatch.exe` clone/patch BND4 (rename identitaire, protection .flver/.clm2, remplacements, regen hash native) | **[T]** | `_work/tools/cs/BndPatch.cs`, compilo OK ; usage par build_c5460 |
| `build_c5460.py` 4 phases | **[T]** | archives `_work/simon_boss/chr/c5460.{chrbnd,behbnd,anibnd,texbnd}.dcx` (24,7 Mo) — 0 résidu, FLVER Simon = mod installé (md5 fa991d7a409c), DCX roundtrip OK, 280/4/4+4 entrees |
| `MsbPatch.exe` (list/retarget/add, diff 0 hors cibles, DCX natif) | **[T]** | sous-agent : `_work/simon_boss/msb/` + `msb_patch_report.md` ; retarget `c7300_0000`, ajout `SIMON_SPAWN` testés sur copie m20_00_00_00 |
| Voie d'installation modengine = overlay `mods/` (loose, **cacheFilePaths=0** = détection à chaud) | **[F]** | `F:/Games/.../modengine.ini` |
| Params : overlay déjà présent `mods/param/gameparam/gameparam.parambnd.dcx` (+.bak) | **[F]** | idem |
| Recette LoR reconstituée (notes/14) : HKB = clone hôte + patch ID, TAE cloné, familles params neuves, spawn MSB | **[F]** | notes/14 |
| Git : commits réguliers | **[T]** | `5e1f865` état initial, `7306f01` outils c5460 |

## 2. En cours
- **Isolation crash baseline** : boot SANS nos 6 fichiers en cours (~7 min/cycle) ; si baseline propre → retest incrémental (params → chr → msb) ; si baseline crash → problème environment (ReShade/FPS unlock) indépendant.

- **ParamEdit.exe** (sous-agent) : édition PARAM (list/dump/set/add) — attendu pour créer les lignes 54600000.
- Reemballeur bundle gameparam (pipeline extract → edit → `bnd4_build.rebuild` → DCX) : à écrire (dès ParamEdit).

## 3. Fichiers touchés (cette session)

- `tools/build_c5460.py` **[neuf, git]**
- `_work/tools/cs/BndPatch.cs` **[neuf, git]**
- `_work/simon_boss/chr/*` (4 dcx), `_work/simon_boss/tmp/*`, `_work/simon_boss/build_c5460.log`
- `_work/simon_boss/msb/*`, `_work/simon_boss/msb_patch_report.md`, `_work/tools/cs/MsbPatch*` (sous-agent)
- `[git] .gitignore` (_work/), commits `5e1f865`, `7306f01`

## 4. Derniers tests

1. `build_c5460.py tout` → 3 archives + texbnd, vérifs internes OK (voir log).
2. `MsbPatch list/retarget/add` sur copie MSB → diffs hors cibles 0 (rapport sous-agent).

## 5. Points ouverts

- [x] Lignes param 54600000 (clone hôte validé ; familles **non** divergentes en phase A — variationId 53xxx conservée, familles 54600 pour phase attaques).
- [x] Bundle `gameparam` recompilé + installé (backup `.bak` + manifeste).
- [x] Install test 6 fichiers + MSB (tool `implantation_simon.py installer`, backups complets via `reverter`).
- [x] **Boot in-game sain avec l'ensemble installé** (titre à +140 s, `obs_140.png`).
- [ ] **Apparition du modèle c5460 en carte** — nécessite gameplay utilisateur (sauvegarde → m20_00_00_00 record `c7300_0000` aux coord (-828,118,642)) ; pas d'input clavier envoyé de mon côté.
- [ ] Greffe du clip Simon slot `a000_003080` + évènements AttackBehavior TAE (phase 3).
- [ ] Famille Behavior/Atk 54600 + HKB (states AttackXXX → attaque exécutable IA).
- [ ] Incertitudes résiduelles : sib modèles, texbnd model-keyed vs name-keyed [H], entityID dupliqué du clone MSB (option `--entity-id`), 41 EMEVD LoR non décodés (non bloquant).

## 6. Prochaine étape immédiate

1. Vous (ou mode lecture utilisateur) : charger une sauvegarde, se rendre aux coordonnées du record → **voir apparaître Simon (modèle c5460)** ; si absence/crash : me renvoyer le crash.log.
2. Côté outils (sans jeu) : `build_c5460.py anibnd --clip a000_003080_simon.hkx` + familles params d'attaque 54600 → signez le début de la phase 3.

## 7. Session implémentation — faits ajoutés (2026-11-25)

- **ID c5460** retenu ; familles libres confirmées ; **hôte = c5400 (Isshin)**.
- **Outils neufs** : `tools/build_c5460.py`, `_work/tools/cs/BndPatch.cs` (rename identitaire + protection .flver/.clm2 + regen hash BND4 native), `_work/tools/cs/ParamEdit.cs` (sous-agent : add/copy/set/dump/list ; interdiction d'écriture in-place jeu/extract), `_work/tools/cs/MsbPatch.cs` (sous-agent : list/retarget/add ; 0 diff hors cibles), `tools/implantation_simon.py` (extraire/appliquer/packer/verifier/installer/reverter avec backups `nouveaux.txt` + `.avant`).
- **Archives c5460 construites & vérifiées** : chrbnd (FLVER Simon md5 fa991d7a409c, 42 patches identitaires, 0 résidu), behbnd (12 patches), anibnd (278 patches/280 entrées), texbnd (clone c5409) → `_work/simon_boss/chr/`.
- **Params** : NpcParam/Think 54600000 = clones identiques du hôte (diff auteur = id seul, 351/351 cellules) ; bundle recompilé (138 entrées, DCX roundtrip OK).
- **MSB** : record `c7300_0000` de `m20_00_00_00` retargeté → c5460/54600000/54600000 ; installé.
- **Install test** : 6 fichiers dans `mods/` (backup `_work/mod_backup/c5460_20261125_*` puis re-`installer` ; backups sauvegarde de jeu `_work/simon_boss/backup_sauvegarde/S0000_191210.sl2`).
- **Tests in-game** :
  1. boot #1 (18:29) : crash « Fatal Application Exit » AV 0xC0000005, backtrace = **Scaleform::Render::Matrix2x4** (UI) ; non reproductible aux boots suivants.
  2. baseline sans nos fichiers : 14 min sans crash puis fermeture externe.
  3. test #2/#3 avec fichiers : fermeture propre externe (« Shutdown initiated » 19:14:51 = l'utilisateur ferme la fenêtre plein écran pendant mes tests).
  4. test #4 observationnel : **TITRE ATTEINT à +140 s avec l'ensemble installé** (`obs_140.png`) — aucun crash, crash.log inchangé.
- **Découverte outil** : `param_lire` biaisé (base 0x48, id@+16 → rang -1) — **corrigé** (base 0x40, id@+0, u64@+8/+16). Re-vérifier les lectures param LoR/notes 12-14 quand concernées.
- **Levier d'observation** : jeux de captures automatiques (`capture_sekiro.ps1`, `obs_*.png`), logs séquentiels `sekirofpsimgui.log` (init ~5 s, swap chain à +3 s).

## 8. Points ouverts (mise à jour)

1. **Apparition en carte** = test utilisateur (charger une sauvegarde, aller à la position record m20_00_00_00 (-828,118,642)) ou axe save-game à définir — n'envoie AUCUN input clavier pour ne plus perturber le poste.
2. Crash #1 Scaleform : à surveiller (probabilité isolé/environnement ; observé seulement 1×).
3. Phase suivante hors test : greffe clip Simon slot `a000_003080` (`build_c5460.py anibnd --clip …`), familles Behavior/Atk 54600, cmsgs/AttackXXX de l'HKB.
4. Relecture biais des anciennes valeurs params (rang -1) dans notes 12-14.

## 9. Relocalisation spawn → m11_01_00_00 (château d'Ashina)

- Abandon spawn Temple m20 : fichier retiré de mods/ (purge) ; anciens cibles docs.
- Choix carte : **m11_01_00_00** = bâtiment principal du château (indices file : stack
  narratif y=1.66/32/54 avec records samurai residence/sickbed conversation NPC —
  c5410/c5430/c5060/c5020 + c5430 even Isshin story) ; sol anchor = trio de records
  debout y=54.00±0.04.
- Spawn = **ADD** `SIMON_SPAWN` (exemplaire c5430_0000, entity -1, pos
  **(-111.8, 54.0, 237.4)**, dist 3.0 m à c5430_0000 / 3.8 m à c5060_0001 / 9.9 m
  c5060_0000) — records vanilla intacts (MsbPatch : diffs hors cibles 0).
- Vérifs installés : models 40→41 (+c5460), ennemis 284→285, ligne conforme,
  chr/param md5 **inchange**, m20 absent ; revert = `implantation_simon.py reverter`
  (nouveaux.txt + .avant reconstruits dans c5460_20261125_215815).
- Route assumée : idole **« Ashina Castle: Dojo »** (écran d'arrivée ≈ salle intérieure
  étage y=54). [INCONNU] appartenance nom/idole exact — test utilisateur tranchera,
  pivot immédiat possible (positions candidates m11_00 y≈-50 cour).

## 10. Diagnostic invisibilité SIMON_SPAWN (session 2026-11-26, MAJ)

Preuves sur le FICHIER INSTALLE (out `_work/tools/cs/MsbForensics.exe`, relecture
MSBS + reflection de TOUS les champs + coupe hex + --max-entity) :

1. Record present et seriealise dans mods/.../m11_01_00_00.msb.dcx (offset UTF16
   0x4fbba0 ; relecture = Parts.Enemies total 285 et non Dummy) : OK.
2. Section = Parts.Enemies (vraie section NPC ennemi) : OK.
3. ModelName = "c5460" ; Models.Enemies contient c5460 avec SibPath standard
   N:\NTC\data\Model\chr\c5460\sib\c5460.sib (meme gabarit que c5430) : OK.
4. NPCParamID = 54600000, ThinkParamID = 54600000 ; NpcParam row presente ;
   NpcThinkParam 54600000 = clone + battleGoalID 540000 (chaine Behavior host) : OK.
5. EntityID **-1 = unique sur 285** (ref c5430_0000 = 1110920) => CAUSE : record
   jamais instancié par le système d'entités de carte -> invisible (mais parse OK).
6. Tous autres champs identiques a ref vanilla (Unk1, Gparam, shadow flags,
   LodParamID, CollisionPartName h012100, Scale 1,1,1, CharaInit -1, SibPath vide)
   => format strictement identique. Seules diffs legitimes : Nom/Model/NPC/Think/Pos.
7. Archives c5460 : verifier = 4/4/280 entrees, 0 residu, FLVER = source Simon : OK.
8. Sol/hauteur : Position Y 4 cm de c5430_0000 meme plancher ; culling/shadow
   flags conformes ref. Non-exclu en dur = collision mesh (jamais testable hors jeu).

Correction : **EntityID -1 -> 1120624** (max carte 1110920/1120623, libre +1 ; outil
`MsbForensics --max-entity`). Bug racine : constante `--entity-id -1` codee dans
`implantation_simon.py installer` (ecrasait les passes manuelles) ; remplacee par la
constante `ENTITE = 1120624` commentee. Installe : cd6e0c3eaf48 ; 0 record a -1.
Revert : backup c5460_20261126_111312 (avant = MSB VANILLA + param 182922 +
nouveaux.txt 6 fichiers).

## 11. Diagnostic apparition : recette EMEVD = cause + correctif (branche diag-apparition)

**Variante de mission** : test concentre sur la zone de l'idole Tour Lookout
(天守展望階, nom interne ; UI = Upper Tower), un seul test in-game, plus aucun
test toit (record SIMON_ROOF supprime de l'etat courant). Branche git
`diag-apparition`.

### 11.1 VÉRIFIÉ dans les fichiers (preuves + origine)

| Element | Preuve |
|---|---|
| Ennemis vanilla toujours referencés par leurs evenements carte | Scan des EMEVD du jeu par u32LE sur les EntityID MSB : 196/284 ennemis de m11_01 ont >=1 ref (c5430_0000 : 31 refs ; c1001_0006 : 39 refs ; idole 1111952 : 8 refs). Les quelques 0-ref (c1000_0007...) = spawns conditionnels/secondaires, a confirmer in-game. |
| Nos ids precedents 1120625/1120626 : 0 ref dans tout EMEVD | scan des 11 fichiers m11_01* avant patch : 0 occurrence. |
| Deduction : record sans ref evenementiel = jamais active | le systeme d'entites de carte declenche l'instanciation via les instructions de la carte ; reste a confirmer par test. |
| Unicite EntityID stricte | 284/284 ennemis vanilla = 284 ids uniques ; LoR m11_00 = 187 recs / 185 ids + 2 (-1) => jamais de doublon : recette = id UNIQUE + reference evenementielle. |
| **Recette LoR (audit reel)** | `EvdPatch find` sur `E:/lor_x/event/m11_00_00_00.emevd.dcx` : leur boss custom Gale (c2200) eid 2200000 = 2 instructions dans l'evenement 11106012 : `bank=2004 id=29 args=(2200000,0)` puis `bank=2004 id=5 args=(2200000,1)` (arg1 = id, arg2 = etat). |
| Meme bank/id dans le vanilla | m11_01 : garde d'idole c1001_0006 = `2004/5 (1110952,1)` dans l'evenement 11110100 ; c1000_0006 = `2004/29 (1110921,0|1)`, `2004/7`, `2003/5`... => bank 2004 = gestion des entites de carte. |
| LoR reecrit bien ses evenements | fichiers plus gros que le jeu : `m11_00_00_00.emevd.dcx` jeu 16 480 O vs LoR 24 795 O ; ils shipent 41 `.emevd.dcx` vs 11 pour le jeu ; compte LoR = 136 evenements / 3248 instr. |
| Fichiers sains | MSB relecture diff=0 ; event re-edite par EMEVD.Write (SoulsFormats, DCX conserve) ; **diff logique instruction par instruction : jeu = 3939 lignes, patche = 3943, i.e. EXACTEMENT +4 lignes (les 4 clones), 3935 lignes identiques**, headers evenements inclus. |
| Positions Tour Lookout | idole 天守展望階 eid 1111952 @ (-121.33, 54.05, 233.28) via idoles_xy.txt (BonfireWarpParam ∩ objets). Sol plancher Y=54.1. Degagement calcule (objdump+mapdump, y bornes) : PROBE (-119.5,54.15,237.5) = 4,60 m autour, 4,6 m de l'idole ; SIMON (-116,54.15,240.8) = 5,80 m autour, 9,2 m de l'idole, 4,8 m d'ecart a la sonde. |
| Installation | manifeste : event 770d72116256 (nouveau), MSB d1e246ad85e6 (backup 111e27411731), 4 chr + param inchange ; hashes installe = copie travail 4/4 ; ids 1120625/626 = 1 occurrence chacun ; max entity Enemies=1120626 ; jeu base intact (event base 162 ev/3777 instr, msb base 1fa1588f, param base f6bca74f) ; `mods/event/` = 1 fichier. |
| Champs records | reflexion MsbForensics : SIMON vs sonde = memes champs TOUS sauf NPC/Think/Model/Position/EntityID (Structure Ennemis propre, CollisionPartName h012100, Scale 1, culling ok). |

### 11.2 À CONFIRMER in-game seule
- Chargement de `mods/event/m11_01_00_00.emevd.dcx` (ModEngine, `showDebugLog=1`).
- Activation effective des 4 instructions clonees (elles vivent dans l'evenement 11110100 = init de zone idole o� deux samourais vanilla de la meme paire sont presents).
- Visibilite c5460 + NpcParam 54600000 (DispMask 17-20 heterogenes = derniere inconnue).
- Matrice attendue : sonde visible + Simon non => cause = param/FLVER c5460 (Test C) ; aucun des deux => event/zone (pivot vers event 0) ; les deux visibles => **succes**.

### 11.3 Etat courant livre (MIS A JOUR)
Sur la branche **diag-apparition** :
- `mods/map/mapstudio/m11_01_00_00.msb.dcx` : + `PROBE_VANILLA` (clone **c1001_0009** = garde vanilla, npc/think 10010000, eid **1120625**, pos **-119.5,54.15,237.5**) + `SIMON_LOOKOUT` (c5460, npc/think 54600000, eid **1120626**, pos **-116,54.15,240.8**) ; aucun record vanilla touche ; 286 ennemis ; ids uniques ; 0 EntityID -1 ; repart TOUJOURS du vanilla (pas d'accumulation).
- `mods/event/m11_01_00_00.emevd.dcx` : +4 instr dans l'evenement `11110100` (register `2004/29 (id,0)` + activation `2004/5 (id,1)` pour chacun de nos 2 ids), templates bytes clones des realences vanilla du garde de l'idole ; pur append, 3935 instr intactes.
- chr c5460 x4 + gameparam : inchanges (hash).
- Outil : `_work/tools/cs/EvdPatch.cs` (find | count | dump | append --event --clone argsHex~flag ; append = clone en boucle endogene sans ecriture vanilla ; dump = diff structurel). Build : `powershell -File tools/cs_build.ps1 EvdPatch`.

### 11.4 Revert (une commande)

    python tools/implantation_simon.py reverter

Backup courant **round-trip prouvé** : `c5460_20261126_155136/` (la sequence reverter
puis installer a ete executee reellement : revert = 2 fichiers restaures, msb
toujours 111e27411731 = l'etat d'avant session ; reinstall = memes hashes
770d72116256 / d1e246ad85e6, 4 chr+param `inchange`) ; precedent =
`c5460_20261126_154405/`. `nouveaux.txt` = (event, map), supprimes par reverter ;
`.avant` = etat precedent du MSB (111e27411731). `installer` repart du vanilla.

### 11.5 Protocole de test (session unique)
1. (etat deja installe, sinon) `python tools/implantation_simon.py reverter` puis `installer`.
2. Verifier le manifeste (msb/event = `installe`, chr/param = `inchange`).
3. Jeu (Sekiro via Steam) -> idole **Tour Lookout** (idole d'arrivee de la salle, interne 天守展望階 = « Upper Tower » côté UI) :
   - **4.6 m en +X/+Z depuis l'idole** : `PROBE_VANILLA` (samourai c1001) ?
   - **+4.8 m dans l'axe** (4.8 m plus loin) : `SIMON_LOOKOUT` (c5460) ?
4. Si echec de chargement : console ModEngine (`showDebugLog=1`, backup `modengine.ini.bak_showdebug`).
5. Croiser avec la matrice §11.2 — aucun test intermediaire demande.

### 11.6 Interdits respectes
Aucun record vanilla supprime/modifie (diff hors cibles = 0), aucun evenement vanilla ecrit (append seul, diff = +4 lignes), combat/patterns Genichiro intacts (pas de fichiers events Genichiro dans cibles), autres bosses/cartes intacts, anim/moveset Simon intacts (aucun fichier chr/anbnd modifie depuis l'etat c5460 stable).

## 12. RACINE DES ECHECS PRECEDENTS = ModEngine inactif sous Sekiro 1.6 (session debug approfondi)

**Resultat : ce n'etait ni le MSB ni l'EMEVD.** Les fichiers n'etaient jamais lus par le jeu
= nos 4 sessions d'echec (Temple, Dojo, EntityID, EMEVD, Tower Lookout) etaient toutes
invalidées en amont. Cause + correction prouvees par execution.

### 12.1 Environnement audité (verifié fichiers/exec)
- `sekiro.exe` 1.6.0.0, 68 005 144 o, machine x64, provenance **CODEX** (`steam_emu.ini` présent, `sekiro.cdx` = copie 68 005 144 o, steam_api64 = emu CODEX 366 808 o). Une seule installation (F:\Games…) ; lancé directement (pas d'options Steam).
- **DLL actives** : `dinput8.dll` (injection) + `dxgi.dll` (hooks graphiques) + dlls internes amd_ags/bink/fmod. **Identités reelles par VersionInfo/exports** :
  - `dxgi.dll` = **ReShade 5.4.2.1604** (crosire, md5 778213…, mtime 2022) — preuve : ReShade.log « loaded from dxgi.dll ». **Ce n'est PAS le Ultimate Mod Menu** ; le log `SekiroMod_Debug.log` (mtime 25/11 21:28) = ancien run où un traineur dxgi etait chargé, **absent des runs récents** (dxgi = ReShade dans tous les runs de contrôle) → aucun conflit dxgi/dinput8 aujourd'hui (chargeurs distincts : GetModuleFileName CreateFileW hook + DX11 VMT).
  - `dinput8.dll` = **ModEngine katalash 0.1.16 stock** (614 912 o, md5 F785817A…, export unique `DirectInput8Create`) — present & doublé du system32 (proxy local).
  - `modengine.ini` conforme (skipLogos=1, useModOverrideDirectory=1, modOverrideDirectory=`\mods`, cacheFilePaths=0, showDebugLog=1 ; backups `.bak_avant_test`/`.bak_showdebug`).
  - `modenginecrash.log` = dump de modules daté 25/11 (DINPUT8+dxgi charges a ce jour = preuve de lancement historique, pas un crash actuel ; fichier jamais re-ecrit).
- Structure `mods/` = bien miroir du jeu (chr/event/map/param + tiers Parts/Sound/mtd), DCX valides ; jeu = fichiers **loose** coexistant avec `Data*.bdt`.

### 12.2 Tests d'isolation (une variable à la fois, tous executés)
| # | Test | Resultat | Verdict |
|---|---|---|---|
| 1 | Snapshot modules du processus sekiro pendant run (aucun input) | `DINPUT8.dll` du jeu ET `dxgi.dll` du jeu charges ; SekiroMod absent | injection DLL OK |
| 2 | skipLogos 1→0 A/B ecran titre | images identiques (timing) | non concluant, abandonne |
| 3 | **Appat vanilla** : bundle `msg/engus/menu.msgbnd.dcx` patché (`PRESS ANY BUTTON`→`MODENGINE IS OK!`, tailles octets identiques), installe dans `mods/` | **toujours « PRESS ANY BUTTON »** | override mods/ NON applique |
| 4 | **Controle fichier jeu** : meme bundle ecrit DANS le jeu (backup verifié md5), appat retire, run | **toujours « PRESS ANY BUTTON »** | le jeu ne lit pas le loose = lit les BDT via hook d'archives |
| 5 | Retrait d'un seul param `dxgi.dll` (ReShade off) + meme appat | **« MODENGINE IS OK! » affiche a l'ecran-titre** (capture `testA_sans_dxgi.png`) | **CAUSE : la presence de dxgi.dll fait perdre au stock 0.1.16 la course d'installation de son hook fichier (Bug 1 connu)** — silencieux, aucun log, exactement le symptome « mods non chargés » |
| 6 | Source upstream clonee (`katalash/ModEngine`) | `CheckSekiroVersion()` n'accepte que 1.02/1.03 + refuse si `sekiro.cdx` existe + console `std::cin.ignore()` ; hook pose depuis `DllMain` via detour `SteamAPI_Init` = race | Bug 2 confirme aussi present pour 1.6, contourne/fait sauter |
| 7 | Repos du fix (piusryan, 0 fork 0 release) => **build maison** : sources complete, MSVC absent/non-admin → **zig 0.13.0 portable** (`zig cc/c++ -target x86_64-windows-gnu`), shim `concurrent_unordered_set.h` (PPL mise en veilleuse), 3 casts `reinterpret_cast<LPVOID>` ajoutes (extension MSVC), `extern "C"` sur `DirectInput8Create` (def .def = nom C brut) | `dinput8_patched.dll` 423 936 o, export `DirectInput8Create`, marqueurs fix presents (Hook attempt/modengine_load.log/INVENTORY/OVERRIDE OK/…), `Unsupported version` ABSENT | build OK |
| 8 | **Installation** : dinput8.dll stock → backup `.bak_stock_0.1.16` (614 912 o, md5 F785817A conserve) ; nouveau 423 936 o (md5 1F62FBE3BA32) ; dxgi/ReShade **conservé actif** | — | correction + rollback 1 commande |
| 9 | Run fix + **sans dxgi** + appat | capture `PREUVE_FINALE.png` = **« MODENGINE IS OK! »** + `modengine_load.log` : `Hook attempt 1/10`, `Detected game as Sekiro`, `Hooking archive loader functions`, `Hooking CreateFileW`, **INVENTORY liste tous nos fichiers** (mapstudio/m11_01… msb.dcx, event/… emevd.dcx, chr/c5460.*, param/…), `[ArchiveHook] Looking for override file …\mods\msg\engus\…` | **boucle mods/→hook→rendu PRUVEE de bout en bout** |
| 10 | Run fix + **avec dxgi** (cohabitation) | `modengine_load.log` : attempt 1/10, hooks archive+CreateFileW poses, **ArchiveHook intercepte des `data1:/…` reels** (param/drawparam/menu), inventory complet : **ModEngine marche avec ReShade charge** | cohabitation OK ; **regression connue** : boot ralenti (ReShade recompile ses effets ~14 restants encore a t=150 s vs <20 s avant-fix ⇒ cout du logger sur les rafales CreateFile de ReShade, a mitiger) |
| 11 | Nettoyage | appat `mods/msg/` supprime ; fichier jeu `menu.msgbnd.dcx` = md5 vanilla 2e0be99f2488 ; `_work/…/vanillatest/menu.msgbnd.ORIG.dcx` = backup durable | vanilla + overlay propres |

### 12.3 Corrections livrees (etat final)
- `F:\Games\Sekiro - Shadows Die Twice\dinput8.dll` = **fix worker-thread compile** (backup : `dinput8.dll.bak_stock_0.1.16`).
- `dxgi.dll` (ReShade) **conserves** — le trainer n'a pas ete sacrifie.
- Toujours installe : MSB (PROBE_VANILLA + SIMON_LOOKOUT, ids 1120625/626, positions §11.3), EMEVD +4 instr, archives c5460, gameparam.
- Source/build : `_work/modengine_fix/repo` (fork piusryan, patches locaux decrits §12.2 n°7) + toolchain `_work/toolchains/zig-windows-x86_64-0.13.0/`.

**REVERT (une commande, ordre inverse) :**
```
cp "/f/Games/Sekiro - Shadows Die Twice/dinput8.dll.bak_stock_0.1.16" "/f/Games/Sekiro - Shadows Die Twice/dinput8.dll"
python tools/implantation_simon.py reverter       # + retire l'event/msb si besoin
```
(`dxgi.dll` n'a jamais ete modifie durablement ; les restes temporaires du test appat ont ete nettoyes.)

### 12.4 A surveiller / limites connues
- Boot **ralenti** avec ReShade actif apres fix (compilation d'effets) : si genant pour un test rapide, renommer temporairement `dxgi.dll` (commande ci-dessous) = boot rapide, aucun gain perdu pour le test.
- `modengine_load.log` reecrit a chaque lancement (CREATE_ALWAYS) = **le diagnostic d'execution est maintenant l'artefact a lire** :
  `Hook attempt 1/10` + `INVENTORY … n file(s)` + `[ArchiveHook] Looking for override file …\mods\…` = preuve d'activation ; `OVERRIDE OK … served` = preuve de substitution effective.
- Aucune preuve encore in-game de nos records NPC (execution des instructions EMEVD, rendu c5460) = **test final §11.5** a faire desormais sur une base ou le mod est enfin charge.
