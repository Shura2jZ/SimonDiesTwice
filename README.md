# Simon Dies Twice

A work-in-progress mod project exploring a playable Simon boss from *Clair Obscur: Expedition 33* in *Sekiro: Shadows Die Twice*.

> **Status:** experimental and not yet a playable or release-ready boss. The character-model replacement and a retargeted animation have been prepared as local test candidates. Attack behavior, hitboxes, weapon presentation, and in-game integration remain unverified. See [Development status](docs/PROGRESS.md).

## Project scope

The project investigates replacing Sekiro's Isshin character (`c5400`) with Simon, including a character model/skin, Simon's sword, and a retargeted attack animation. Work so far has focused on reverse-engineering Sekiro's model, animation, binder, compression, and TAE formats, then validating conversions outside the game before considering installation.

## Important caveats

- Nothing in this repository should be treated as a ready-to-install mod.
- Experimental assets and game files are kept outside this repository; no Sekiro files or third-party character assets are distributed here.
- Animation playback in an offline preview does **not** establish that Sekiro will trigger the move, apply suitable damage, or use correct hitboxes.
- The original Simon source assets and a local Sekiro installation are not included. Tools and notes may require paths and dependencies to be adapted for another machine.

## Development notes

See [docs/PROGRESS.md](docs/PROGRESS.md) for completed work, current findings, known limitations, and the next validation steps. The local research workspace is not this Git repository; only the project overview and progress documentation are published here.
