// FlverOsNoms - pour chaque maillage : liste des os distincts utilises par les
// sommets, avec le NOM du noeud correspondant et le poids total.
//
// But : verifier que les index d'os ecrits dans les sommets pointent bien vers
// les os attendus (et pas vers des noeuds de maillage, des dummies, ou un index
// de repli silencieux).
//
// Usage : FlverOsNoms.exe <flver> [emplacements separes par des virgules]
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using SoulsFormats;

internal static class FlverOsNoms
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage: FlverOsNoms.exe <flver> [emplacements]");
            return 2;
        }

        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("  noeuds : " + f.Nodes.Count);

        PropertyInfo pi = typeof(FLVER2).GetProperty("Bones");
        if (pi == null)
        {
            Console.WriteLine("  propriete 'Bones' : absente de ce SoulsFormats");
        }
        else
        {
            ICollection c = pi.GetValue(f, null) as ICollection;
            Console.WriteLine("  propriete 'Bones' : presente, " + (c == null ? -1 : c.Count) + " elements");
        }

        List<int> slots = new List<int>();
        if (args.Length > 1)
        {
            foreach (string s in args[1].Split(',')) slots.Add(int.Parse(s, Inv));
        }
        else
        {
            for (int i = 0; i < f.Meshes.Count; i++) slots.Add(i);
        }

        foreach (int i in slots)
        {
            FLVER2.Mesh m = f.Meshes[i];
            Dictionary<int, double> poids = new Dictionary<int, double>();
            foreach (FLVER.Vertex v in m.Vertices)
            {
                for (int k = 0; k < 4; k++)
                {
                    if (v.BoneWeights[k] > 0f && v.BoneIndices[k] != 0)
                    {
                        double cur;
                        poids.TryGetValue(v.BoneIndices[k], out cur);
                        poids[v.BoneIndices[k]] = cur + v.BoneWeights[k];
                    }
                }
            }

            Console.WriteLine();
            Console.WriteLine(string.Format(Inv, "emplacement {0} : {1} sommets, {2} os distincts",
                i, m.Vertices.Count, poids.Count));

            foreach (KeyValuePair<int, double> kv in poids)
            {
                string nom;
                if (kv.Key >= 0 && kv.Key < f.Nodes.Count) { nom = f.Nodes[kv.Key].Name; }
                else { nom = "!! HORS BORNES !!"; }
                Console.WriteLine(string.Format(Inv, "    os {0,4} -> {1,-28} poids cumule {2,9:F1}",
                    kv.Key, nom, kv.Value));
            }
        }

        return 0;
    }
}
