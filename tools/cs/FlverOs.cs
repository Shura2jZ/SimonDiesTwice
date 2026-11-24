// FlverOs - liste TOUS les os utilises par chaque maillage, avec leur nom et le
// nombre de sommets ponderes. Sert a reperer les sommets accroches a des os
// "mous" (tissu CLM2, fourreau, mousquet, lance, cibles...) que le jeu deplace
// sans le HKX : ces sommets partent en vrille et fabriquent des triangles geants.
//
// Usage : FlverOs.exe modele.flver [motif1 motif2 ...]
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using SoulsFormats;

internal static class FlverOs
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static readonly string[] MOUS = {
        "Wire", "Target", "Skirt", "SpineArmor", "Eyeball", "Storage", "Saya",
        "Katana", "Gun", "Yari", "Spear", "Rope", "cloth", "Cloth", "Adjust",
        "Beard", "Hakama"
    };

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverOs.exe modele.flver [motifs]"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        string[] motifs = args.Length > 1 ? args.Skip(1).ToArray() : MOUS;

        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("os : " + f.Nodes.Count + "   maillages : " + f.Meshes.Count);
        Console.WriteLine();

        var global = new Dictionary<int, int>();
        for (int mi = 0; mi < f.Meshes.Count; mi++)
        {
            FLVER2.Mesh m = f.Meshes[mi];
            var compte = new Dictionary<int, int>();
            foreach (FLVER.Vertex v in m.Vertices)
                for (int b = 0; b < 4; b++)
                    if (v.BoneWeights[b] > 0f)
                    {
                        int bi = v.BoneIndices[b];
                        compte[bi] = (compte.ContainsKey(bi) ? compte[bi] : 0) + 1;
                        global[bi] = (global.ContainsKey(bi) ? global[bi] : 0) + 1;
                    }

            Console.WriteLine("[{0,2}] noeud={1,4} ({2})  materiau={3}  sommets={4}  os distincts={5}",
                mi, m.NodeIndex, f.Nodes[m.NodeIndex].Name, m.MaterialIndex, m.Vertices.Count, compte.Count);
            foreach (var kv in compte.OrderByDescending(k => k.Value))
            {
                string nom = (kv.Key >= 0 && kv.Key < f.Nodes.Count) ? f.Nodes[kv.Key].Name : "?";
                bool mou = motifs.Any(x => nom.IndexOf(x, StringComparison.OrdinalIgnoreCase) >= 0);
                Console.WriteLine("        {0,4} {1,-30} {2,7} sommets{3}",
                    kv.Key, nom, kv.Value, mou ? "   <<< OS MOU/ATTACHE" : "");
            }
        }

        Console.WriteLine();
        Console.WriteLine("=== os mous/attaches utilises par au moins un maillage ===");
        bool trouve = false;
        foreach (var kv in global.OrderByDescending(k => k.Value))
        {
            string nom = (kv.Key >= 0 && kv.Key < f.Nodes.Count) ? f.Nodes[kv.Key].Name : "?";
            if (!motifs.Any(x => nom.IndexOf(x, StringComparison.OrdinalIgnoreCase) >= 0)) continue;
            trouve = true;
            Console.WriteLine("  {0,4} {1,-30} {2,7} sommets", kv.Key, nom, kv.Value);
        }
        if (!trouve) Console.WriteLine("  (aucun)");
        Console.WriteLine();
        Console.WriteLine("os distincts utilises, tous maillages : " + global.Count);
        return 0;
    }
}
