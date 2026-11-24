// FlverPalette - pour chaque maillage d'un FLVER, affiche la palette d'os
// (Mesh.BoneIndices) et les indices d'os reellement utilises par les sommets.
//
// En question : les indices d'os des sommets sont-ils des indices GLOBAUX de
// noeuds, ou des indices dans la palette du maillage ? Si la palette du
// maillage d'origine est peuplee et que l'injecteur l'a laissee vide, le moteur
// lit hors bornes et dessine n'importe quoi.
//
// Usage : FlverPalette.exe <modele.flver> [maxLignes]
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using SoulsFormats;

internal static class FlverPalette
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage: FlverPalette.exe <modele.flver> [maxLignes]");
            return 2;
        }
        int maxLignes = args.Length > 1 ? int.Parse(args[1], Inv) : 40;

        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("maillages : " + f.Meshes.Count + "   noeuds : " + f.Nodes.Count);
        Console.WriteLine();

        Console.WriteLine("  [i] mat  noeud  osPoids  dyn  palette  minOs  maxOs  osDistincts  premiers indices de palette");
        int n = 0;
        foreach (FLVER2.Mesh m in f.Meshes)
        {
            if (n++ >= maxLignes) { Console.WriteLine("  ... (" + (f.Meshes.Count - maxLignes) + " maillages de plus)"); break; }

            int minOs = int.MaxValue, maxOs = int.MinValue;
            HashSet<int> distincts = new HashSet<int>();
            foreach (FLVER.Vertex v in m.Vertices)
            {
                for (int b = 0; b < 4; b++)
                {
                    float w = v.BoneWeights[b];
                    if (w <= 0f) continue;
                    int bi = v.BoneIndices[b];
                    if (bi < minOs) minOs = bi;
                    if (bi > maxOs) maxOs = bi;
                    distincts.Add(bi);
                }
            }
            if (minOs == int.MaxValue) { minOs = -1; maxOs = -1; }

            string tete = "";
            int k = 0;
            foreach (int bidx in m.BoneIndices)
            {
                if (k >= 8) { tete += " ..."; break; }
                tete += " " + bidx;
                k++;
            }
            if (m.BoneIndices.Count == 0) tete = " (vide)";

            Console.WriteLine(string.Format(Inv,
                "  [{0,2}] {1,3}  {2,5}  {3,7}  {4,3}  {5,7}  {6,5}  {7,5}  {8,11}  {9}",
                n - 1, m.MaterialIndex, m.NodeIndex, m.UseBoneWeights ? "oui" : "non",
                m.Dynamic, m.BoneIndices.Count, minOs, maxOs, distincts.Count, tete));

            if (args.Length > 2 && args[2] == "--os")
            {
                List<int> tries = new List<int>(distincts);
                tries.Sort();
                System.Text.StringBuilder sb = new System.Text.StringBuilder();
                foreach (int bi in tries)
                {
                    string nom = (bi >= 0 && bi < f.Nodes.Count) ? f.Nodes[bi].Name : "?";
                    sb.Append(bi).Append('=').Append(nom).Append("  ");
                }
                Console.WriteLine("        os : " + sb.ToString());
            }
        }

        if (args.Length > 2 && args[2] == "--compte")
        {
            Dictionary<int, int> compte = new Dictionary<int, int>();
            foreach (FLVER2.Mesh m in f.Meshes)
            {
                foreach (FLVER.Vertex v in m.Vertices)
                {
                    int dom = -1;
                    float pm = 0f;
                    for (int b = 0; b < 4; b++)
                    {
                        float w = v.BoneWeights[b];
                        if (w > pm) { pm = w; dom = v.BoneIndices[b]; }
                    }
                    if (dom >= 0)
                    {
                        if (!compte.ContainsKey(dom)) compte[dom] = 0;
                        compte[dom]++;
                    }
                }
            }
            List<int> tries = new List<int>(compte.Keys);
            tries.Sort();
            string chemin = args.Length > 3 ? args[3] : "_work/os_du_modele.tsv";
            using (StreamWriter w = new StreamWriter(chemin))
            {
                foreach (int i in tries)
                    w.WriteLine(f.Nodes[i].Name + "\t" + compte[i]);
            }
            Console.WriteLine();
            Console.WriteLine("table os/sommets ecrite : " + chemin + "   (" + tries.Count + " os)");
        }
        return 0;    }
}
