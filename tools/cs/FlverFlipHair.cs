// FlverFlipHair.exe -- deplace les sommets de cheveux (arriere, z<0, y>2.0)
// vers l'avant (z=-z) pour rendre les cheveux visibles de face.
using System;
using System.Globalization;
using System.Numerics;
using SoulsFormats;

internal static class FlverFlipHair
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    private static int Main(string[] args)
    {
        FLVER2 f = FLVER2.Read(args[0]);
        FLVER2.Mesh m = f.Meshes[4]; // head mesh
        int n = 0;
        foreach (FLVER.Vertex v in m.Vertices)
        {
            if (v.Position.Z < -0.05f && v.Position.Y > 2.0f)
            {
                v.Position = new Vector3(v.Position.X, v.Position.Y, -v.Position.Z);
                v.Normal = new Vector3(v.Normal.X, v.Normal.Y, -v.Normal.Z);
                n++;
            }
        }
        Console.WriteLine("cheveux deplaces : " + n + " sommets");
        f.Write(args[1]);
        return 0;
    }
}
