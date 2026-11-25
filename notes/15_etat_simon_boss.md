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
