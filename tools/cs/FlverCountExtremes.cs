using System;
using System.Globalization;
using SoulsFormats;

internal static class FlverCountExtremes
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    private static int Main(string[] args)
    {
        FLVER2 f = FLVER2.Read(args[0]);
        int mi = int.Parse(args[1], Inv);
        int axe = args[2] == "x" ? 0 : (args[2] == "y" ? 1 : 2);
        float thr = float.Parse(args[3], Inv);
        bool max = args[4] == "max";
        FLVER2.Mesh m = f.Meshes[mi];
        int n = 0;
        foreach (FLVER.Vertex v in m.Vertices)
        {
            float val = axe == 0 ? v.Position.X : (axe == 1 ? v.Position.Y : v.Position.Z);
            if (max ? val > thr : val < thr) n++;
        }
        Console.WriteLine("maillage {0} : {1} sommets dont {2} au-dela du seuil {3} ({4})",
            mi, m.Vertices.Count, n, thr, max ? "max" : "min");
        return 0;
    }
}
