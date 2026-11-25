# 09 — La couleur de sommet : permutation d'un octet (cause du symptôme)

## Fait mesuré (la cause)

`SoulsFormats.FLVER.VertexColor` déclare ses champs dans l'ordre **`A, R, G, B`**
et expose deux constructeurs :

```
VertexColor(Single a, Single r, Single g, Single b)
VertexColor(Byte   a, Byte   r, Byte   g, Byte   b)
```

(données par réflexion, `_ProbeColor.exe`).

L'injecteur écrivait `new VertexColor(X, Y, Z, W)` en croyant l'ordre
`(r, g, b, a)`. Conséquence sur **tous** les sommets de nos 5 maillages :

| | R | G | B | A |
|---|---|---|---|---|
| GLB de Simon (voulu) | 100 | 100 | 100 | **255** |
| ce qui était écrit | 100 | 100 | **255** | **100** |

Rotation d'un octet, visible sans ambiguïté sur le maillage « Top » :
GLB `(132, 62, 149, 255)` → FLVER `(62, 149, 255, 132)`.

C'est-à-dire **alpha 0,39 au lieu de 1,0** (personnage à 40 % transparent,
donc invisible et rendu dans la passe transparente sans écriture de
profondeur : d'où « je me prends des textures dans la gueule », Sekiro masqué
quand Isshin est dans le champ) **et canaux R/G/B assombris à 0,39**
(« grandes géométries sombres »).

## Chaîne de preuve (qui est innocent)

1. `_work/glb_couleur.py` / `_work/glb_couleurs5.py` : le GLB de Simon porte
   `COLOR_0` = `VEC4` `unsigned byte` normalisé, **alpha toujours 255**
   (opaque) ; les trois canaux R/G/B sont égaux (gris 0,30–1,0).
2. `_work/inter_couleur.py` : `_work/simon_inter.bin` (SMPORT) contient bien
   `(0.3922, 0.3922, 0.3922, 1.0)` → **l'exportateur Python est innocent**.
3. `_work/tools/cs/_ProbeColor.exe` : l'ordre réel des champs et des
   paramètres du constructeur → **la faute est dans l'injecteur**.
4. Relecture par `FlverAttr.exe` : avant correction 3–11 couleurs distinctes
   par maillage (alpha 0,24–1,0) ; après correction **1 seule**,
   `(255,0,0,255)`, identique aux 33 maillages de la vanille.

## Correction

`_work/tools/cs/FlverInject.cs` : les arguments du constructeur suivent
maintenant l'ordre `(a, r, g, b)` du type :

* défaut : `new FLVER.VertexColor((byte)255, (byte)255, (byte)0, (byte)0)`,
  soit les champs `A=255, R=255, G=0, B=0` — et la vanille se relit
  précisément `(R,G,B,A) = (255,0,0,255)` ;
* `--attributs-glb` : `(W, X, Y, Z)` du GLB, dans le même ordre corrigé.

## Leçon

Les types de SoulsFormats ne suivent pas l'ordre habituel RGBA
(`VertexColor` = `(a, r, g, b)`). **Tout appel à un constructeur de
SoulsFormats doit être vérifié par réflexion** (`FlverMembres.exe`,
`_ProbeColor.exe`) avant d'être cru — un seul appel mal ordonné a produit un
symptôme constant, à l'épreuve de tous les autres correctifs.
