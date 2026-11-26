# Simon Dies Twice

A work-in-progress mod project exploring a playable Simon boss from *Clair Obscur: Expedition 33* in *Sekiro: Shadows Die Twice*.

> **Status:** experimental. Character-model replacement (Simon replacing Isshin, `c5400`) is in progress: skin validated by the user, hair now visible (extracted from Clair Obscur via CUE4Parse), clothes bug fixed (33 mesh slots restored). Animation/moveset integration is the next phase.

## Project scope

The project investigates replacing Sekiro's Isshin character (`c5400`) with Simon, including a character model/skin, Simon's sword, and a retargeted attack animation. Work so far has focused on reverse-engineering Sekiro's model, animation, binder, compression, and TAE formats, then validating conversions outside the game before considering installation.

## Important caveats

- Nothing in this repository should be treated as a ready-to-install mod.
- Experimental assets and game files are kept outside this repository; no Sekiro files or third-party character assets are distributed here.
- Animation playback in an offline preview does **not** establish that Sekiro will trigger the move, apply suitable damage, or use correct hitboxes.
- The original Simon source assets and a local Sekiro installation are not included. Tools and notes may require paths and dependencies to be adapted for another machine.

## Development notes

See [docs/PROGRESS.md](docs/PROGRESS.md) for completed work, current findings, known limitations, and the next validation steps.

## Tooling (modding pipeline)

The `tools/` directory contains the reverse-engineering and conversion pipeline used for this project:

- `simon_export.py` — export GLB → intermediate binary (re-pose, bone mapping, texture assignment)
- `tools/tex_dds.py`, `tex_dds_alpha.py` — DDS BC1 encoder (with and without alpha)
- `tools/make_mod.py` — packaging into `c5400.chrbnd.dcx` + `c5409.texbnd.dcx` (DCX + BND4)
- `tools/cs/*.cs` — C# tools (FLVER injection, mesh manipulation, MTD/TPF patching, local FLVER renderer with textures)
- `tools/cs_build.ps1` — build script for the C# tools

The local research workspace (`_work/`) is not part of this repository. Only the tooling and documentation are published here.