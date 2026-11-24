// FlverFs6 - pour chaque maillage : drapeaux, unk06 et taille de chaque faceset,
// plus le nombre d'os distincts reellement utilises par les sommets.
//
// But : verifier que CHAQUE faceset (et pas seulement le premier) declare la
// taille de palette d'os attendue par le moteur. Un faceset laisse sur une
// valeur perimee ferait exploser le skinning ("geometrie geante").
//
// Usage : FlverFs6.exe <modele.flver>
using System;
using System.Collections.Generic;
using System.Globalization;
using SoulsFormats;

internal static class FlverFs6
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage: FlverFs6.exe <modele.flver>");
            return 2;
        }

        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("  idx | mat | node | sommets | osDistincts | facesets [drapeaux u6=nbIndices]");

        for (int i = 0; i < f.Meshes.Count; i++)
        {
            FLVER2.Mesh m = f.Meshes[i];

            HashSet<int> os = new HashSet<int>();
            foreach (FLVER.Vertex v in m.Vertices)
            {
                for (int k = 0; k < 4; k++)
                {
                    if (v.BoneWeights[k] > 0f && v.BoneIndices[k] != 0)
                    {
                        os.Add(v.BoneIndices[k]);
                    }
                }
            }

            string fsDesc = "";
            foreach (FLVER2.FaceSet fs in m.FaceSets)
            {
                fsDesc += string.Format(Inv, "[0x{0:X8} u6={1} n={2}] ",
                    (uint)fs.Flags, fs.Unk06, fs.Indices.Count);
            }

            Console.WriteLine(string.Format(Inv,
                "  {0,3} | {1,3} | {2,4} | {3,7} | {4,11} | {5}",
                i, m.MaterialIndex, m.NodeIndex, m.Vertices.Count, os.Count, fsDesc));
        }

        return 0;
    }
}
