// FlverFlipWinding.exe -- pour les triangles dont les 3 sommets ont z>0 (cheveux flips),
// inverse l'ordre des indices (1<->2) pour corriger le culling.
using System;
using System.Collections.Generic;
using SoulsFormats;

internal static class FlverFlipWinding
{
    private static int Main(string[] args)
    {
        FLVER2 f = FLVER2.Read(args[0]);
        FLVER2.Mesh m = f.Meshes[4];
        foreach (FLVER2.FaceSet fs in m.FaceSets)
        {
            if (fs.TriangleStrip) continue;
            int triCount = fs.Indices.Count / 3;
            for (int t = 0; t < triCount; t++)
            {
                int i0 = fs.Indices[t * 3];
                int i1 = fs.Indices[t * 3 + 1];
                int i2 = fs.Indices[t * 3 + 2];
                // Only flip triangles where all vertices have z > 0 (flipped hair)
                if (m.Vertices[i0].Position.Z > 0 && m.Vertices[i1].Position.Z > 0 && m.Vertices[i2].Position.Z > 0)
                {
                    fs.Indices[t * 3 + 1] = i2;
                    fs.Indices[t * 3 + 2] = i1;
                }
            }
        }
        f.Write(args[1]);
        Console.WriteLine("done");
        return 0;
    }
}
