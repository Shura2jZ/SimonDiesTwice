// FlverMeshBones - pour un maillage donne, regroupe les sommets par os
// dominant et affiche la boite englobante de chaque groupe. Sert a voir quel
// os tire une partie du maillage trop loin (tete etiree, cheveux, etc.).
//
// Usage : FlverMeshBones.exe <flver> <emplacement> [seuil]
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Numerics;
using SoulsFormats;

internal static class FlverMeshBones
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("usage: FlverMeshBones.exe <flver> <emplacement> [seuil]");
            return 2;
        }
        float seuil = args.Length > 2 ? float.Parse(args[2], Inv) : 0.5f;
        FLVER2 f = FLVER2.Read(args[0]);
        int slot = int.Parse(args[1], Inv);
        FLVER2.Mesh m = f.Meshes[slot];
        Console.WriteLine("fichier : " + args[0] + "   maillage " + slot + "   sommets " + m.Vertices.Count);

        var groupes = new Dictionary<int, List<FLVER.Vertex>>();
        var tous = new Dictionary<int, List<FLVER.Vertex>>();
        foreach (FLVER.Vertex v in m.Vertices)
        {
            int best = -1;
            float bw = -1f;
            for (int k = 0; k < 4; k++)
            {
                float w = v.BoneWeights[k];
                int bi = v.BoneIndices[k];
                if (w <= 0f) continue;
                if (!tous.ContainsKey(bi)) tous[bi] = new List<FLVER.Vertex>();
                tous[bi].Add(v);
                if (w > bw) { bw = w; best = bi; }
            }
            if (best >= 0)
            {
                if (!groupes.ContainsKey(best)) groupes[best] = new List<FLVER.Vertex>();
                groupes[best].Add(v);
            }
        }

        Console.WriteLine();
        Console.WriteLine("=== tous les sommets ponderes (poids > 0) ===");
        foreach (var kv in tous.OrderByDescending(k => k.Value.Count))
        {
            Console.WriteLine(string.Format(Inv, "os {0,3} {1,-22} {2,6} sommets   y {3,8:F4} .. {4,8:F4}",
                kv.Key, Nom(f, kv.Key), kv.Value.Count,
                kv.Value.Min(v => v.Position.Y), kv.Value.Max(v => v.Position.Y)));
        }

        Console.WriteLine();
        Console.WriteLine("=== groupes par os DOMINANT (poids >= " + seuil.ToString(Inv) + ") ===");
        foreach (var kv in groupes.OrderByDescending(k => k.Value.Count))
        {
            var vs = kv.Value;
            Console.WriteLine(string.Format(Inv,
                "os {0,3} {1,-22} {2,6} sommets   y {3,8:F4} .. {4,8:F4}   x {5,7:F3} .. {6,7:F3}   z {7,7:F3} .. {8,7:F3}",
                kv.Key, Nom(f, kv.Key), vs.Count,
                vs.Min(v => v.Position.Y), vs.Max(v => v.Position.Y),
                vs.Min(v => v.Position.X), vs.Max(v => v.Position.X),
                vs.Min(v => v.Position.Z), vs.Max(v => v.Position.Z)));
        }
        return 0;
    }

    private static string Nom(FLVER2 f, int i)
    {
        if (i >= 0 && i < f.Nodes.Count) return f.Nodes[i].Name;
        return "?";
    }
}
