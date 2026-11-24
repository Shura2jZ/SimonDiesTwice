"""
Configure FModel pour Clair Obscur: Expedition 33 (phase 1 du portage de Simon).

Ce que le script fait, dans %APPDATA%\\FModel\\AppSettings.json :
  * sauvegarde le fichier existant dans _work/fmodel/AppSettings.json.bak
  * ajoute une entree PerDirectory pour le dossier Paks du jeu, avec :
      - UeVersion = GAME_UE5_4 (0x05040000), valeur verifiee dans EGame.cs de CUE4Parse
      - Endpoints[1] (Mapping) : Overwrite=true + FilePath = notre .usmap local
        -> c'est exactement ce que fait la case « Local Mapping File » de l'interface
      - Directories : 3 raccourcis vers les dossiers de Simon
  * selectionne ce dossier comme dossier courant (GameDirectory)
  * passe MeshExportFormat a Gltf2 (=1) ; la valeur d'origine (3) etait UEFormat,
    que Blender ne lit pas

Aucune cle AES n'est necessaire (les conteneurs du jeu ne sont pas chiffres).

Usage :
    python tools/fmodel_setup.py            # applique
    python tools/fmodel_setup.py --dry-run  # montre sans ecrire
"""

import json
import os
import shutil
import sys

APPDATA = os.environ.get("APPDATA", "")
SETTINGS = os.path.join(APPDATA, "FModel", "AppSettings.json")

GAME = r"E:\Games\Clair Obscur - Expedition 33"
PAKS = os.path.join(GAME, "Sandfall", "Content", "Paks")

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USMAP = os.path.join(PROJECT, "tools", "mappings", "ClairObscur_Mappings.usmap")
BACKUP_DIR = os.path.join(PROJECT, "_work", "fmodel")

GAME_UE5_4 = 0x05040000          # GameUtils.GameUe5Base (0x5000000) + (4 << 16)
SIMON = "Sandfall/Content/Characters/Enemies/HumanEnnemies/Simon/"

EMPTY_ENDPOINT = {"Url": "", "Path": None, "Overwrite": False, "FilePath": None, "IsValid": False}


def endpoints() -> list:
    aes = dict(EMPTY_ENDPOINT)
    mapping = dict(EMPTY_ENDPOINT)
    mapping["Overwrite"] = True          # « Local Mapping File » coche
    mapping["FilePath"] = USMAP          # « Mapping File Path »
    return [aes, mapping]


def directories() -> list:
    return [
        {"Header": "Simon (le boss)", "DirectoryPath": SIMON},
        {"Header": "Textures de Simon", "DirectoryPath": SIMON + "Textures/"},
        {"Header": "Cheveux de Simon", "DirectoryPath": "Sandfall/Content/Characters/Hair/NPCs/Simon/"},
    ]


def main() -> None:
    dry = "--dry-run" in sys.argv

    if not os.path.exists(SETTINGS):
        print(f"ERREUR : {SETTINGS} introuvable (FModel a-t-il deja ete lance ?)")
        sys.exit(1)
    if not os.path.exists(USMAP):
        print(f"ERREUR : fichier de mappings introuvable : {USMAP}")
        sys.exit(1)

    with open(SETTINGS, "r", encoding="utf-8-sig") as fh:
        s = json.load(fh)

    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup = os.path.join(BACKUP_DIR, "AppSettings.json.bak")
    if not dry:
        shutil.copy2(SETTINGS, backup)
        print(f"sauvegarde      : {backup}")

    before_format = s.get("MeshExportFormat")
    s["MeshExportFormat"] = 1                       # EMeshFormat.Gltf2
    print(f"MeshExportFormat: {before_format} -> 1 (glTF 2.0 binaire)")

    s["GameDirectory"] = PAKS
    print(f"GameDirectory   : {PAKS}")

    s.setdefault("PerDirectory", {})[PAKS] = {
        "GameName": "Clair Obscur: Expedition 33",
        "GameDirectory": PAKS,
        "IsManual": True,
        "UeVersion": GAME_UE5_4,
        "TexturePlatform": 0,                       # DesktopMobile
        "Versioning": {"CustomVersions": None, "Options": None, "MapStructTypes": None},
        "Endpoints": endpoints(),
        "Directories": directories(),
        "AesKeys": {"mainKey": "", "dynamicKeys": []},
        "LastAesReload": "2026-10-15T00:00:00+02:00",
        "CriwareDecryptionKey": 0,
        "UnluacOpCodeMap": "",
    }
    print(f"UeVersion       : {GAME_UE5_4} (GAME_UE5_4)")
    print(f"mappings locaux : {USMAP}")
    print(f"raccourcis      : {len(directories())} dossiers de Simon")
    print(f"jeux connus     : {len(s['PerDirectory'])} ({', '.join(s['PerDirectory'])})")

    if dry:
        print("\n--dry-run : rien ecrit.")
        return

    with open(SETTINGS, "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=2, ensure_ascii=False)

    with open(SETTINGS, "r", encoding="utf-8") as fh:
        check = json.load(fh)
    ok = check["PerDirectory"][PAKS]["UeVersion"] == GAME_UE5_4
    print(f"\necrit           : {SETTINGS} ({os.path.getsize(SETTINGS):,} octets)")
    print(f"relecture       : {'OK' if ok else 'ECHEC'}")


if __name__ == "__main__":
    main()
