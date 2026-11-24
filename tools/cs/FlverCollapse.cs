// FlverCollapse.exe -- met a zero les sommets d'un maillage qui verifient une
// condition sur leur position (pour supprimer un morceau qui se balade).
//
// Usage : FlverCollapse.exe <entree.flver> <sortie.flver> <maillage> <axe> <seuil> <min|max>
//   ex : FlverCollapse.exe in.flver out.flver 0 x -0.6 min
//        -> sommets du maillage 0 dont x < -0.6 -> position (0,0,0)
using System;
using System.Globalization;
using System.Numerics;
using SoulsFormats;

internal static class FlverCollapse
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    private static int Main(string[] args)
    {
        if (args.Length < 6)
        {
            Console.WriteLine("usage: FlverCollapse.exe <entree.flver> <sortie.flver> <maillage> <axe x|y|z> <seuil> <min|max>");
            return 2;
        }
        FLVER2 f = FLVER2.Read(args[0]);
        int mi = int.Parse(args[2], Inv);
        int axe = args[3] == "x" ? 0 : (args[3] == "y" ? 1 : 2);
        float thr = float.Parse(args[4], Inv);
        bool min = args[5] == "min";
        FLVER2.Mesh m = f.Meshes[mi];
        int n = 0;
        foreach (FLVER.Vertex v in m.Vertices)
        {
            float val = axe == 0 ? v.Position.X : (axe == 1 ? v.Position.Y : v.Position.Z);
            bool hit = min ? val < thr : val > thr;
            if (hit)
            {
                v.Position = new Vector3(0, 0, 0);
                n++;
            }
        }
        f.Write(args[1]);
        Console.WriteLine("maillage {0} : {1} sommets mis a zero (sur {2})", mi, n, m.Vertices.Count);
        return 0;
    }
}
