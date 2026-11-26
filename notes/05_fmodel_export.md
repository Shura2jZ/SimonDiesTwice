# 05 - FModel : configuration et export de SK_Simon (palier 1A)

Objectif : sortir le mesh de Simon (`SK_Simon`) sous une forme que Blender peut lire,
sans que l'utilisateur ait a comprendre l'interface.

## 1. Etat des lieux (verifie le 16/10/2026)

| Element | Valeur constatee | Preuve |
|---|---|---|
| FModel | `F:\Desktop\Deep\FModel.exe` (50,5 Mo, x64 autonome) | listing du dossier |
| Config FModel | `C:\Users\marou\AppData\Roaming\FModel\AppSettings.json` | listing |
| Sorties FModel | `F:\Desktop\Deep\Output\{Exports,Logs,Backups}` | listing |
| Journal | `F:\Desktop\Deep\Output\Logs\FModel-Log-<date>.log` | contient le montage des paks |
| Blender | `E:\Softwares\blender.exe` (5.2.2, version fichier 5.2) | registre + version du binaire |
| Dossier de jeu | `E:\Games\Clair Obscur - Expedition 33\Sandfall\Content\Paks` | contient `pakchunk*.utoc/.ucas` |

Au premier lancement, FModel etait pointe sur **Fortnite** - d'ou la confusion.

## 2. Version du moteur : UE 5.4 (verifie)

Trois confirmations independantes :

1. `CUE4Parse/UE4/Versions/EGame.cs` : `GameUtils.GameUe5Base = 0x5000000`,
   `GAME_UE5_4 = GameUe5Base + (4 << 16)` = `0x05040000` = **84 148 224**.
   (Coherence : la config Fortnite livree contient `UeVersion = 100663296 = 0x06000000 = GAME_UE6_0`.)
2. Capture d'ecran officielle du mod Nexus "Mappings .usmap file for FModel"
   (`clairobscurexpedition33/mods/198`, image `notes/refs/nexus_198-1747236640-237908908.png`) :
   le champ *UE Versions* affiche `GAME_UE5_4`, et le fichier de mappings utilise s'appelle
   `ClairObscur5.4.usmap`.
3. Le mount point des archives est `../../../` et les chemins stockes commencent par
   `Sandfall/Content/...` (chaines en clair dans `pakchunk0-Windows.utoc`) - coherent avec
   les chemins du manifeste UE.

**Non verifiable** : l'executable `SandFall-Win64-Shipping.exe` ne contient plus les chaines
de version (`+UE5+Release-5.4`, `BuildSettingsVersion` : 0 occurrence, ASCII et UTF-16).
La detection automatique de FModel (`TryGetUeVersionFromExe`, qui lit `FileMajorPart`/`FileMinorPart`
de l'exe) echouerait donc ou tomberait sur une valeur fausse : la version doit etre forcee.

## 3. Ce que fait `tools/fmodel_setup.py`

Le script edite `%APPDATA%\FModel\AppSettings.json` (sauvegarde prealable dans
`_work/fmodel/AppSettings.json.bak`) :

| Champ | Valeur | Pourquoi |
|---|---|---|
| `MeshExportFormat` | `3 -> 1` | 3 = `EMeshFormat.UEFormat` (binaire maison, illisible par Blender) ; 1 = `Gltf2` (`CUE4Parse-Conversion/Options/EMeshFormat.cs`) |
| `GameDirectory` | dossier `Paks` | FModel monte ce dossier au demarrage |
| `PerDirectory[<Paks>]` | nouvelle entree | c'est la table des jeux connus de FModel |
| └ `UeVersion` | `84148224` | `GAME_UE5_4` (voir §2) |
| └ `IsManual` | `true` | necessaire pour que l'entree apparaisse dans le selecteur (`GameSelectorViewModel.cs:52`) |
| └ `TexturePlatform` | `0` | `DesktopMobile` (defaut du code) |
| └ `Endpoints[1]` | `Overwrite=true` + `FilePath=<notre .usmap>` | c'est **exactement** ce que fait la case « Local Mapping File » de l'interface (`UserSettings.IsEndpointValid` : `endpoint.Overwrite \|\| endpoint.IsValid`, et `InitMappings` charge le fichier local si `Overwrite`) |
| └ `Directories` | 3 raccourcis | menu *Favorite Directories* de FModel |
| `AesKeys.mainKey` | vide | conteneurs du jeu non chiffres (`ContainerFlags=0x09`) |

Verifications faites dans le code source (archive `_work/fmodel_src/FModel-dev/`) :

* `GameSelectorViewModel` (l.59) : au demarrage, FModel cherche `DetectedDirectories` par
  `GameDirectory` -> notre entree y est (l.52, car `IsManual`) -> elle est selectionnee
  et montee automatiquement.
* `ApplicationViewModel` (l.158-163) : `UserSettings.CurrentDir` recoit nos `Endpoints`.
* `GoToCommand.JumpTo` : les chemins de raccourcis sont decoupes sur `/`
  (`RemoveEmptyEntries`) ; un `/` initial est donc tolere, et `CustomDirectoriesViewModel`
  supprime un `/` final. Nos chemins (`Sandfall/Content/...`) correspondent aux cles de
  premier niveau de l'arbre.
* `CustomDirectory` se serialise en `{ Header, DirectoryPath }`.

Les 3 raccourcis (chemins verifies dans `Manifest_UFSFiles_Win64.txt`) :

```
Sandfall/Content/Characters/Enemies/HumanEnnemies/Simon/            <- SK_Simon, SM_Simon_Sword_UE5_2
Sandfall/Content/Characters/Enemies/HumanEnnemies/Simon/Textures/
Sandfall/Content/Characters/Hair/NPCs/Simon/                       <- cheveux
```

## 4. Procedure d'export (cote utilisateur)

1. Lancer `F:\Desktop\Deep\FModel.exe`. FModel doit s'ouvrir **directement sur
   « Clair Obscur: Expedition 33 »** (arbre d'assets a gauche, journal en bas).
2. Verifier dans le journal : `Mappings pulled from ... ClairObscur_Mappings.usmap`.
3. Menu **Favorite Directories -> Simon (le boss)**.
4. Clic droit sur `SK_Simon` -> **Export -> Model**.
5. Le fichier produit est un `.glb` (glTF 2.0 binaire) dans
   `F:\Desktop\Deep\Output\Exports\Sandfall\Content\Characters\Enemies\HumanEnnemies\Simon\`
   (option *Keep Directory Structure* active).
   `SK_Simon_Physics` (physics asset) et `SM_Simon_Sword_UE5_2` (epee) sont des assets
   separes : les exporter aussi si besoin plus tard.

## 5. Pieges connus

* **FModel ecrit `AppSettings.json` en quittant.** Toute modification du fichier doit etre
  faite FModel ferme, sinon elle est ecrasee. (Le script le verifie : `Get-Process FModel`.)
* `MeshExportFormat = 3` (valeur par defaut rencontree) produit un `.uemodel`, pas un glTF.
* Le `.glb` sorti est en pose de reference UE : axe Z vers le haut, metre/centimetre UE,
  squelette UE (`root`/`pelvis`...). La conversion vers le squelette Havok de Sekiro se fait
  au palier suivant (FLVER_Editor), pas ici.
* Ne pas modifier les archives du jeu : on ne touche qu'a `%APPDATA%\FModel`.
