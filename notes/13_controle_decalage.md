# 13 — Témoin minimal « tête d'Isshin décalée de 30 cm » (2026-10-18)

## Pourquoi ce test maintenant

Après deux jours, tous les builds donnent **le même symptôme, quel que soit le
contenu** (notes 10 et 12). Toutes les vérifications hors jeu disent que le
fichier est sain : conteneur BND4 byte-identique quand on ne change rien,
DCX en Oodle **Kraken** produit par **la DLL du jeu elle-même**
(`soulsutil.OODLE_DLL` pointe sur `F:\Games\...\oo2core_6_win64.dll`,
sha256 `988E8226…`), tables/facesets/index/sommets vérifiés un par un.

Il reste donc **une seule hypothèse qui explique tout** : ce n'est pas le
contenu qui casse, c'est **la chaîne d'écriture/chargement qui casse dès que le
FLVER s'écarte de la vanille**, même d'un octet.

Ce test le prouve ou l'élimine, sans ambiguïté possible.

## Le build

`_work/decaler.py 0.30` : on prend le **FLVER vanille tel quel** et on ajoute
**+0,30 m en Y** aux 8589 sommets du **maillage 4** (la tête d'Isshin), sans
toucher à un seul autre octet.

Mesures :

```
1er sommet avant : (-0.07692, 2.19697, -0.01203)   temps que la vanille
Y avant : min=1.9953  max=2.2398
Y apres : min=2.2953  max=2.5398                   (decalage +0.300)
taille identique : 7 966 688 = 7 966 688
regions differentes : 8589   (3 octets chacune, au +4 de chaque sommet)
```

Puis `python -u tools/make_mod.py _work\decalage.flver --sans-clm2 --install` :

- `GX : rien a corriger`, `0x40/0x44 : deja conforme`  → aucune correction ajoutee ;
- **BND4 reconstruit : 8 599 360 octets — exactement la taille de la vanille** ;
- `verification : BND4 relu identique=True | c5400.flver relu identique=True`.

Contrôle du conteneur reconstruit contre la vanille :

```
BND4 vanille 8599360 / BND4 temoin 8599360
regions differentes : 8589     octets differents : 25796
premiere : 0x214F84 (3 octets) au pas de 0x28  -> uniquement les Y du maillage 4
```

⇒ **Tout le reste est identique à l'octet** : en-tête BND4, table des entrées,
en-tête FLVER, matériaux, nœuds, facesets, tampons, agencements, GX, CLM2,
HKX, anibnd.

Fichiers : `_work/decalage.flver`, `_work/mod/chr/c5400.chrbnd.dcx`
(sha256 `9FFA77CC0B0C6C16…`, 3 151 164 o), installé sur
`mods\chr\c5400.chrbnd.dcx` (même sha256, vérifié).
Sauvegarde de l'état précédent : `_work/mod_backup/c5400.avant_decalage.dcx`.

## Comment lire le résultat (une seule modification, donc non ambigu)

| Observation | Conclusion |
|---|---|
| Isshin debout, **tête décollée au-dessus des épaules** (jour visible au cou), tout le reste normal | la chaîne écrit/charge correctement un FLVER modifié ⇒ **le problème vient de notre contenu** (sommets importés, liaison aux os, `.bin` de Simon). On reprend `notes/12` sur le contenu. |
| Encore **la masse brune** | la chaîne casse dès qu'un octet du FLVER change, **avec un conteneur de taille identique et des tables intactes** ⇒ il faut abandonner la piste du contenu et instruire l'écriture BND4/DCX (ou la façon dont le jeu relit un `mods\chr`). |
| Isshin normal, tête non décalée | le jeu n'a pas chargé notre fichier (override inopérant pour `chr`) ⇒ tester avec un fichier volontairement invalide. |

## Notes d'outillage

- `_work/decaler.py` : patch octet par octet, réutilisable pour décaler
  n'importe quel maillage (adresse = DataOffset + BufferOffset du tampon).
- Le décalage est fait sur la position seule ; normales, tangentes, UV,
  couleurs, indices d'os et poids restent **la vanille exacte** ⇒ ce build ne
  peut pas être mis en cause pour un défaut d'import.
