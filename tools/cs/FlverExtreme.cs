// FlverExtreme.exe -- sommets les plus eloignes sur un axe, avec leurs os.
//
// Sert a identifier les "pointes" : quelques sommets projetes loin du corps par
// un poids sur un os lointain. On trie les sommets d'un maillage par position
// sur un axe et on affiche les N extremes avec leurs indices d'os et poids.
//
// Usage : FlverExtreme.exe <fichier.flver> <maillage> <axe x|y|z> <n> [min|max]
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Numerics;
using SoulsFormats;

internal static class FlverExtreme
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 4)
        {
            Console.WriteLine("usage: FlverExtreme.exe <fichier.flver> <maillage> <axe x|y|z> <n> [min|max]");
            return 2;
        }
        FLVER2 f = FLVER2.Read(args[0]);
        int mi = int.Parse(args[1], Inv);
        string nomAxe = args[2].ToLowerInvariant();
        int axe = nomAxe == "y" ? 1 : (nomAxe == "z" ? 2 : 0);
        int n = int.Parse(args[3], Inv);
        bool max = args.Length < 5 || args[4] != "min";

        FLVER2.Mesh m = f.Meshes[mi];
        var liste = new List<FLVER.Vertex>(m.Vertices);
        liste.Sort((a, b) =>
        {
            float va = Composante(a.Position, axe);
            float vb = Composante(b.Position, axe);
            return max ? vb.CompareTo(va) : va.CompareTo(vb);
        });

        Console.WriteLine("fichier : " + args[0] + "   maillage " + mi
                          + "   materiau " + m.MaterialIndex + "   sommets " + m.Vertices.Count);
        for (int i = 0; i < Math.Min(n, liste.Count); i++)
        {
            FLVER.Vertex v = liste[i];
            string os = "";
            for (int k = 0; k < 4; k++)
            {
                if (v.BoneWeights[k] <= 0.001f) continue;
                int b = v.BoneIndices[k];
                string nom = (b >= 0 && b < f.Nodes.Count) ? f.Nodes[b].Name : "?";
                os += string.Format(Inv, "{0}:{1}={2:0.###}  ", b, nom, v.BoneWeights[k]);
            }
            Console.WriteLine(string.Format(Inv, "  {0,2}  pos ({1:0.0000} {2:0.0000} {3:0.0000})  os {4}",
                i, v.Position.X, v.Position.Y, v.Position.Z, os));
        }
        return 0;
    }

    private static float Composante(Vector3 v, int axe)
    {
        return axe == 0 ? v.X : (axe == 1 ? v.Y : v.Z);
    }
}
