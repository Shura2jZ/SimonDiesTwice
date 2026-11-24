# Development status

Last updated: 2026-11-24

## Current state

This is an experimental research/modding project, not a playable release. The work targets Isshin (`c5400`) as the replacement character. Model and animation candidates exist in a separate local research workspace; they have not been published in this repository or validated as a complete in-game boss.

## Completed / demonstrated outside the game

- Parsed Sekiro FLVER character geometry and skeleton data, mapped Simon's skeleton to Isshin's, and generated character-model/skin candidates. The user considers the current skin candidate validated for this phase; hair work is explicitly paused.
- Verified the local FLVER transform calculation against 284 bones (maximum reported error approximately `2.1e-7`).
- Exported Simon's large sword as a local geometry candidate and checked its scale and attachment positions in offline previews. Final grip, materials, and in-game appearance are not confirmed.
- Decoded Simon's `Skill 1` animation and retargeted a 231-frame clip to 199 Isshin tracks. The clip is about 7.63 seconds at approximately 30.13 frames per second; HKX encoding and offline replay have been checked.
- Built a **local-only** `c5400.anibnd.dcx` candidate in `_work/` that replaces `a000_003080.hkx` while retaining the original TAE and other binder entries. The archive comparison verified that this is the only changed entry. This verifies packaging, not in-game attack behavior.
- Read Isshin's TAE (`ID 205400`, event bank 14) and correlated attack behavior IDs with Sekiro's `BehaviorParam` and `AtkParam_Npc` tables.
- Confirmed the installed game character archives were left untouched during the recent offline packaging/research work; prior game installations have backups in the local workspace.

## Attack / TAE findings — unresolved

- The replaced animation is `a000_003080.hkx`, but its existing six `InvokeAttackBehavior` events at about 1.50, 2.50, 2.70, 2.90, 3.10, and 3.77 seconds invoke behavior judge IDs `411`, `416`, `417`, `418`, `419`, and `412`.
- In Isshin's behavior table, these resolve to attacks `54000411`, `54000416`, and `54000412`. The Paramdex names identify them as Isshin's invisible-Iai continuous/delayed slashes. For example, `54000411` has fire damage and a special effect, while `54000416` is a delayed-slash entry with zero physical attack in the inspected row. These are not justified as Simon's normal sword hitboxes or damage.
- Ordinary Isshin sword moves use other behavior IDs (for example, basic combo IDs around `10–14`), but no such behavior/timing mapping has yet been validated against Simon's animation. Simply retaining the original TAE events is therefore not an approved attack integration.
- No TAE/attack-parameter package has been created or installed. The candidate animation binder is not an attack-ready mod.

## Remaining work

1. Determine the intended gameplay role and timing of Simon's `Skill 1` clip (single special move versus part of a larger moveset).
2. Match its active strike frames and sword trajectory to Sekiro behavior IDs and hitbox dummy-bone pairs; account for Simon's longer blade. Verify damage, posture damage, effects, and recovery behavior rather than copying Isshin's Iai events.
3. Build and inspect any TAE/parameter candidate offline, preserving the original files and documenting every changed entry.
4. Finish the sword grip, attachment, and materials. Hairline/front-hair geometry remains paused; do not describe it as fixed.
5. Only after offline checks, install test candidates with backups and verify appearance, move triggering, collision/hitboxes, damage, and recovery in game.
6. Reassess whether character scale, transitions, and the whole boss AI/moveset are adequate before calling the project playable or release-ready.

## Safety and scope

- Treat files under `_work/` as experiments, not release assets.
- Do not overwrite game files without a backup and explicit, successful validation of the candidate.
- This repository contains documentation only at present. It does not contain Sekiro game data, Simon source meshes/textures/animations, or an installable mod package.
