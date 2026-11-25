# 14 — LAND OF REEDS (芦苇之国) : analyse d'un boss indépendant, transfert vers Simon

Période d'analyse : version **5.7.1** du mod (NexusMods 1333, `芦苇之国5.7.1 魂五特别版.rar`,
MD5 `9467718901cbe4e1b7e05be306965f67`, 2 390 690 779 o, extraite `E:/lor_x`, **aucune écriture
dans le jeu ni dans `mods/`**).

Légende des preuves :
- **[FICHIER]** = constaté directement dans les fichiers (reproductible).
- **[PUBLICATION]** = lu dans une publication (changelog, Bilibili, Nexus).
- **[DÉDUIT]** = inférence depuis des faits mesurés, hypothèse argumentée.
- **[INCONNU]** = élément non déterminé faute de preuve.

## 1. Cartographie d'archives

**[FICHIER]** Racines de l'archive (1190 fichiers, 2359 Mo) : `chr/` (155 f., 1092 Mo),
`map/` (800 f., dont 11 MSB `mapstudio/*.msb.dcx`), `param/gameparam/gameparam.parambnd.dcx`,
`event/` (41 `*.emevd`), `action/script/` (42 `.hks`), `msg/zhocn/{item,menu}.msgbnd.dcx`,
`cutscene/`, `mtd/`, `sfx/`, `sound/`…

Par personnage, le moteur a besoin de 4 archives : `cXXXX.anibnd.dcx` (HKX d'anim + `cXXXX.tae`
+ `skeleton.hkx` + `cXXXX.compendium` + `load_c0000_cXXXX.txt`), `cXXXX.behbnd.dcx`
(`cXXXX.hkx` graphe HKB + `c9997.hkx` arbre d'IA partagé), `cXXXX.chrbnd.dcx`
(`cXXXX.flver` + `cXXXX.hkx` squelette + `.clm2`), `cXXXX.texbnd.dcx`.

**[FICHIER]** Pools partagés : `c0000.a000`, `c0000_a000_hi/lo`, `c0000_a07x`, `c0000_a2xx`
(animations communes — un TAE renvoie souvent vers des clips hébergés là, ex. `a000_000401.hkx`
retrouvé dans le `c0000_a000_lo` vanilla) + 6 archives croisées `c0000_cXXXX.anibnd.dcx`.

**[FICHIER]** 31 IDs de personnages **absents du vanilla** :
c1480, c2120, c2190‑c2194, c2200, c2300, c2620, c2640, c2710, c3010, c3100, c3170,
c4000‑c4002, c4100, c4290, c4520, c4530, c5110, c5280, c6120, c6121, c6200, c6201,
c7320, c8040, c8050, c9010, c9020 (32e : c9000 remplacé). `.behbnd` livrés pour 35 IDs.

## 2. Identification des 4 cibles (Malenia, Lady Maria, Gael, Artorias)

**[FICHIER] Méthode d'identification** : les records de la paramétrique MSB
(`map/mapstudio/*.msb.dcx`) portent des **noms lisibles** (`record=女武神 modele=c2120`) —
les noms de records sont le plus sûr lien ID↔personnage. Recoupement par rendu FLVER
(`rendu/c4530_av.png`, `c4100_av.png`, etc.) et par signatures d'os/matériaux.

| ID | Nom (record MSB) | Signatures sur modèle | HP (NpcParam) | TAE : anims / AttackBehavior / judges | Hôte HKB |
|---|---|---|---|---|---|
| **c2120** | 女武神 « Valkyrie » = **Malenia** | matière `#21#_Malenia_all` ; os `R_BladeGimmick_1..3` (bras de prothèse) ; os `Xtra_Petal_001..032` (pétales d'Éclosion) ; `Butterfly_*`, clones `c2120_Clone_*` | 1800 / 1600 / 1650 / 9999 | 185 / 100 / 90 | c5060 |
| **c4530** | BOSS玛利亚 = **Lady Maria** | rendu : long manteau + cape rouge + rapier | 3000 / 1350 | 347 / 107 / 90 | **c5400 (Isshin)** |
| **c2200** | `Gale` + `幻影盖尔` = **Gael** (P1/phantome) | — | 700 / 9999 | 283 / 20 / 18 | c1470 |
| **c6201** | 盖尔01 / 再战盖尔**一阶段** = Gael P1 (rematch) | — | 1700 | 185 / 36 / 33 | c5060 |
| **c6200** | 盖尔 / 再战盖尔**二阶段** = Gael P2 (rematch) | — | 1595 / 1700 | 185 / 58 / 47 | c5060 |
| **c4100** | 亚尔特留斯 = **Artorias** | rendu : heaume à plume, cape en lambeaux | 850 / 1800 | 185 / 48 / 41 | c5060 |

**Correction d'attribution** : c2710 = 神父 « Père » (records `神父`, matière `hat/necklace/mantle`,
coquille probable de Gehrman/Bloodborne) — **ce n'est pas Lady Maria**, contrairement à une
première lecture visuelle. Maria = c4530 [FICHIER].

Autres identités révélées par les records MSB (liste étendue, `[FICHIER]` sur le nom de record) :
`c8050` 格曼(Gehrman), `c8040` 轮椅格曼(chaise roulante), `c3100` 灵珠猎人,
`c3170` 吸魂鬼, `c4290` 猎犬骑士(Bloodhound Knight), `c4520` 希夫(Sif),
`c5110` 无名王者, `c5280` 薪王, `c6120/6121` 少爷/大小姐, `c2190` 索拉尔(Solaire),
`c2191‑2194` « thief » / **魂五化身** (P1‑4, arsenaïque DS3 intégral),
`c7320` 米娘(Miquella, liens BGM), `c4000/01/02` 猎人 刀/鞭/锤 (chasseur Bloodborne,
matériaux 锯肉刀 + 火铳), `c9010` 2B, `c9020` 神秘剑客, `c9000` 修罗/心狼, etc.

**[PUBLICATION]** Chronologie (`更新日志25-5-1.txt`) : 8/17 « 盖尔 » ; 8/24 « 一阶段 » ;
9/4 « 女武神 巴 » ; 9/24 « 绘画世界支线 » (carte d'Artorias) ; 9/26 « 亚尔特留斯bgm修复 » ;
11/22 猎犬骑士 ; 11/29 « 新增四个boss **再战** » (d'où les records 再战* de 2023‑11‑24/25
dans les MSB) ; 12/15 « 猎人支线…老猎人的遗骨 » ; 2024/1/6 Artorias en élite.
**[FICHIER]** Dates de fichiers : c2120 textures 2023‑08‑22/24, TAE/anibnd c4100 09/11‑09/20,
c4530 tex 2023‑12‑06, « 再战 » MSB 2023‑11‑24/25. Tensions de dates → [DÉDUIT] contenus
préparés avant annonce.

## 3. Chaîne animation → TAE → paramètres → HKB → IA (reconstructée)

### 3.1 Événement d'attaque TAE bit à bit
**[FICHIER]** `AttackBehavior` (template SDT de DSAnimStudio, `TAE.Template.SDT.xml`) :
`s32 AttackType | s32 (réservé) | s32 BehaviorJudgeID | u8 DirectionType | u8 Source | s16 StateInfo`
(+8 octets selon variante, événements 16 ou 24 B).
Décodeur appliqué (`_work/lor/attacks_tae.json`) : ex. `c4100` ANIM 3000, `0.8667‑1.0000 s`,
`judge=300`.

### 3.2 Liaison complète, vérifiée sur les 6 cibles
```
map MSB record ──NPCParamID──▶ NpcParam {hp, stamina, behaviorVariationId, nameId}
             ──ThinkParamID─▶ NpcThinkParam {logicId, battleGoalID, BattleStartDist …}

animation a000XXXXXX.hkx (anibnd) ◀─ ANIM id ─ cXXXX.tae
        événement AttackBehavior(BehaviorJudgeID) ──▶ BehaviorParam
        (lignes de famille variationId = behaviorVariationId ; sélection par judge)
                          ──refType/refId──▶ AtkParam_Npc (phys 70..120, poise, portées…)
                                        ── condition de juge/expulsion, fenêtre temporelle

NpcThinkParam.battleGoalID ──▶ états du graphe HKB
cXXXX.hkx  = copie du graphe d'un boss vanilla + patch de l'ID « c5400 »→« c4530 » (6 octets, 2 occurrences)
c9997.hkx  = copie littérale de l'arbre IA du boss hôte (MD5 identique)
états nommés Attack<ID> dans c9997  ⇄  animation <ID> dans le TAE du récepteur [DÉDUIT]
```

**[FICHIER] Provenance HKB mesurée (MD5 + `cmp -l`)** :

| LoR | `cXXXX.hkx` vs hôte | octets changés | `c9997.hkx` = BD du hôte |
|---|---|---|---|
| c4100 | c5060.hkx | 6 (« c5060 »→« c4100 » ×2) | `23ad65f6…` = c5060 ✓ |
| c2120 / c6200 / c6201 | c5060.hkx | 6–8 | idem ✓ |
| c4530 (Maria) | c5400.hkx (Isshin) | 6 | `05f772f3…` = **c5400 ✓ octet à octet** |
| c2200 (Gael) | c1470.hkx | 6 | `d6bc7d9b…` = c1470 ✓ |

**[FICHIER]** Entête TAE des clones : `id=205060` pour c4100/c2120/c6200/c6201,
`id=205400` pour c4530, `id=201470` pour c2200 → `200000 + ID du boss hôte` : les TAE sont
**clonés depuis le hôte puis réécrits** (MD5 tous distincts, inventaire d'anim identique au hôte
— 185 entrées pour les clones 5060).

**[FICHIER] Couverture judge→BehaviorParam** (famille `variationId=NpcParam.behaviorVariationId`) :
c2120 *rematch* 86/90 ; c4530 *rematch* 89/90 ; c2200幻影 18/18 ; c2200 14/18 ;
c6200 42/47 ; c6201 24/33 ; c4100 32/41 (var. 41000010) et 19/41 (var. 41000000).
Les records « boîtes » non couverts pointent des judges du template hôte non réimplémentés.

**[FICHIER]** Modèles d'ID : `battleGoalID ≈ behaviorVariationId × 10` (40020→400200,
45200→452000, 62000→620000, 21200→212000, 53200→532000 pour Isshin vanilla), sauf recyclages
de goals vanilla (Malenia centrale : `logicId=170000, battleGoalID=170030`).

**[FICHIER]** IA : 3 variantes de `c9997` seulement dans le mod ; 66 états `Attack*`
(vanilla c5060) pour c4100/c2120/c6200/c6201, 83 (vanilla c5400) pour c4530, 57 (c1470)
pour c2200 ; selectors `Attack<ID>_CMSG` (199–301 par fichier). 41 EMEVD non décodés [INCONNU].

### 3.3 Régimes de densité mesurés
| | hKX rel. | judges | AttackBehavior |
|---|---|---|---|
| Artorias | 47 | 41 | 48 |
| Gael P1 (c2200) | 85 | 18 | 20 |
| Gael P2 (c6200) | 95 | 47 | 58 |
| Malenia | 118 | 90 | 100 |
| Lady Maria | 136 | 90 | 107 |

**[DÉDUIT]** Plus le boss est « central » (réception principale), plus les lignes
Behavior/AtkParam et les fenêtres d'attaque sont complètes ; les variantes « 再战 »
marient TAE du clone et familles de行为 propres.

## 4. Publications Bilibili (rapport complet : `F:/lor_source/bilibili_report.md`)

Livrables : `F:/lor_source/bilibili_videos.tsv` (156 vidéos espace 33653150),
`F:/lor_source/bilibili_comments_BV1h84y1D7Gj.tsv` (**721/721 commentaires** : 430 racines +
291 sous-réponses), `bilibili_report.md` (321 lignes, légendes [CONSTATÉ]/[DÉDUIT]/[INCONNU]).

**[CONSTATÉ]** Vidéo prioritaire `BV1h84y1D7Gj` : titre exact
« 【只狼/高燃/全新mod发布】新地图！多支线！新BOSS! 芦苇之国·空想 全新版本《尸山血海》震撼上线 »,
aid `618831875`, owner 摸鱼的心愿SAMA (mid 33653150), **publiée 2023-09-24 13:02 (UTC+8)**
(la date « 2023-09-22 » de la consigne n'apparaît nulle part), 254 221 vues / 7 981 likes /
3 089 partages / 5 530 favoris / 400 danmaku / 721 réponses, aucun épinglé, aucun sous-titre.
Description = les 3 boss (盖尔 / 女武神 / 亚尔特留斯) + 心中的狼 + 3支线/3结局 + carte
《画中世界·源之宫》, liens Quark `pan.quark.cn/s/b0fa402bf3d8`, 3DM `mod.3dmgame.com/mod/194658`,
QQ groupes 134266735 / 632684651 / 706382432.

**[CONSTATÉ]** aveux d'organisation dans les réponses de l'UP :
« 我们是双作者，新东西（盖尔、女武神）是只狼吧吧主做的，老东西（原版boss强化）是我做的 »
(boss neufs = 只狼吧吧生 = Last孤影众丶 [DÉDUIT], renforts = 摸鱼的心愿SAMA) ;
« 新版加密了，不能合的 » (build chiffré, non composable) ; « 不要用什么mod启动器 » →
installation via `引擎` + dossier `mods/` + builds numérotés.

**[CONSTATÉ]** Espaces : 33653150 = 156 vidéos (2020-01-30 → 2026-03-07), 0 hit sur les motifs
盖尔/女武神/亚尔特留斯/油画/特别版/生肉. **436916463 = 123 vidéos** (2022-06-30 → 2026-10-18)
= le bon espace : showcases `BV1iu4y197XY` (盖尔), `BV1BG411Z7sY`/`BV1bF411679u` (女武神玛莲尼亚),
`BV1m14y1u71M` (亚尔特留斯) + **23 vidéos-tutoriels** (参数编辑, 动作映射, hks, 事件编辑,
地图新建, 移植/特效转换…) = le pipeline réel publié, crédité 琐帝BNU / 莫佬 / 若叶姐 / 苏一儿
(« ai由我和@琐帝BNU 编写 »).

**[INCONNU]** aucun logiciel nommé dans les métadonnées/commentaires (0 hit MapStudio/Smithbox/…) ;
aucune question « ordres d'objets/param » dans les 721 commentaires ; les vidéos-tutoriels n'ont pas
été visionnées (téléchargement interdit) — leurs titres sont donc la seule trace offline exploitable.

**[CONSTATÉ] limites de collecte** : pagination des réponses via `x/v2/reply/main` signé
(appkey + cookie `buvid3`), `x/v2/reply/wbi/main` → `-403` hors session, `x/space/arc/search`
→ `412 request was banned` (exceptions notées), titre affiché en anglais par la page `/en/`
puis corrigé par `x/web-interface/view` sur chaque BV ; `space_33653150.lst` introuvable
(fichier inexistant → liste reconstruite depuis la page espace).

## 5. Chaîne d'import des auteurs (ce que les fichiers prouvent)

- **[FICHIER]** Tous les chemins d'entrée internes suivent la convention vanilla
  `N:\NTC\data\Target\INTERROOT_win64\chr\cXXXX\hkx_compendium\…` (`NTC` = projet Sekiro :
  `standalone/game_profiles.py` du Bridge : `/ntc/→sekiro, /frpg/→ds1, /fdp/→ds3, /gr/→er`).
  **[FICHIER]** Le vanilla possède déjà ces chemins (notes/01, `c0000_a000_hi`) → l'absence de
  fuite de devkit dans ces chaînes héréditées ; en revanche les MATÉRIAUX des textures portent
  aussi des habitats sources : `\FDP\…` (DS3, ex. armure `FB_M_8200`), `\FRPG2\…` (jeu
  ancien), `\LiveTokyo\…` [FAIT chaîne ; INCONNU provenance exacte de l'obtention].
- **[FICHIER]** 3 matériaux nommés `untitled.fbx_c4100_*` → **étape FBX intermédiaire** avec
  nom de scène par défaut. **[DÉDUIT]** DCC = Blender (« untitled » = nom de scène neuve) ;
  aucun indice `Maya/Max`. `[DÉDUIT]` conversion HKX par outillage habituel (SDK Havok 2016
  `SDKV20160200` vu dans les HKB = normal pour le format 2016 du jeu).
- **[FICHIER]** HKB : aucun auteur d'arbre → **patch d'octets sur copie vanilla** (6 B) ;
  TAE : clone du hôte + réécriture d'événements ; params : familles neuves `2219xxxx`,
  `24002xxxx`, `21200xxxx`… écrites en `gameparam.parambnd.dcx` [FICHIER].
- **[FICHIER]** **Sekiro Animation Bridge** (évalué) : dépôt `F:/simon_research`, commit unique
  2026‑11‑13 (release 0.15.0), add‑on exigé Blender 4.5 → **postérieur au développement LoR
  (2023‑2025) : LoR ne l'a pas utilisé**. Capacités actuelles (README/docs + code) : import
  `.anibnd/.chrbnd/.partsbnd` → scène Blender éditable (rig, skins, textures), export HKX+`.motion.json`,
  écriture optionnelle dans un brouillon de binder, retarget inter-personnages (bones
  différents), rig de contrôle IK/FK, **caractéristiques neuves** « écrire un nouveau
  personnage Sekiro depuis Blender » (testé debout/idle, **pas encore testé en jeu**),
  jeux tiers (DS3/ER/DMC5 import ; DMC5 package). Limites : prototype, tests hors‑jeu non
  faits, sortie binder compatible avec WitchyBND.
- **[FICHIER]** DSAnimStudio (`F:/simon_research`) : sert ici de **vérité de référence**
  (template événements TAE SDT, simulateur de TAE, `ParamData.*`, compendium) — plausible que
  les auteurs aient manipulé TAE de la sorte, mais le lien de causalité leur outil exact
  reste **[INCONNU]** (aucun binaire d'outil dans l'archive).

## 6. Ce qui est réutilisable pour Simon

1. **MSB record names comme boussole de test** : garder des records explicites pour valider le spawn.
2. **Module `AttackBehavior` bit‑à‑bit** : déjà opérationnel (session Isshin : `judge 90`,
   fenêtre 1,5000‑1,6333 s) → outil de contrôle de cohérence TAE↔BehaviorParam↔AtkParam.
3. **Familles de behaviorVariant propres** (pattern `variationId=xxxx0`, `ligne id=hôte+index`)
   → nouvelle famille Simon sans toucher au vanilla.
4. **HKB sans authored** : host = copie vanilla + patch 6 octets = risque minimal, adopté par
   les 6 cibles confirment le modèle.
5. **couverture Hitbox/lame** (résultats c5400) + notre mesure corps (ω, v_pointe) : outillage
   QS inexistants chez LoR à notre connaissance [INCONNU pour eux].
6. **Réponses aux patterns de densité** : viser ≥90 judge couverts/100 pour un boss majeur.
7. **Canaux msg/menu/EMEVD** : LoR ajoute 41 EMEVD + msg — pour Simon en 1er combat, réutiliser
   l'emplacement existant comme fait Isshin (identique stratégique avec #7).
8. **Blender→FBX→HKX→binder** confirmé le dénominateur du secteur → notre pont PSA/anim2 garde
   un avantage : contrôle précis sur la retarget (validation FK vs oracle 0,0013–0,0034 u).

## 7. Comparaison des 3 architectures

**A. Modifier un NPC existant (modèle = LoR sur IDs vanilla : c9000…)** — remplacer modèle et
animations d'un emplacement déjà référencé. *Avantages* : zéro nouveau spawn, IA déjà câblée,
params existants, tests rapides. *Limites* : identité du PNJ attachée (nom, arena, phases),
conflits de slots de maillages (gabarit) — nous l'avons vécu avec la calibration d'échelle et
les meshes 12/30/31/32 cassés sur c5400.

**B. Empocher de nouvelles animations dans le moveset existant (nous : c5400 + 6 clips)** —
TAE/231 frames/HKX injectés, liens `Animation → AtkParam` déjà validés, état
`Attack3011` + sélecteur `Attack3011_CMSG` réutilisés. *Limites* : comportement contraint
par les états/branches vanilla (Isshin), intelligence limitée à l'arbre hôte, identité du boss
enfermée dans « le boss d'Isshin ».

**C. Personnage indépendant (Modèle = LoR c2120/c4530/… : 31 nouveaux IDs)** — 4 archives +
params propres + spawn MSB. *Preuve par LoR* : pas de création d'arbre HKB (hôte + patch),
TAE clonés/écrits, familles Behavior/AtkParam neuves, réaffichage en jeu (changelog +
vidéos). *Limites* : droits éditoriaux lourds (FLVER, tex, compendium, TAE complet),
une arena + EMEVD par spawn, phases = lignes de params plutôt que features HKB natives.

## 8. Recommandation (arguée)

**C, en appliquant délibérément la recette LoR plutôt que B** : nouveau `cXXXX` pour
Simon (indépendance totale de la trame d'Isshin, comme demandé), **arbre HKB = clone
d'hôte vanilla avec patch d'ID** (risque minimal, standard observé sur 6/6 cibles LoR),
**TAE cloné depuis le même hôte puis réécrit** (garantit tous les événements utilitaires :
sons, FFX, stamina, Blend…), **BehaviorParam/AtkParam en familles neuves** liées à un
`behaviorVariationId` dédié (jamais modifions un row vanilla partagé), **MSB record + NpcParam
+ NpcThinkParam dédiés** (battlesystem « 40 m de portée » comme les boss LoR).
Justification chiffrée : (a) la couverture juge→famille prouve que la personnalisation réelle
est là ; (b) le patch 6 octets évite tout craft Havok, le plus gros risque connu (notre
expérience HKB sur ceux de c5400 : lisière étroite) ; (c) LoR tient 31 personnages avec cette
recette, c'est robuste ; (d) notre avantage : outils de mesure (couverture lame 97,5 %,
fenêtres ω, mesures en repère corps) injectés dans la boucle de test avant commission.
Écarter A (identité impose le modèle de départ) ; garder B comme filet si l'hôte se révèle
trop pauvre (Isshin = 90 judges : plafond probable).

## 9. Plan priorisé (sans exécution, ordonné)

1. **Choisir l'hôte HKB** : comparer les familles de behavior (c5400 vs c5060 vs c1470) sur
   nos besoins (déplacements, combos) — comparatif mesuré des 3 familles (déjà
   mesurables via `_work/lor/attacks_tae.json`).
2. **Gel des contenus** : 6 clips Simon (Skill_1, 231 images existantes) → ID de TAE attribué,
   fenêtre de coup + judge fixés (outillage `judge`+AtkParam déjà testé).
3. **Créer l'ID cXXXX** : 4 archives vides→clones d'hôte (pattern LoR), FLVER Simon
   (déjà prêt : mesh10 + dummies 10/11 + couverture 97,5 %), textures, `.clm2`.
4. **Paramètres** : NpcParam (hp/stamina/behaviorVariationId), familles BehaviorParam/AtkParam
   neuves, NpcThinkParam (logicId hôte + `battleGoalID=variationId×10`).
5. **Spawn** : record MSB explicite dans arena d'Isshin (m10_01 ? m10_00… à valider) avec
   NPCParamID propre, pas de EMEVD sauf conditions.
6. **Boucle de test mesurée** : couverture ω/v_pointe en repère corps (nos PNG/JSON), inclure
   regression les 6 clips.
7. **Puis seulement** phases/Behavior profonds (si le plafond de 90 judges est atteint),
   effets/sons approfondis (le template hérité de l'hôte fournit déjà FFX/son/stamina).
8. **En parallèle** : intégration du relevé Bilibili (rapport séparé) et relecture de cette note.
