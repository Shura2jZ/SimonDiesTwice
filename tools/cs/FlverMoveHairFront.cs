// FlverMoveHairFront.exe -- deplace les cheveux de l'arriere (z<0, y>2.0) vers l'avant (z=-z)
// et corrige le winding des triangles correspondants.
using System;
using System.Collections.Generic;
using System.Numerics;
using SoulsFormats;

internal static class FlverMoveHairFront
{
    private static int Main(string[] args)
    {
        FLVER2 f = FLVER2.Read(args[0]);
        FLVER2.Mesh m = f.Meshes[4]; // head mesh
        int n = 0;
        // Step 1: identify back-hair vertices and move them
        var isHair = new bool[m.Vertices.Count];
        for (int i = 0; i < m.Vertices.Count; i++)
        {
            FLVER.Vertex v = m.Vertices[i];
            if (v.Position.Z < -0.05f && v.Position.Y > 2.0f)
            {
                isHair[i] = true;
                v.Position = new Vector3(v.Position.X, v.Position.Y, -v.Position.Z);
                v.Normal = new Vector3(v.Normal.X, v.Normal.Y, -v.Normal.Z);
                // flip tangent z too
                if (v.Tangents.Count > 0)
                {
                    var t = v.Tangents[0];
                    v.Tangents[0] = new Vector4(t.X, t.Y, -t.Z, t.W);
                }
                n++;
            }
        }
        Console.WriteLine("cheveux deplaces : " + n);

        // Step 2: flip winding for triangles that are now all front (z>0)
        foreach (FLVER2.FaceSet fs in m.FaceSets)
        {
            if (fs.TriangleStrip) continue;
            int triCount = fs.Indices.Count / 3;
            for (int t = 0; t < triCount; t++)
            {
                int i0 = fs.Indices[t * 3];
                int i1 = fs.Indices[t * 3 + 1];
                int i2 = fs.Indices[t * 3 + 2];
                if (isHair[i0] && isHair[i1] && isHair[i2])
                {
                    // swap 1 and 2 to fix winding
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
