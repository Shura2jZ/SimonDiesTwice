# Development status

Last updated: 2026-11-24

## Current state

This is an experimental research/modding project, not a playable release. The work targets Isshin (`c5400`) as the replacement character. Model and animation candidates exist in a separate local research workspace; they have not been published in this repository or validated as a complete in-game boss.

## Phase 1 — Character model replacement (Simon replacing Isshin)

### Completed / demonstrated

**Model re-pose and skin**
- Parsed Sekiro FLVER character geometry and skeleton data, mapped Simon's skeleton to Isshin's, and generated character-model/skin candidates.
- Verified the local FLVER transform calculation against 284 bones (maximum reported error approximately `2.1e-7`).
- Skin candidate validated by the user ("c'est bon pour les habits" / "le visage est droit et le manteau est collé").

**Textures**
- Route "replace by name" validated: `c5409_kimono_a/n` (coat), `c5409_hoture_a/n` (top), `c5409_helfur_a/n` (bottom), `c5409_head_a/n`, `c5409_head_1m` (SSS mask, replaced by white/grey), `c5409_body_a/n`. BC1 (DXT1) 1024×1024 with full mip chain, header DDS DX10.
- SSS vanilla conserved (stone + gold) — `g_SSSStrength`/`g_DiffuseMapColor` modified then restored.
- No `allmaterialbnd` override (avoided white-clothes regression).

**Clothes fix (user-added)**
- The FLVER vanilla of Isshin has **33 mesh slots**, the mod had only **5**. The TAE draw masks reference 33 slots → the engine read out of bounds and drew garbage geometry ("morceaux d'habits qui partent en couille" at the arms).
- Fix: rebuild the FLVER with **33 mesh slots** (5 filled with Simon's geometry, 28 emptied). CLM2 rewritten with 33 empty elements.
- Validated: no more garbage geometry, clothes intact.

**Hair**
- Simon's hair was NOT in `SK_Simon.glb` — it's a separate UE5 asset: `Simon_Hair_Custo_skl.uasset` (82 816 vertices LOD4, 149-bone strand rig).
- Extracted from Clair Obscur via CUE4Parse (UE 5.4, IoStore pakchunk100). Required installing .NET SDK 10.0.403 (only runtime 10 was available).
- The CUE4Parse sub-agent found that the game attaches the hair to the `head` bone (not a socket), with a relative offset of `+209.06 cm` on the Z axis. The UE→glTF conversion was corrected (Z-up → Y-up) and the placement goes through the `head` bone as a common reference frame.
- Hair mesh injected into slot 5 (Isshin's beard slot, `c5409_hair_e_Decal` MTD → Fur_NTC shader). Texture `c5409_helmet_a` replaced by Simon's hair atlas (`T_Hair_Simon_Color` + alpha, BC1 with 1-bit alpha, mode 3 colours — like Sekiro's hair masks). No `allmaterialbnd` override.
- Normals fixed: UE hair cards have tangential normals → black render. Replaced with mixed normals (vertical + radial).
- Scale ×1.25 applied (mesh + bind poses + rig), configurable via `--echelle`.
- Local textured renderer (`FlverRendu.exe` + `FlverRenduTex.exe`) used to verify geometry and placement without launching the game.

## Attack / TAE findings — unresolved

- The replaced animation is `a000_003080.hkx`, but its existing six `InvokeAttackBehavior` events at about 1.50, 2.50, 2.70, 2.90, 3.10, and 3.77 seconds invoke behavior judge IDs `411`, `416`, `417`, `418`, `419`, and `412`.
- In Isshin's behavior table, these resolve to attacks `54000411`, `54000416`, and `54000412` — Isshin's invisible-Iai continuous/delayed slashes. Not justified as Simon's normal sword hitboxes.
- Ordinary Isshin sword moves use other behavior IDs (basic combo IDs around `10–14`), but no such behavior/timing mapping has yet been validated against Simon's animation.
- No TAE/attack-parameter package has been created or installed. The candidate animation binder is not an attack-ready mod.

## Remaining work

1. Fine-tune hair placement (parameters `dx, dy, dz` of `FlverHairInject`) and colour.
2. Adjust scale (parameter `--echelle`) if needed.
3. Remove the remaining "floating piece of fabric" (24 vertices collapsed, minor residue).
4. Determine the intended gameplay role and timing of Simon's `Skill 1` clip.
5. Match its active strike frames and sword trajectory to Sekiro behavior IDs and hitbox dummy-bone pairs; verify damage, posture damage, effects, recovery.
6. Build and inspect any TAE/parameter candidate offline, preserving originals.
7. Finish sword grip, attachment, materials.
8. Only after offline checks, install test candidates with backups and verify appearance, move triggering, collision/hitboxes, damage, recovery in game.
9. Reassess character scale, transitions, and whole boss AI/moveset before calling the project playable or release-ready.

## Safety and scope

- Treat files under `_work/` as experiments, not release assets.
- Do not overwrite game files without a backup and explicit, successful validation.
- This repository contains documentation + tooling. It does **not** contain Sekiro game data, Simon source meshes/textures/animations, or an installable mod package.<|end|>