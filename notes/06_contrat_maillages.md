# 06 — Le contrat « un maillage = un bit » (masques de dessin)

## Fait vérifié (mesure)

`c5400.tae` (extrait de `c5400.anibnd.dcx`, 1 070 896 octets) contient **35 événements**
dont le motif d'octets est :

```
FF FF FF FF 01  00 01 00  83 00 00 00 00 00 00 00  <pointeur 8 octets>
 |__ masque __|  | pad |  |____ type d'événement ____|
```

Mesuré avec `tools/tae_masques.py` (recherche de la signature
`00 01 00 83 00 00 00 00 00 00 00`, puis relevé de la fréquence des 5 octets
qui précèdent).

* les 35 événements portent le **même** masque `FF FF FF FF 01` ;
* taille du masque : **5 octets = 33 bits** ;
* le modèle vanille d'Isshin a **exactement 33 maillages** ;
* le fichier de tissu `c5400_c.clm2` a **exactement 33 éléments**, un par
  maillage, et ne porte des entrées que sur les maillages 21 à 24 (les
  matériaux `*_Cloth` : `c5409_kimono_Blend_AN_Cloth`, `kimono_Cloth_Decal`,
  `hoture`, `hair_cloth`, `helmfur_cloth`).

Conclusion de la mesure : **les animations distinguent les maillages par leur
index, dans un tableau indexé par le numéro de maillage**, et ce tableau a la
taille du nombre de maillages du modèle (33 ici).

## Hypothèse (cause du palier 1A cassé)

Un modèle à 5 maillages, recevant des masques à 33 bits, fait lire/écrire le
moteur hors de son tableau de maillages → géométrie aléatoire à l'écran
(« polygones géants / traits blancs »). C'est cohérent avec tout le reste :

* le FLVER se relit correctement et se **rend** correctement hors jeu
  (`MySFformat.Cli.exe` ne joue aucun masque) ;
* le skinning est vérifié bon (test de pose ciblée sur `Head`) ;
* le correctif « CLM2 à 5 éléments vides » n'a rien changé : le CLM2 n'était
  pas la source du dépassement, les masques le sont.

## Statut

* Mesure ci-dessus : **vérifiée**.
* Interprétation « dépassement de tableau » : **hypothèse**, en cours de test
  en jeu (`--remplacer` : garder les 33 emplacements de maillages d'Isshin).
* Reste inconnu : si le moteur borne ou non ses lectures de masque, et si
  d'autres tableaux hors FLVER (hors CLM2) sont indexés par maillage.
