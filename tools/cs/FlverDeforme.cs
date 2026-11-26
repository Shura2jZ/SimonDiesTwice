// FlverDeforme - applique une pose d'animation a un FLVER en deformant les
// sommets exactement comme le moteur, puis ecrit un FLVER dont les positions
// sont deja deformees. Rendu sans pose = ce que le jeu affiche a cet instant.
//
// Le melange lineaire de peaux est :
//     p = somme_b  poids_b * ( pose_b * (bind_b)^-1 * v )
// ou bind_b est la transformation globale du noeud b dans le FLVER lui-meme
// (la pose de reference) et pose_b celle fournie pour l'animation.
//
// C'est l'oracle hors jeu : on peut rejouer une VRAIE animation et comparer un
// modele d'origine a un modele modifie dans exactement les memes conditions.
//
// Usage : FlverDeforme.exe <entree.flver> <pose.tsv> <sortie.flver>
//
// pose.tsv : une ligne par os : nom<TAB>m11 m12 m13 m14 m21 ... m44
// (matrice 4x4 ligne par ligne, convention ligne, comme le TSV d'ossature).
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Numerics;
using SoulsFormats;

internal static class FlverDeforme
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    private static FLVER2 g;
    private static Matrix4x4[] g_local, g_global;
    private static bool[] g_done;
    private static double[] deplParOs;
    private static int[] compteParOs;
    private static Vector3[] miniParOs, maxiParOs;

    private static double Etendue(int i)
    {
        if (compteParOs[i] == 0) return -1.0;
        Vector3 e = maxiParOs[i] - miniParOs[i];
        return Math.Max(e.X, Math.Max(e.Y, e.Z));
    }

    private static string LigneOs(int i)
    {
        Vector3 e = maxiParOs[i] - miniParOs[i];
        Vector3 centre = (maxiParOs[i] + miniParOs[i]) * 0.5f;
        Vector3 origine = new Vector3(g_global[i].M41, g_global[i].M42, g_global[i].M43);
        double d = (centre - origine).Length();
        return string.Format(Inv,
            "os {0,4} {1,-26} sommets {2,6}   depl max {3,7:0.####} m   emprise ({4:0.##} {5:0.##} {6:0.##})   centre a {7:0.###} m de l'os",
            i, g.Nodes[i].Name, compteParOs[i], deplParOs[i], e.X, e.Y, e.Z, d);
    }

    private static Matrix4x4 Global(int i)
    {
        if (g_done[i]) return g_global[i];
        Matrix4x4 m = g_local[i];
        int p = g.Nodes[i].ParentIndex;
        if (p >= 0 && p < g.Nodes.Count && p != i) m = Matrix4x4.Multiply(m, Global(p));
        g_global[i] = m;
        g_done[i] = true;
        return m;
    }

    private static int Main(string[] args)
    {
        if (args.Length < 3)
        {
            Console.WriteLine("usage: FlverDeforme.exe <entree.flver> <pose.tsv> <sortie.flver>");
            return 2;
        }

        g = FLVER2.Read(args[0]);
        int n = g.Nodes.Count;
        g_local = new Matrix4x4[n];
        g_global = new Matrix4x4[n];
        g_done = new bool[n];
        for (int i = 0; i < n; i++) g_local[i] = g.Nodes[i].ComputeLocalTransform();
        for (int i = 0; i < n; i++) Global(i);

        // --- lecture de la pose ---
        var pose = new Dictionary<string, Matrix4x4>();
        foreach (string ligne in File.ReadAllLines(args[1]))
        {
            if (ligne.Length == 0) continue;
            string[] c = ligne.Split('\t');
            if (c.Length < 17) continue;
            float[] v = new float[16];
            for (int k = 0; k < 16; k++) v[k] = float.Parse(c[1 + k], Inv);
            pose[c[0]] = new Matrix4x4(
                v[0], v[1], v[2], v[3],
                v[4], v[5], v[6], v[7],
                v[8], v[9], v[10], v[11],
                v[12], v[13], v[14], v[15]);
        }
        Console.WriteLine("modele      : " + args[0]);
        Console.WriteLine("os du modele: " + n + "   os poses : " + pose.Count);

        // --- transformation propre a chaque os : bind^-1 * pose ---
        var delta = new Matrix4x4[n];
        int avecPose = 0, sansPose = 0;
        for (int i = 0; i < n; i++)
        {
            Matrix4x4 a;
            if (pose.TryGetValue(g.Nodes[i].Name, out a)) avecPose++;
            else { a = g_global[i]; sansPose++; }
            Matrix4x4 invB;
            if (!Matrix4x4.Invert(g_global[i], out invB)) invB = Matrix4x4.Identity;
            delta[i] = Matrix4x4.Multiply(invB, a);
        }
        Console.WriteLine("os avec pose explicite : " + avecPose + "   sans (repos) : " + sansPose);
        Console.WriteLine();

        // --- deformation ---
        double[] seuils = { 0.05, 0.1, 0.5, 1.0, 5.0 };
        int[] depasses = new int[seuils.Length];
        double deplMaxGlobale = 0; int meshMaxGlobale = -1, vertMaxGlobale = -1;
        double ecartNormalisation = 0;
        double sommeMinGlobale = double.MaxValue, sommeMaxGlobale = double.MinValue;
        Vector3 loGlobale = new Vector3(float.MaxValue), hiGlobale = new Vector3(float.MinValue);

        // Bilan par os : pour chaque os, le plus grand deplacement subi par les
        // sommets dont cet os est le poids dominant. C'est le diagnostic qui
        // designe directement un os mal assigne.
        deplParOs = new double[n];
        compteParOs = new int[n];
        miniParOs = new Vector3[n];
        maxiParOs = new Vector3[n];
        for (int i = 0; i < n; i++)
        {
            miniParOs[i] = new Vector3(float.MaxValue);
            maxiParOs[i] = new Vector3(float.MinValue);
        }

        Console.WriteLine("=== deformation, maillage par maillage ===");
        for (int mi = 0; mi < g.Meshes.Count; mi++)
        {
            FLVER2.Mesh mesh = g.Meshes[mi];
            double maxMesh = 0;
            int vertMaxMesh = -1;
            double sommeMin = double.MaxValue, sommeMax = double.MinValue;
            double sommeDepl = 0;
            int nbDepasses = 0;

            for (int vi = 0; vi < mesh.Vertices.Count; vi++)
            {
                FLVER.Vertex v = mesh.Vertices[vi];
                Vector3 p = Vector3.Zero;
                float somme = 0f;
                int dominant = -1;
                float poidMax = 0f;
                for (int b = 0; b < 4; b++)
                {
                    float w = v.BoneWeights[b];
                    if (w <= 0f) continue;
                    int bi = v.BoneIndices[b];
                    if (bi < 0 || bi >= n) continue;
                    p += w * Vector3.Transform(v.Position, delta[bi]);
                    somme += w;
                    if (w > poidMax) { poidMax = w; dominant = bi; }
                }
                if (somme <= 0f) { p = v.Position; somme = 1f; }

                double d = (p - v.Position).Length();
                if (dominant >= 0)
                {
                    compteParOs[dominant]++;
                    if (d > deplParOs[dominant]) deplParOs[dominant] = d;
                    miniParOs[dominant] = Vector3.Min(miniParOs[dominant], v.Position);
                    maxiParOs[dominant] = Vector3.Max(maxiParOs[dominant], v.Position);
                }
                double dn = (p / somme - v.Position).Length();
                ecartNormalisation = Math.Max(ecartNormalisation, Math.Abs(dn - d));
                sommeMin = Math.Min(sommeMin, somme);
                sommeMax = Math.Max(sommeMax, somme);
                sommeDepl += d;
                if (d > maxMesh) { maxMesh = d; vertMaxMesh = vi; }
                if (d > 0.1) nbDepasses++;
                for (int s = 0; s < seuils.Length; s++) if (d > seuils[s]) depasses[s]++;

                v.Position = p;
            }

            Vector3 lo = new Vector3(float.MaxValue), hi = new Vector3(float.MinValue);
            foreach (FLVER.Vertex v in mesh.Vertices)
            {
                lo = Vector3.Min(lo, v.Position);
                hi = Vector3.Max(hi, v.Position);
            }
            mesh.BoundingBox = new FLVER2.Mesh.BoundingBoxes();
            mesh.BoundingBox.Min = lo;
            mesh.BoundingBox.Max = hi;
            mesh.BoundingBox.Unk = Vector3.Zero;
            loGlobale = Vector3.Min(loGlobale, lo);
            hiGlobale = Vector3.Max(hiGlobale, hi);

            if (maxMesh > deplMaxGlobale)
            {
                deplMaxGlobale = maxMesh; meshMaxGlobale = mi; vertMaxGlobale = vertMaxMesh;
            }
            sommeMinGlobale = Math.Min(sommeMinGlobale, sommeMin);
            sommeMaxGlobale = Math.Max(sommeMaxGlobale, sommeMax);

            Vector3 bb = hi - lo;
            Console.WriteLine(string.Format(Inv,
                "  [{0,2}] {1,-22} sommets {2,7}   deplacement max {3,9:0.####} m  moyen {4,8:0.####}   >10 cm : {5,6}   somme des poids {6:0.####}..{7:0.####}   bbox ({8:0.##} {9:0.##} {10:0.##})",
                mi, mesh.MaterialIndex, mesh.Vertices.Count, maxMesh,
                sommeDepl / Math.Max(1, mesh.Vertices.Count), nbDepasses,
                sommeMin, sommeMax, bb.X, bb.Y, bb.Z));
        }

        Console.WriteLine();
        Console.WriteLine("=== bilan ===");
        Console.WriteLine("somme des poids : min " + sommeMinGlobale.ToString("0.####", Inv)
            + "   max " + sommeMaxGlobale.ToString("0.####", Inv)
            + "   (1 = melange exact ; autre = le moteur etirait le sommet)");
        Console.WriteLine("ecart max entre somme brute et somme normalisee : " + ecartNormalisation.ToString("0.######", Inv));
        Console.WriteLine("deplacement max : " + deplMaxGlobale.ToString("0.####", Inv)
            + " m   (maillage " + meshMaxGlobale + ", sommet " + vertMaxGlobale + ")");
        for (int s = 0; s < seuils.Length; s++)
            Console.WriteLine("  sommets deplaces de plus de " + seuils[s].ToString("0.##", Inv) + " m : " + depasses[s]);

        Console.WriteLine();
        Console.WriteLine("=== os classes par deplacement maximal des sommets qui leur sont attaches ===");
        List<int> ordre = new List<int>();
        for (int i = 0; i < n; i++) if (compteParOs[i] > 0) ordre.Add(i);
        ordre.Sort(delegate(int a, int b) { return deplParOs[b].CompareTo(deplParOs[a]); });
        int montres = 0;
        foreach (int i in ordre)
        {
            if (montres++ >= 15) break;
            Console.WriteLine("- " + LigneOs(i));
        }

        Console.WriteLine();
        Console.WriteLine("=== os classes par emprise du nuage de sommets attaches (un os dont les sommets sont etales est suspect) ===");
        List<int> ordre2 = new List<int>();
        for (int i = 0; i < n; i++) if (compteParOs[i] > 0) ordre2.Add(i);
        ordre2.Sort(delegate(int a, int b) { return Etendue(b).CompareTo(Etendue(a)); });
        montres = 0;
        foreach (int i in ordre2)
        {
            if (montres++ >= 15) break;
            Console.WriteLine("- " + LigneOs(i));
        }

        Console.WriteLine();
        Console.WriteLine(string.Format(Inv, "etendue deformee : min ({0:0.###} {1:0.###} {2:0.###})  max ({3:0.###} {4:0.###} {5:0.###})",
            loGlobale.X, loGlobale.Y, loGlobale.Z, hiGlobale.X, hiGlobale.Y, hiGlobale.Z));
        g.Header.BoundingBoxMin = loGlobale;
        g.Header.BoundingBoxMax = hiGlobale;
        Console.WriteLine("ecriture : " + args[2]);
        g.Write(args[2]);
        return 0;
    }
}
