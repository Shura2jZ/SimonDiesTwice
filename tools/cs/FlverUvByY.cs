using System;
using System.Globalization;
using SoulsFormats;

internal static class FlverUvByY
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    private static int Main(string[] args)
    {
        FLVER2 f = FLVER2.Read(args[0]);
        int mi = int.Parse(args[1], Inv);
        float ymin = float.Parse(args[2], Inv);
        FLVER2.Mesh m = f.Meshes[mi];
        float umin=1,umax=0,vmin=1,vmax=0;
        int n=0;
        foreach (FLVER.Vertex v in m.Vertices)
        {
            if (v.Position.Y < ymin) continue;
            n++;
            if (v.UVs[0].X < umin) umin = v.UVs[0].X;
            if (v.UVs[0].X > umax) umax = v.UVs[0].X;
            if (v.UVs[0].Y < vmin) vmin = v.UVs[0].Y;
            if (v.UVs[0].Y > vmax) vmax = v.UVs[0].Y;
        }
        Console.WriteLine("maillage {0} : {1} sommets avec Y>{2}", mi, n, ymin);
        Console.WriteLine("  U : {0:0.0000} .. {1:0.0000}", umin, umax);
        Console.WriteLine("  V : {0:0.0000} .. {1:0.0000}", vmin, vmax);
        return 0;
    }
}
