// FlverToObj.exe -- convertit un FLVER en OBJ pour rendu Blender.
// Usage : FlverToObj.exe <entree.flver> <sortie.obj>
using System;
using System.Collections.Generic;
using System.IO;
using System.Numerics;
using SoulsFormats;

internal static class FlverToObj
{
    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("usage : FlverToObj.exe <entree.flver> <sortie.obj>");
            return 2;
        }

        FLVER2 f = FLVER2.Read(args[0]);
        var sb = new System.Text.StringBuilder();
        sb.Append("# FLVER to OBJ conversion\n");
        sb.Append("# maillages: ").Append(f.Meshes.Count).Append("\n");

        int vOffset = 1;
        for (int mi = 0; mi < f.Meshes.Count; mi++)
        {
            var m = f.Meshes[mi];
            string matName = m.MaterialIndex < f.Materials.Count ? f.Materials[m.MaterialIndex].Name : "mat" + m.MaterialIndex;
            sb.Append("o mesh").Append(mi).Append("\n");
            sb.Append("usemtl ").Append(matName).Append("\n");

            // Vertices
            foreach (var v in m.Vertices)
            {
                sb.Append("v ").Append(v.Position.X.ToString("R")).Append(" ").Append(v.Position.Y.ToString("R")).Append(" ").Append(v.Position.Z.ToString("R")).Append("\n");
                sb.Append("vn ").Append(v.Normal.X.ToString("R")).Append(" ").Append(v.Normal.Y.ToString("R")).Append(" ").Append(v.Normal.Z.ToString("R")).Append("\n");
                if (v.UVs.Count > 0)
                {
                    var uv = v.UVs[0];
                    sb.Append("vt ").Append(uv.X.ToString("R")).Append(" ").Append(uv.Y.ToString("R")).Append("\n");
                }
            }

            // Faces
            foreach (var fs in m.FaceSets)
            {
                var idx = fs.Indices;
                for (int i = 0; i + 2 < idx.Count; i += 3)
                {
                    int a = idx[i] + vOffset;
                    int b = idx[i + 1] + vOffset;
                    int c = idx[i + 2] + vOffset;
                    // OBJ face: v/vt/vn
                    sb.Append("f ").Append(a).Append("/").Append(a).Append("/").Append(a)
                      .Append(" ").Append(b).Append("/").Append(b).Append("/").Append(b)
                      .Append(" ").Append(c).Append("/").Append(c).Append("/").Append(c).Append("\n");
                }
            }

            vOffset += m.Vertices.Count;
        }

        File.WriteAllText(args[1], sb.ToString());
        Console.WriteLine("ecrit: " + args[1] + " (" + vOffset + " vertices total)");
        return 0;
    }
}
