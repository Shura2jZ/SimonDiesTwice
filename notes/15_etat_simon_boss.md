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

- [ ] Lignes param 54600000 (NpcParam clone 54000000 hp/taupe/behaviorVariationId=54600 ; Think battleGoalID=546000 ; Behavior famille 254600000+k ; AtkParam 54600000+).
- [ ] Bundle `gameparam` recompilé → `mods/param/gameparam/…` (backup `.bak` existant).
- [ ] Install test : 4 archives + msb + bundle → `mods/` (tool `install_simon_boss.py`, backup dédié).
- [ ] **Test In-Game #1 : apparition du modèle c5460** (spawn) — puis crash-log / rendu.
- [ ] Greffe du clip Simon slot `a000_003080` + évènements AttackBehavior TAE (phase 3).
- [ ] Choix record/carte définitifs pour le spawn (testé : `c7300_0000`/`SIMON_SPAWN` sur m20_00_00_00).
- [ ] HKB attaques (states AttackXXX) et famille Behavior → attaque exécutable par IA (phase 3-4).
- [ ] Incertitudes résiduelles : sib modèles, texbnd model-keyed vs name-keyed [H], entityID dupliqué du clone MSB (option `--entity-id`), 41 EMEVD LoR non décodés (non bloquant).

## 6. Prochaine étape immédiate

ParamEdit posé → créer les lignes 54600000 → reemballeur bundle → `install_simon_boss.py` → **Test In-Game #1 apparition**.
