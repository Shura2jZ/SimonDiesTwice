# Development status

Last updated: 2026-11-26

## Current state

Experimental research/modding project. Two parallel workstreams are active:

1. **Boss candidate work** (model, animation, packaging) — offline-validated candidates in a local research workspace; not yet a playable boss.
2. **In-game integration of "Simon" as a standalone NPC** (`c5460` slot) in `m11_01_00_00`, now unblocked after a root-cause fix to the mod loader itself (see below).

No Sekiro files, Simon source assets, or installable packages are published in this repository. This repository carries documentation, full research notes, and evidence screenshots of loader behaviour.

## Milestone 2026-11-26 — mod loader root cause found, corrected, proven

**Symptom:** five successive in-game test cycles showed nothing (Temple spawn, Dojo probe + Simon, EntityID fixes, EMEVD event references, Tower Lookout test) although every file-level check passed statically.

**Root cause (proven by controlled execution, one variable per test):**

- The installed `dinput8.dll` is stock **ModEngine 0.1.16**, which on **Sekiro 1.6.0.0** fails twice: its hook is only installed from a `DllMain`-era detour of `SteamAPI_Init` (load-order race, commonly lost when overlays are present), and its version gate only accepts 1.02/1.03 builds (our exe: 68,005,144 bytes, `sekiro.cdx` present).
- With `dxgi.dll` (**ReShade 5.4.2** in this install — identified by VersionInfo and its own log) present, the loader lost the race **silently**: the game ran normally, no error appeared, and **nothing under `mods/` was ever served**. Every MSB/EMEVD/param edit was therefore inert.

**Decisive isolation tests (executed, captured):**

| Test | Result |
| --- | --- |
| Binary A/B trap: vanilla `msg/engus/menu.msgbnd.dcx` patched (`PRESS ANY BUTTON` → `MODENGINE IS OK!`, byte-identical length) placed in `mods/` | Unchanged in game → override not served |
| Same patched bundle written into the game folder itself (with backup) | Still unchanged → the game reads `Data*.bdt` archives, so only the loader's archive/file hook can substitute files |
| Single-variable test: `dxgi.dll` renamed away, trap back in `mods/` | **Title screen rendered `MODENGINE IS OK!`** → loader works; overlay presence was the failing variable |
| Fix built from sources (`piusryan` 1.6 fix tree; no MSVC/admin available → built with portable zig targeting `x86_64-windows-gnu`, PPL shim + 3 MSVC-extension casts + `extern "C"` on the export), installed with backup | `modengine_load.log` now proves every launch: `Hook attempt 1/10`, `Detected game as Sekiro`, hooks on archive loader **and** `CreateFileW`, full `INVENTORY` listing `mods\map\…msb.dcx`, `mods\event\…emevd.dcx`, `chr\c5460.*`, plus `[ArchiveHook] ... mods\…` override lookups. Screenshot evidence of the trap rendered in game. |

**Installed state (on top of documented backups):**

- `dinput8.dll` = locally built fix (423,936 bytes); original stock file preserved as `dinput8.dll.bak_stock_0.1.16` (614,912 bytes) — reverting the loader is one file copy.
- `dxgi.dll` (ReShade) and trainer situation untouched; coexistence confirmed (both DLLs loaded, hooks active in one run). Known caveat: boot is slower while ReShade recompiles effects; renaming `dxgi.dll` temporarily restores fast boots for a quick test.
- Game folder checked untouched (talk/menu bundle back to vanilla md5, map/event/param base files unchanged from their pre-test hashes).

## In-game integration under test (pending one user session)

- Map `m11_01_00_00`, zone "Tower Lookout" (idol `天守展望階`, in-game UI "Upper Tower"), two new vanilla-unique records, no vanilla record touched:
  - `PROBE_VANILLA` — clone of `c1001_0009` (visible samurai), npc/think `10010000`, EntityID `1120625`, position `(-119.5, 54.15, 237.5)` (4.6 m from idol).
  - `SIMON_LOOKOUT` — `c5460`, npc/think `54600000`, EntityID `1120626`, position `(-116.0, 54.15, 240.8)` (9.2 m from idol, 4.8 m beyond the probe).
- Map event file patched with **+4 instructions only** (entity register/enable pair cloned byte-for-byte from vanilla idol-guard instructions, `bank 2004 id 29` then `id 5`, matching the recipe read in Land of Reeds). Logical diff: 3,939 lines identical, +4 added.
- Archives `c5460` (chrbnd/behbnd/anibnd/texbnd) and `gameparam.parambnd.dcx` unchanged from the validated state.

**Verified in files:** records, EntityIDs (unique, no `-1`), positions with clearance computed from MSB dumps, event patch identity, installed-file hashes, loader execution logs.
**Still to confirm in game (single session):** event instructions executing, both NPCs instancing and rendering — nothing else remains.

## Rollback

```
cp dinput8.dll.bak_stock_0.1.16 dinput8.dll        # loader back to stock
python tools/implantation_simon.py reverter         # removes/restores mod overlay files
```

## Prior documented findings (unchanged)

- Simon model/memory pipeline on the `c5460` slot: `c5400` as build host, renamed archives, FLVER/skin/sword candidates, hair work **paused**.
- `Skill 1` clip (231 frames → 199 Isshin tracks, ~7.63 s at ~30.13 fps) packaged offline in `_work`; TAE/Behavior column of the clip still unresolved (existing `InvokeAttackBehavior` events point at Isshin's Iai IDs — not an approved mapping).
- Land of Reeds audit: custom-enemy integration recipe recorded in `notes/14_lor_boss_methode.md` (records + EMEVD activation + overlay archive layout) — now validated against our own hooked runs.
- Isshin trajectory/bow analysis (clips 3003/3008/3011/3030/3050/3090) paused pending the NPC visibility milestone.

## Single next manual step

Start Sekiro → travel to the Tower Lookout idol → check (a) samurai probe ~4.6 m in, (b) `SIMON_LOOKOUT` ~4.8 m further. If absent, read `modengine_load.log` (`Hook attempt`, `INVENTORY`, `[ArchiveHook] …\mods\…`) — it now distinguishes "file not served" from "file served but record not instanced".

---

## Archived — full detailed status of 2026-11-24 (Simon-on-Isshin workstream)

Kept verbatim: detailed model/texture/hair/TAE findings summarized above.

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