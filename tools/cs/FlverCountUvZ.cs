using System;
using System.Globalization;
using SoulsFormats;

internal static class FlverCountUvZ
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    private static int Main(string[] args)
    {
        FLVER2 f = FLVER2.Read(args[0]);
        int mi = int.Parse(args[1], Inv);
        float zmin = float.Parse(args[2], Inv);
        float vmax = float.Parse(args[3], Inv);
        FLVER2.Mesh m = f.Meshes[mi];
        int total=0, hair=0, face=0;
        foreach (FLVER.Vertex v in m.Vertices)
        {
            if (v.Position.Z < zmin) continue;
            total++;
            if (v.UVs[0].Y < vmax) hair++;
            else face++;
        }
        Console.WriteLine("maillage {0}: {1} sommets avec Z>{2}", mi, total, zmin);
        Console.WriteLine("  V<{0} (cheveux) : {1}", vmax, hair);
        Console.WriteLine("  V>={0} (visage) : {1}", vmax, face);
        return 0;
    }
}
