# M2 — Identification de la cible : Isshin, le Saint de l'Épée

Objectif : **prouver** quel identifiant de personnage Sekiro correspond au boss final
« Isshin, the Sword Saint » (剣聖 = *Kensei*), pour ne pas modifier le mauvais modèle.

Les archives vanilla sont extraites en clair dans `F:\Games\Sekiro - Shadows Die Twice\`.

---

## 1. Le roster des IA (source : Lua, FAIT)

Sekiro n'a **aucun fichier nommé d'après un boss**. L'IA est en Lua, organisée par
**id d'IA** (`think param`) :

- `script\aicommon.luabnd.dcx` → `goal_list.lua` / `logic_list.lua` (514 entrées `GOAL_*`)
- `script\mXX_XX_XX_XX.luabnd.dcx` → un fichier par id d'IA et par map
  (`540000_battle.lua`, `540000_logic.lua`, …)

Extrait du roster (62 types d'IA, `tools/` → cf. commande d'extraction) :

| nom d'IA | ids | lecture |
|---|---|---|
| **`Kensei`** | 540000, 540010, 540300, 540310, 543000 | 剣聖 = **« Saint de l'Épée »** |
| `Rival` | 710000, 710300 | Genichiro (le rival) |
| `Ouji` | 720000 | « le prince » = Kuro |
| `Iseinomusume` | 740000 | « la fille de la renaissance » = Enfant Divine |
| `Otyou` | 509000 | Lady Butterfly (まぼろしお蝶) |
| `Orochi` | 501000 | le Grand Serpent |
| `Nishikigoi` | 505000 | la Carpe |
| `RedOgre` | 502000 | l'Ogre enchaîné |
| `OnnaSousha` | 700000 | la nonne corrompue (femme) |

⇒ **le boss final est l'IA `Kensei` (540000 + variantes de phase).**

## 2. Où vit cette IA ? (FAIT)

Fichiers Lua présents par map :

| map | scripts `Kensei` présents |
|---|---|
| `m11_01` | 540000, 543000 |
| **`m11_02`** | **540000, 540010, 540300, 540310** |
| autres | aucun |

Et `m11_02` contient aussi `710000_battle.lua`, `711000_battle.lua` (Genichiro), `720000` (Kuro),
`740000` (Enfant Divine) ⇒ **`m11_02` est l'arène du combat final** (Genichiro puis Isshin).

## 3. Le casting de l'arène finale (source : MSB, FAIT)

Les MSB stockent les noms de « parts » en UTF-16LE, sous la forme `cXXXX_NNNN`.
Contenu de `m11_02_00_00.msb.dcx` (24 modèles) :

`c0000` (Wolf) · `c1000/c1001/c1010/c1011/c1020/c1021/c1100/c1120/c1150/c1180/c1190`
(ennemis/NPC courants) · `c1360` · `c1470` · `c1500` · **`c5400` ×2** · `c7010` ·
`c7100` (Genichiro) · `c7110` (Genichiro, voie de Tomoe) · `c7200` (Kuro) · `c7300` ·
`c7400/c7401/c7410` (Enfant Divine)

⇒ **`c5400` est le seul modèle de boss présent dans l'arène finale**, et il n'apparaît
**dans aucune autre map**.

## 4. La règle `id IA = chrId × 100` (validée)

| modèle | id IA | nom d'IA | où | cohérent ? |
|---|---|---|---|---|
| `c7100` | 710000 | `Rival` = Genichiro | m11_00, m11_01, **m11_02** | ✓ |
| `c7110` | 711000 | Genichiro (voie de Tomoe) | m11_01, **m11_02** | ✓ |
| `c7200` | 720000 | `Ouji` = Kuro | m11_00, m11_01, m11_02 | ✓ |
| `c7400` | 740000 | `Iseinomusume` | m11_00, m11_01, m11_02 | ✓ |
| `c1180` | 118000 | `Genan` | m11_00, m11_01, m11_02 | ✓ |
| `c1120` | 112000 | `MoujaKnight` | m11_00, m11_01, m11_02 | ✓ |
| `c1250` | 125000 | `YasyazaruKenzoku` (ennemi courant) | 14× en m11_01, 46× en m17, 25× en m20 | ✓ |
| **`c5400`** | **540000** | **`Kensei`** | **m11_02 seulement** | ✓ |

**Test de réfutation** : `c1250` apparaît jusqu'à **46 fois** dans une seule map
(des dizaines d'instances) ⇒ ce n'est pas un boss, c'est un ennemi de base.
**L'hypothèse initiale `c1250 = Isshin` est donc ÉCARTÉE.**

## 5. Preuve interne au modèle (source : FLVER, FAIT)

`c5400.flver` déclare lui-même son identité — ses chaînes (UTF-16LE) contiennent :

```
#20#c5400_body     #20#c5400_head     #20#c5400_hair     #20#c5400_kimono
N:\NTC\data\Material\mtd\character\c5408_hairface.mtd
N:\NTC\data\Material\mtd\character\c5409_body_SSS.mtd
N:\NTC\data\Material\mtd\character\c5409_head_SSS.mtd
N:\NTC\data\Material\mtd\character\c5409_helmet.mtd
N:\NTC\data\Material\mtd\character\c5409_kimono_Blend_AN.mtd
N:\NTC\data\Material\mtd\character\c5409_eyeshadow.mtd
N:\NTC\data\Material\mtd\character\c5409_hair_e_Decal.mtd
```

⇒ kimono + casque + cheveux + corps : un samouraï en kimono. **Confirmé : c'est bien `c5400`.**

## 6. Fichiers de la cible (FAIT)

| fichier | taille | rôle |
|---|---|---|
| `chr\c5400.chrbnd.dcx` | 3 708 400 | **mesh** (`c5400.flver` 7,97 Mo) + squelette (`c5400.hkx`) + cloth (`c5400_c.clm2`, `c5400_c.hkx` 552 Ko) |
| `chr\c5400.anibnd.dcx` | 7 254 512 | **animations** (4ᵉ plus gros `anibnd` sur 476 → moveset 3 phases) |
| `chr\c5400.behbnd.dcx` | 58 528 | **behavior / state machine** |
| `chr\c5408.texbnd.dcx` | 13 713 771 | **textures** (hairface) |
| `chr\c5409.texbnd.dcx` | 18 831 668 | **textures** (body, head, kimono, helmet, eyeshadow, hair) |
| `sound\c5400.fev/.fsb/.itl` | — | sons du personnage (`c5430.fev` partage `bank/c5400/*.wav`) |
| `action\` | — | noms d'états de behavior (`statenameid.txt`) |

⚠️ **Piège** : les textures **ne sont pas** dans `c5400.texbnd.dcx` (n'existe pas) mais dans
`c5408.texbnd.dcx` + `c5409.texbnd.dcx`, conformément aux chemins MTD lus dans le FLVER.

## 7. La « famille » Isshin dans les fichiers

| modèle | placé dans | hypothèse (NON vérifiée) |
|---|---|---|
| `c5400` | **m11_02** uniquement | **Isshin, le Saint de l'Épée** (boss final) ✓ identifié |
| `c5410` | m11_01 (×1) | Isshin version « Shura » (boss de la fin Shura) |
| `c5430` | m11_00 (×1), m11_01 (×3) | Isshin **PNJ** (le vieil homme assis au château) |
| `c5420`, `c5440` | nulle part (placement) | variantes non placées / inutilisées |

## 8. Ce qui reste INCERTAIN

- **Le MSB ne stocke pas l'id d'IA en int32** (recherche de 540000/710000 : 0 résultat).
  Le lien exact placement ↔ IA reste à établir (probablement via `NpcParam`).
- Quel modèle parmi `c5400_0000` / `c5400_0001` est le boss combattu et lequel est un
  doublon (corps/cinématique).
- La table de correspondance **texture ↔ matériau** dans le FLVER (les textures ne sont
  référencées par aucun chemin, seulement par index).
- Le rôle du préfixe `#20#` des noms de matériaux.
- Le contenu réel de `c5400.anibnd.dcx` (nombre de clips, structure).

## 9. Conclusion

> **La cible est `c5400`** (`chr\c5400.chrbnd.dcx`, `.anibnd.dcx`, `.behbnd.dcx`,
> textures `c5408` + `c5409`).
>
> Confirmation finale, à faire quand un premier modèle sera injecté :
> remplacer `c5400` et constater visuellement le changement sur le boss final.
