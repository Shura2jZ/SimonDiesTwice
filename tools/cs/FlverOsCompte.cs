// FlverOsCompte - pour chaque maillage, plusieurs facons de compter les os
// utilises par les sommets, a confronter a unk06 du premier faceset.
//
// But : determiner la regle exacte du format (le nombre d'os distincts que le
// moteur attend dans unk06).
//
// Usage : FlverOsCompte.exe <modele.flver>
using System;
using System.Collections.Generic;
using System.Globalization;
using SoulsFormats;

internal static class FlverOsCompte
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage: FlverOsCompte.exe <modele.flver>");
            return 2;
        }

        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("  idx | unk06 | c1 poids>0 | c2 poids>0 +0 | c3 idx!=0 | c4 tout | minOs | maxOs | ecart c3");
        int n = 0;
        foreach (FLVER2.Mesh m in f.Meshes)
        {
            HashSet<int> c1 = new HashSet<int>();
            HashSet<int> c2 = new HashSet<int>();
            HashSet<int> c3 = new HashSet<int>();
            HashSet<int> c4 = new HashSet<int>();
            int minOs = int.MaxValue, maxOs = int.MinValue;
            foreach (FLVER.Vertex v in m.Vertices)
            {
                for (int b = 0; b < 4; b++)
                {
                    int bi = v.BoneIndices[b];
                    float w = v.BoneWeights[b];
                    c4.Add(bi);
                    if (bi != 0) c3.Add(bi);
                    if (w > 0f)
                    {
                        c2.Add(bi);
                        if (bi != 0) c1.Add(bi);
                        if (bi < minOs) minOs = bi;
                        if (bi > maxOs) maxOs = bi;
                    }
                }
            }
            if (minOs == int.MaxValue) { minOs = -1; maxOs = -1; }
            int unk = m.FaceSets.Count > 0 ? m.FaceSets[0].Unk06 : -1;
            Console.WriteLine(string.Format(Inv,
                "  {0,3} | {1,5} | {2,10} | {3,12} | {4,8} | {5,7} | {6,5} | {7,5} | {8,5}",
                n, unk, c1.Count, c2.Count, c3.Count, c4.Count, minOs, maxOs, c3.Count - unk));
            n++;
        }
        return 0;
    }
}
