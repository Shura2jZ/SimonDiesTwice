// FlverInject.exe -- injecte la geometrie preparee (format intermediaire ecrit
// par tools/simon_export.py) dans un FLVER, en remplacant ses maillages.
//
// Usage :
//     FlverInject.exe <source.flver> <intermediaire.bin> <sortie.flver> [--garder] [--remplacer]
//                     [--slots 6,7,3,5,0] [--boite-origine] [--attributs-glb]
//
//   --garder    : ne supprime pas les maillages d'origine (diagnostic).
//   --remplacer : ecrit nos maillages PAR-DESSUS les premiers emplacements de
//                 maillages d'origine, sans changer leur nombre. La boite
//                 englobante de chaque emplacement est recalculee sur nos
//                 sommets (option --boite-origine : conserver celle de
//                 l'emplacement d'origine). Celle de l'en-tete est conservee.
//
//                 C'est le mode a utiliser en jeu : les masques de dessin des
//                 animations (ChangeDrawMask du .tae) referencent 33 maillages,
//                 donc le modele doit conserver ses 33 emplacements. Avec moins
//                 de maillages que de bits dans le masque, le moteur lit et
//                 ecrit hors du tableau et dessine de la geometrie aleatoire.
//
// Ce qui est repris de l'original, pour chaque nouveau maillage :
//   - le materiau (choisi par le script Python) et le noeud porteur ;
//   - la structure des facesets (drapeaux, cull) du maillage d'origine
//     utilisant le meme materiau, avec nos indices ;
//   - le champ unk06 des facesets est RECALCULE sur nos sommets (voir plus bas) ;
//   - le bbox est recalcule sur nos sommets (sauf en mode --remplacer).
//
// CHAMP unk06 DES FACESETS = TAILLE DE LA PALETTE D'OS DU MAILLAGE.
// Mesure : sur les 33 maillages de la vanille de c5400, unk06 egale exactement
// le nombre d'indices d'os distincts NON NULS references par les sommets du
// maillage (33/33 exacts ; outil de mesure : _work/tools/cs/FlverOsCompte.cs).
// Exemples vanille : casque 1 (rigide), cils 7, tete 31, corps 81, cheveux 27.
// C'est une propriete DU MAILLAGE, pas du materiau : deux maillages partageant
// le materiau 21 ont 21 et 16.
// L'ancien code recopiait cette valeur depuis le gabarit du materiau : nos
// maillages 6 (manteau) et 7 (haut) declaraient 19 alors qu'ils utilisent 26 et
// 32 os, donc le moteur lisait au-dela de la palette allouee et le skinning
// explosait (geometrie geante couvrant l'ecran, personnage invisible).
//
//   - la disposition de sommets : position, normale et tangente du GLB ;
//   - le W de normale 0 et la couleur de sommet (255,0,0,255), valeurs
//     neutres mesurees sur les 33 maillages de la vanille (--attributs-glb
//     pour garder les valeurs du GLB, diagnostic).
//
// PIEGE VERIFIE : FLVER.VertexColor a pour champs (A, R, G, B) et pour
// constructeur (a, r, g, b) -- et non (r, g, b, a). L'ancien appel rangeait la
// valeur du gris du GLB (0,392) dans l'alpha : tous nos sommets sortaient a
// alpha 0,39, donc transparents et assombris.
//
// La disposition de sommets utilisee est le n°7 (celle du corps d'Isshin) :
//   Position:Float3  Normal:UByte4  Tangent:UByte4  BoneIndices:UByte4
//   BoneWeights:UByte4Norm  VertexColor1:UByte4Norm  UV:Short4        = 40 octets
// C'est une disposition a un seul tampon, deja utilisee par ce personnage :
// rien a inventer cote disposition.

using System;
using System.Collections.Generic;
using System.IO;
using System.Numerics;
using System.Text;
using SoulsFormats;

internal static class FlverInject
{
    private const int LAYOUT_DEFAUT = 7;

    // --- gabarit repris d'un maillage existant -----------------------------
    private sealed class Gabarit
    {
        public int Materiau;
        public int Layout;
        public byte Dynamique = 1;
        public bool Poids = true;
        public List<int[]> Facesets = new List<int[]>();   // [flags, strip, cull, unk]
        public int NbFacesets;
        public List<int> Os = new List<int>();
    }

    private static int Main(string[] args)
    {
        if (args.Length < 3)
        {
            Console.WriteLine("usage : FlverInject.exe <source.flver> <intermediaire.bin> <sortie.flver> [--garder] [--remplacer]");
            return 2;
        }
        string fSource = args[0], fInter, fSortie;
        fInter = args[1];
        fSortie = args[2];
        bool garder = Array.IndexOf(args, "--garder") >= 0;
        bool remplacer = Array.IndexOf(args, "--remplacer") >= 0;
        int[] emplacementsChoisis = null;
        for (int i = 3; i < args.Length; i++)
        {
            if (args[i] == "--slots" && i + 1 < args.Length)
            {
                string[] morceaux = args[i + 1].Split(',');
                emplacementsChoisis = new int[morceaux.Length];
                for (int k = 0; k < morceaux.Length; k++)
                {
                    emplacementsChoisis[k] = int.Parse(morceaux[k]);
                }
            }
        }
        int layoutForce = -1;
        for (int i = 3; i < args.Length; i++)
        {
            if (args[i] == "--layout" && i + 1 < args.Length)
            {
                layoutForce = int.Parse(args[i + 1]);
            }
        }
        // par defaut (mode --remplacer), la boite englobante de chaque emplacement
        // est recalculee sur NOS sommets ; --boite-origine restaure l'ancien
        // comportement (boite de l'emplacement d'origine) pour comparer.
        bool boiteOriginelle = Array.IndexOf(args, "--boite-origine") >= 0;

        // --echelle : homothetie du personnage. Les positions locales des noeuds
        // (bind pose du rig) sont multipliees : le jeu deforme alors le maillage
        // dans un rig agrandi, et Simon garde ses proportions.
        float echelle = 1.0f;
        for (int i = 3; i < args.Length; i++)
        {
            if (args[i] == "--echelle" && i + 1 < args.Length)
            {
                echelle = float.Parse(args[i + 1], System.Globalization.CultureInfo.InvariantCulture);
            }
        }

        // --- attributs de sommet -------------------------------------------
        // Mesure : sur les 33 maillages de la vanille, le W de normale vaut 0
        // et la couleur de sommet est la CONSTANTE (255,0,0,255), sur tous les
        // sommets de tous les maillages. Ce sont donc des champs neutres, et
        // seuls NOS maillages s'en ecartent (W = 255, couleurs du GLB de Simon
        // avec un alpha a 0,24-0,4). On ecrit desormais les valeurs neutres de
        // la vanille ; --attributs-glb restaure l'ancien comportement (valeurs
        // venues du GLB) pour comparer.
        bool attributsGlb = Array.IndexOf(args, "--attributs-glb") >= 0;

        FLVER2 flver = FLVER2.Read(fSource);
        Console.WriteLine("source        : " + fSource);
        Console.WriteLine("  os          : " + flver.Nodes.Count);
        Console.WriteLine("  materiaux   : " + flver.Materials.Count);
        Console.WriteLine("  maillages   : " + flver.Meshes.Count);
        Console.WriteLine("  dispositions : " + flver.BufferLayouts.Count);

        // --echelle : agrandit le rig autour de Master (origine, au sol).
        // Root est un enfant de Master et sa translation locale doit donc aussi
        // etre multipliee; ne pas la scaler decale tout le personnage en hauteur.
        if (echelle != 1.0f)
        {
            int nn = 0;
            foreach (FLVER.Node nd in flver.Nodes)
            {
                if (nd.Name == "Master") continue;
                nd.Translation = nd.Translation * echelle;
                nn++;
            }
            Console.WriteLine("  echelle      : " + echelle.ToString("0.###") + " appliquee a " + nn + " noeuds (pivot Master conserve)");
        }

        // --- gabarits, avant toute modification ----------------------------
        Dictionary<int, Gabarit> gabarits = new Dictionary<int, Gabarit>();
        foreach (FLVER2.Mesh m in flver.Meshes)
        {
            int mat = m.MaterialIndex;
            if (gabarits.ContainsKey(mat))
            {
                continue;
            }
            Gabarit g = new Gabarit();
            g.Materiau = mat;
            g.Layout = layoutForce >= 0 ? layoutForce
                                        : (m.VertexBuffers.Count > 0 ? m.VertexBuffers[0].LayoutIndex : LAYOUT_DEFAUT);
            g.Dynamique = m.Dynamic;
            g.Poids = m.UseBoneWeights;
            foreach (FLVER2.FaceSet fs in m.FaceSets)
            {
                g.Facesets.Add(new int[] { (int)fs.Flags, fs.TriangleStrip ? 1 : 0,
                                           fs.CullBackfaces ? 1 : 0, (int)fs.Unk06 });
            }
            g.NbFacesets = m.FaceSets.Count;
            g.Os.AddRange(m.BoneIndices);
            gabarits[mat] = g;
        }
        Console.WriteLine("gabarits      : " + gabarits.Count);
        foreach (KeyValuePair<int, Gabarit> kv in gabarits)
        {
            Console.WriteLine("  materiau " + kv.Key + " -> disposition " + kv.Value.Layout
                              + ", " + kv.Value.Facesets.Count + " facesets, os en palette "
                              + kv.Value.Os.Count);
        }

        // --- lecture de l'intermediaire ------------------------------------
        List<Maillage> maillages = new List<Maillage>();
        using (BinaryReader r = new BinaryReader(File.OpenRead(fInter), Encoding.UTF8))
        {
            byte[] magie = r.ReadBytes(8);
            string m8 = Encoding.ASCII.GetString(magie);
            if (!m8.StartsWith("SMPORT"))
            {
                Console.WriteLine("ERREUR : entete inconnue (" + m8 + ")");
                return 3;
            }
            int nbMaillages = r.ReadInt32();
            float[] axe = new float[9];
            for (int i = 0; i < 9; i++)
            {
                axe[i] = r.ReadSingle();
            }
            int nbOs = r.ReadInt32();
            Dictionary<int, string> nomOs = new Dictionary<int, string>();
            for (int i = 0; i < nbOs; i++)
            {
                int n = r.ReadInt32();
                string nom = Encoding.UTF8.GetString(r.ReadBytes(n));
                int noeud = r.ReadInt32();
                nomOs[noeud] = nom;
            }
            Console.WriteLine("intermediaire : " + nbMaillages + " maillages, " + nbOs + " os");
            Console.WriteLine("  axe         : [" + axe[0] + " " + axe[1] + " " + axe[2] + " ; "
                              + axe[3] + " " + axe[4] + " " + axe[5] + " ; "
                              + axe[6] + " " + axe[7] + " " + axe[8] + "]");

            for (int m = 0; m < nbMaillages; m++)
            {
                Maillage ma = new Maillage();
                int ln = r.ReadInt32();
                ma.Nom = Encoding.UTF8.GetString(r.ReadBytes(ln));
                ma.Materiau = r.ReadInt32();
                ma.Noeud = r.ReadInt32();
                ma.GabaritForce = r.ReadInt32();
                ma.NbSommets = r.ReadInt32();
                ma.NbIndices = r.ReadInt32();
                for (int v = 0; v < ma.NbSommets; v++)
                {
                    Sommet s = new Sommet();
                    s.Position = new Vector3(r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
                    s.Normal = new Vector3(r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
                    s.Tangente = new Vector4(r.ReadSingle(), r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
                    s.Uv = new Vector2(r.ReadSingle(), r.ReadSingle());
                    s.Couleur = new Vector4(r.ReadSingle(), r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
                    s.Os = new int[4];
                    s.Poids = new float[4];
                    for (int k = 0; k < 4; k++)
                    {
                        s.Os[k] = r.ReadInt32();
                    }
                    for (int k = 0; k < 4; k++)
                    {
                        s.Poids[k] = r.ReadSingle();
                    }
                    ma.Sommets.Add(s);
                }
                for (int i = 0; i < ma.NbIndices; i++)
                {
                    ma.Indices.Add(r.ReadInt32());
                }
                maillages.Add(ma);
                Console.WriteLine("  " + ma.Nom + " : " + ma.NbSommets + " sommets, "
                                  + (ma.NbIndices / 3) + " triangles, materiau " + ma.Materiau
                                  + ", noeud " + ma.Noeud);
            }
        }

        // --- construction --------------------------------------------------
        Console.WriteLine();
        Console.WriteLine("=== construction ===");
        if (!garder && !remplacer)
        {
            flver.Meshes.Clear();
        }
        int emplacement = 0;
        foreach (Maillage ma in maillages)
        {
            Gabarit g;
            if (ma.GabaritForce >= 0 && gabarits.ContainsKey(ma.GabaritForce))
            {
                g = gabarits[ma.GabaritForce];
            }
            else if (gabarits.ContainsKey(ma.Materiau))
            {
                g = gabarits[ma.Materiau];
            }
            else
            {
                g = null;
                foreach (KeyValuePair<int, Gabarit> kv in gabarits)
                {
                    g = kv.Value;
                    break;
                }
                if (g != null)
                {
                    Console.WriteLine("  " + ma.Nom + " : aucun gabarit pour le materiau "
                                      + ma.Materiau + ", reprise du materiau " + g.Materiau);
                }
            }
            if (g == null)
            {
                Console.WriteLine("ERREUR : aucun gabarit disponible");
                return 4;
            }
            if (!g.Poids)
            {
                Console.WriteLine("  ATTENTION : le gabarit du materiau " + g.Materiau + " n'utilise pas de poids");
            }

            FLVER2.Mesh mn = new FLVER2.Mesh();
            mn.MaterialIndex = ma.Materiau;
            mn.NodeIndex = ma.Noeud;
            mn.Dynamic = g.Dynamique;
            mn.UseBoneWeights = true;
            mn.BoneIndices = new List<int>();

            mn.VertexBuffers = new List<FLVER2.VertexBuffer>();
            mn.VertexBuffers.Add(new FLVER2.VertexBuffer(g.Layout));

            foreach (Sommet s in ma.Sommets)
            {
                FLVER.Vertex v = new FLVER.Vertex();
                v.Position = s.Position;
                v.Normal = s.Normal;
                v.NormalW = attributsGlb ? -1 : 0;
                v.Tangents = new List<Vector4>();
                v.Tangents.Add(s.Tangente);
                v.Tangents.Add(s.Tangente);
                v.Bitangent = s.Tangente;
                v.UVs = new List<Vector3>();
                v.UVs.Add(new Vector3(s.Uv.X, s.Uv.Y, 0.0f));
                v.UVs.Add(new Vector3(s.Uv.X, s.Uv.Y, 0.0f));
                v.UVs.Add(new Vector3(s.Uv.X, s.Uv.Y, 0.0f));
                // ATTENTION : FLVER.VertexColor declare ses champs dans l'ordre
                // A, R, G, B et son constructeur est (a, r, g, b) -- PAS
                // (r, g, b, a). Mesure : avec l'ancien ordre, la couleur de
                // Simon (0,392 0,392 0,392 1,0) arrivait en (a=0,392 r=0,392
                // g=0,392 b=1,0) : alpha 0,39 sur TOUS les sommets, donc
                // personnage transparent a 40 % et assombri de 60 %.
                // La vanille porte (R,G,B,A) = (255,0,0,255), soit les champs
                // A=255, R=255, G=0, B=0 -> arguments (a, r, g, b).
                v.Colors = new List<FLVER.VertexColor>();
                v.Colors.Add(attributsGlb
                    ? new FLVER.VertexColor(
                        (byte)Math.Min(255.0f, Math.Max(0.0f, s.Couleur.W * 255.0f)),
                        (byte)Math.Min(255.0f, Math.Max(0.0f, s.Couleur.X * 255.0f)),
                        (byte)Math.Min(255.0f, Math.Max(0.0f, s.Couleur.Y * 255.0f)),
                        (byte)Math.Min(255.0f, Math.Max(0.0f, s.Couleur.Z * 255.0f)))
                    : new FLVER.VertexColor((byte)255, (byte)255, (byte)0, (byte)0));
                for (int k = 0; k < 4; k++)
                {
                    v.BoneIndices[k] = (byte)s.Os[k];
                    v.BoneWeights[k] = s.Poids[k];
                }
                mn.Vertices.Add(v);
            }

            // Taille de la palette d'os de CE maillage : nombre d'indices d'os
            // distincts non nuls references par nos sommets. C'est la valeur que
            // la vanille met dans unk06 (33/33 exacts). Le gabarit ne fournit que
            // les drapeaux et le cull ; unk06 decrit NOS sommets.
            HashSet<int> osDistincts = new HashSet<int>();
            foreach (Sommet s in ma.Sommets)
            {
                for (int k = 0; k < 4; k++)
                {
                    if (s.Os[k] != 0)
                    {
                        osDistincts.Add(s.Os[k]);
                    }
                }
            }
            int palette = osDistincts.Count;

            mn.FaceSets = new List<FLVER2.FaceSet>();
            if (g.Facesets.Count == 0)
            {
                FLVER2.FaceSet fs = new FLVER2.FaceSet();
                fs.Flags = 0;
                fs.TriangleStrip = false;
                fs.CullBackfaces = false;
                fs.Unk06 = (short)palette;
                fs.Indices = ma.Indices;
                mn.FaceSets.Add(fs);
            }
            else
            {
                foreach (int[] spec in g.Facesets)
                {
                    FLVER2.FaceSet fs = new FLVER2.FaceSet();
                    fs.Flags = (FLVER2.FaceSet.FSFlags)spec[0];
                    fs.TriangleStrip = spec[1] != 0;
                    fs.CullBackfaces = spec[2] != 0;
                    fs.Unk06 = (short)palette;
                    fs.Indices = ma.Indices;
                    mn.FaceSets.Add(fs);
                }
            }

            // bbox du maillage
            Vector3 lo = ma.Sommets[0].Position, hi = lo;
            foreach (Sommet s in ma.Sommets)
            {
                lo = Vector3.Min(lo, s.Position);
                hi = Vector3.Max(hi, s.Position);
            }
            if (!remplacer)
            {
                mn.BoundingBox = new FLVER2.Mesh.BoundingBoxes();
                mn.BoundingBox.Min = lo;
                mn.BoundingBox.Max = hi;
                mn.BoundingBox.Unk = Vector3.Zero;
            }

            int cible = (emplacementsChoisis != null && emplacement < emplacementsChoisis.Length)
                        ? emplacementsChoisis[emplacement]
                        : emplacement;
            if (remplacer && cible >= 0 && cible < flver.Meshes.Count)
            {
                // on reprend l'emplacement : materiau, noeud et structure des
                // facesets viennent du gabarit ; la geometrie est la notre.
                FLVER2.Mesh ancien = flver.Meshes[cible];
                if (boiteOriginelle && ancien.BoundingBox != null)
                {
                    // ancien comportement : boite de l'emplacement d'origine, qui ne
                    // decrit plus la geometrie qu'on vient d'y mettre.
                    mn.BoundingBox = ancien.BoundingBox;
                }
                else
                {
                    // boite recalculee sur nos sommets : cette boite doit contenir la
                    // geometrie reellement presente dans l'emplacement.
                    mn.BoundingBox = new FLVER2.Mesh.BoundingBoxes();
                    mn.BoundingBox.Min = lo;
                    mn.BoundingBox.Max = hi;
                    mn.BoundingBox.Unk = ancien.BoundingBox != null
                        ? ancien.BoundingBox.Unk
                        : Vector3.Zero;
                }
                flver.Meshes[cible] = mn;
                Console.WriteLine("  " + ma.Nom + " : ecrit dans l'emplacement " + cible
                                  + " (" + mn.FaceSets.Count + " facesets, disposition " + g.Layout
                                  + ", palette d'os " + palette
                                  + ", boite " + V(mn.BoundingBox.Min)
                                  + " .. " + V(mn.BoundingBox.Max)
                                  + (boiteOriginelle ? " [origine]" : " [recalculee]")
                                  + ", nos sommets " + V(lo) + " .. " + V(hi) + ")");
            }
            else
            {
                if (remplacer)
                {
                    mn.BoundingBox = new FLVER2.Mesh.BoundingBoxes();
                    mn.BoundingBox.Min = lo;
                    mn.BoundingBox.Max = hi;
                    mn.BoundingBox.Unk = Vector3.Zero;
                }
                flver.Meshes.Add(mn);
                Console.WriteLine("  " + ma.Nom + " : ecrit (" + mn.FaceSets.Count + " facesets, disposition "
                                  + g.Layout + ", bbox " + V(lo) + " .. " + V(hi) + ")");
            }
            emplacement++;
        }

        // --- bbox d'en-tete -------------------------------------------------
        Vector3 hlo = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue);
        Vector3 hhi = new Vector3(float.MinValue, float.MinValue, float.MinValue);
        foreach (FLVER2.Mesh m in flver.Meshes)
        {
            foreach (FLVER.Vertex v in m.Vertices)
            {
                hlo = Vector3.Min(hlo, v.Position);
                hhi = Vector3.Max(hhi, v.Position);
            }
        }
        if (flver.Meshes.Count > 0 && !remplacer)
        {
            flver.Header.BoundingBoxMin = hlo;
            flver.Header.BoundingBoxMax = hhi;
            Console.WriteLine("bbox en-tete  : " + V(hlo) + " .. " + V(hhi));
        }
        else if (remplacer)
        {
            Console.WriteLine("bbox en-tete  : conservee (" + V(flver.Header.BoundingBoxMin)
                              + " .. " + V(flver.Header.BoundingBoxMax)
                              + ") ; union de tous les maillages = " + V(hlo) + " .. " + V(hhi));
        }

        // --- dummies referencant un maillage ? ------------------------------
        int refsNegatives = 0;
        foreach (FLVER.Dummy d in flver.Dummies)
        {
            if (d.ReferenceID < 0)
            {
                refsNegatives++;
            }
        }
        Console.WriteLine("dummies       : " + flver.Dummies.Count
                          + " (dont " + refsNegatives + " a reference negative, possible reference de maillage)");

        // --- ecriture ------------------------------------------------------
        flver.Write(fSortie);
        Console.WriteLine();
        Console.WriteLine("ecrit         : " + fSortie + " ("
                          + new FileInfo(fSortie).Length + " octets)");

        // --- correction du champ d'en-tete 0x40 ----------------------------
        // SoulsFormats ecrit 0x40 == 0x44 (total des faces), la vanille y met la
        // somme des faces des facesets SANS le drapeau MotionBlur (0x80000000).
        // Mesure sur la vanille de c5400 : 0x40 = 262 326, 0x44 = 562 486.
        {
            int facesHorsMb = 0;
            int facesTotales = 0;
            foreach (FLVER2.Mesh mm in flver.Meshes)
            {
                foreach (FLVER2.FaceSet fs in mm.FaceSets)
                {
                    int nbFaces = fs.Indices.Count / 3;
                    facesTotales += nbFaces;
                    if (((uint)fs.Flags & 0x80000000u) == 0)
                        facesHorsMb += nbFaces;
                }
            }
            byte[] octets = File.ReadAllBytes(fSortie);
            int ancien = BitConverter.ToInt32(octets, 0x40);
            if (ancien != facesHorsMb)
            {
                Array.Copy(BitConverter.GetBytes(facesHorsMb), 0, octets, 0x40, 4);
                File.WriteAllBytes(fSortie, octets);
                Console.WriteLine("entete 0x40   : " + ancien + " -> " + facesHorsMb
                                  + " (faces hors motion blur ; 0x44 = " + facesTotales + ")");
            }
            else
            {
                Console.WriteLine("entete 0x40   : " + facesHorsMb + " (deja conforme)");
            }
        }

        // --- verification : relecture --------------------------------------
        Console.WriteLine();
        Console.WriteLine("=== verification (relecture) ===");
        FLVER2 relu = FLVER2.Read(fSortie);
        Console.WriteLine("  maillages relus : " + relu.Meshes.Count);
        if (remplacer)
        {
            Console.WriteLine("  (mode --remplacer : " + relu.Meshes.Count + " emplacements au total, "
                              + maillages.Count + " remplaces par notre geometrie)");
        }
        int decalage = garder ? relu.Meshes.Count - maillages.Count : 0;
        for (int i = 0; i < maillages.Count; i++)
        {
            Maillage ma = maillages[i];
            int emplacementRelu = i + decalage;
            if (remplacer && emplacementsChoisis != null && i < emplacementsChoisis.Length)
            {
                emplacementRelu = emplacementsChoisis[i];
            }
            if (emplacementRelu < 0 || emplacementRelu >= relu.Meshes.Count)
            {
                Console.WriteLine("  [" + i + "] " + ma.Nom + " : emplacement " + emplacementRelu
                                  + " hors limites, verification impossible");
                continue;
            }
            FLVER2.Mesh m = relu.Meshes[emplacementRelu];
            double dpos = 0.0, dnorm = 0.0, duv = 0.0, dpoids = 0.0;
            int indicesOsIdentiques = 1, nbOsNuls = 0;
            for (int v = 0; v < m.Vertices.Count && v < ma.Sommets.Count; v++)
            {
                FLVER.Vertex rv = m.Vertices[v];
                Sommet s = ma.Sommets[v];
                dpos = Math.Max(dpos, (rv.Position - s.Position).Length());
                dnorm = Math.Max(dnorm, (rv.Normal - s.Normal).Length());
                duv = Math.Max(duv, (rv.UVs[0] - new Vector3(s.Uv.X, s.Uv.Y, 0)).Length());
                double somme = 0.0;
                for (int k = 0; k < 4; k++)
                {
                    if (rv.BoneIndices[k] != (byte)s.Os[k])
                    {
                        indicesOsIdentiques = 0;
                    }
                    if (rv.BoneIndices[k] == 0)
                    {
                        nbOsNuls++;
                    }
                    somme += rv.BoneWeights[k] - s.Poids[k];
                }
                dpoids = Math.Max(dpoids, Math.Abs(somme));
            }
            Console.WriteLine("  [" + i + "] " + ma.Nom + " : emplacement " + emplacementRelu
                              + ", sommets " + m.Vertices.Count
                              + " (attendu " + ma.Sommets.Count + "), facesets " + m.FaceSets.Count
                              + ", materiau " + m.MaterialIndex + ", noeud " + m.NodeIndex);
            Console.WriteLine("      ecarts max : position " + dpos.ToString("0.00000")
                              + ", normale " + dnorm.ToString("0.00000")
                              + ", uv " + duv.ToString("0.00000")
                              + ", poids " + dpoids.ToString("0.00000")
                              + ", indices d'os conserves : " + (indicesOsIdentiques == 1 ? "OUI" : "NON"));
        }
        return 0;
    }

    private sealed class Sommet
    {
        public Vector3 Position;
        public Vector3 Normal;
        public Vector4 Tangente;
        public Vector2 Uv;
        public Vector4 Couleur;
        public int[] Os;
        public float[] Poids;
    }

    private sealed class Maillage
    {
        public string Nom;
        public int Materiau;
        public int Noeud;
        public int GabaritForce;
        public int NbSommets;
        public int NbIndices;
        public List<Sommet> Sommets = new List<Sommet>();
        public List<int> Indices = new List<int>();
    }

    private static string V(Vector3 v)
    {
        return "(" + v.X.ToString("0.000") + ", " + v.Y.ToString("0.000") + ", " + v.Z.ToString("0.000") + ")";
    }
}
