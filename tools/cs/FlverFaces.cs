// FlverFaces.exe -- detaille les facesets d'un FLVER.
//
// Question a trancher : les 6 facesets d'un maillage sont-ils
//   - six PASSES de rendu sur les memes triangles (meme liste d'indices), ou
//   - six TRONCONS distincts qui se partagent les triangles ?
//
// Si ce sont des troncons et que notre injecteur met la liste complete dans les
// six, le maillage est dessine six fois : surcout, et surtout toute logique du
// moteur qui suppose que les troncons se recouvrent exactement devient fausse.
//
// Usage : FlverFaces.exe <fichier.flver> [premier] [combien]

using System;
using System.Collections.Generic;
using System.Reflection;
using SoulsFormats;

internal static class FlverFaces
{
    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverFaces.exe <fichier.flver> [premier] [combien]"); return 2; }
        int premier = args.Length > 1 ? int.Parse(args[1]) : 0;
        int combien = args.Length > 2 ? int.Parse(args[2]) : 4;

        Console.WriteLine("=== valeurs de l'enumeration FSFlags ===");
        Type t = typeof(FLVER2.FaceSet).GetNestedType("FSFlags");
        if (t != null) foreach (string n in Enum.GetNames(t))
            Console.WriteLine("    " + n + " = " + Convert.ToInt64(Enum.Parse(t, n)));
        Console.WriteLine();

        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0] + "   maillages : " + f.Meshes.Count);
        for (int i = premier; i < Math.Min(f.Meshes.Count, premier + combien); i++)
        {
            FLVER2.Mesh m = f.Meshes[i];
            Console.WriteLine("[" + i + "] mat " + m.MaterialIndex + "  noeud " + m.NodeIndex
                              + "  sommets " + m.Vertices.Count);
            int k = 0;
            foreach (FLVER2.FaceSet fs in m.FaceSets)
            {
                int lo = int.MaxValue, hi = -1;
                foreach (int x in fs.Indices)
                {
                    if (x < lo) lo = x;
                    if (x > hi) hi = x;
                }
                Console.WriteLine("      faceset " + k + " : drapeaux " + fs.Flags + " (" + Convert.ToInt64(fs.Flags) + ")"
                                  + "  bande " + fs.TriangleStrip
                                  + "  cull " + fs.CullBackfaces
                                  + "  unk06 " + fs.Unk06
                                  + "  indices " + fs.Indices.Count
                                  + " (" + (fs.Indices.Count / 3) + " triangles)"
                                  + "  min " + (hi < 0 ? 0 : lo) + " max " + (hi < 0 ? 0 : hi));
                k++;
            }
        }
        return 0;
    }
}
