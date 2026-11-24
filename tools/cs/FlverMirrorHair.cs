// FlverMirrorHair.exe -- duplique les sommets de cheveux (arriere, z<0, y>2.0)
// vers l'avant (z>0) pour rendre les cheveux visibles de face.
using System;
using System.Collections.Generic;
using System.Numerics;
using SoulsFormats;

internal static class FlverMirrorHair
{
    private static int Main(string[] args)
    {
        FLVER2 f = FLVER2.Read(args[0]);
        FLVER2.Mesh m = f.Meshes[4]; // head mesh
        int nOrig = m.Vertices.Count;

        var isHair = new bool[nOrig];
        int hairCount = 0;
        for (int i = 0; i < nOrig; i++)
        {
            FLVER.Vertex v = m.Vertices[i];
            if (v.Position.Z < -0.05f && v.Position.Y > 2.0f)
            {
                isHair[i] = true;
                hairCount++;
            }
        }
        Console.WriteLine("cheveux arriere : " + hairCount + " sommets");

        var mirrorMap = new Dictionary<int, int>();
        for (int i = 0; i < nOrig; i++)
        {
            if (!isHair[i]) continue;
            FLVER.Vertex orig = m.Vertices[i];
            FLVER.Vertex nv = new FLVER.Vertex(0, 0, 0); // layout placeholder
            // copy via fields
            nv.Position = new Vector3(orig.Position.X, orig.Position.Y, -orig.Position.Z);
            nv.Normal = new Vector3(orig.Normal.X, orig.Normal.Y, -orig.Normal.Z);
            nv.NormalW = orig.NormalW;
            nv.BoneIndices = new FLVER.VertexBoneIndices();
            nv.BoneIndices[0] = orig.BoneIndices[0];
            nv.BoneIndices[1] = orig.BoneIndices[1];
            nv.BoneIndices[2] = orig.BoneIndices[2];
            nv.BoneIndices[3] = orig.BoneIndices[3];
            nv.BoneWeights = new FLVER.VertexBoneWeights();
            nv.BoneWeights[0] = orig.BoneWeights[0];
            nv.BoneWeights[1] = orig.BoneWeights[1];
            nv.BoneWeights[2] = orig.BoneWeights[2];
            nv.BoneWeights[3] = orig.BoneWeights[3];
            nv.UVs = new List<System.Numerics.Vector3>();
            foreach (var uv in orig.UVs) nv.UVs.Add(uv);
            nv.Tangents = new List<Vector4>();
            foreach (var t in orig.Tangents) nv.Tangents.Add(new Vector4(t.X, t.Y, -t.Z, t.W));
            nv.Bitangent = new Vector4(orig.Bitangent.X, orig.Bitangent.Y, -orig.Bitangent.Z, orig.Bitangent.W);
            nv.Colors = new List<FLVER.VertexColor>();
            foreach (var c in orig.Colors) nv.Colors.Add(c);
            mirrorMap[i] = m.Vertices.Count;
            m.Vertices.Add(nv);
        }
        Console.WriteLine("sommets totaux : " + m.Vertices.Count);

        foreach (FLVER2.FaceSet fs in m.FaceSets)
        {
            if (fs.TriangleStrip) { Console.WriteLine("strip not supported"); continue; }
            var newIndices = new List<int>(fs.Indices);
            int triCount = fs.Indices.Count / 3;
            for (int t = 0; t < triCount; t++)
            {
                int i0 = fs.Indices[t * 3];
                int i1 = fs.Indices[t * 3 + 1];
                int i2 = fs.Indices[t * 3 + 2];
                if (isHair[i0] && isHair[i1] && isHair[i2])
                {
                    newIndices.Add(mirrorMap[i0]);
                    newIndices.Add(mirrorMap[i2]);
                    newIndices.Add(mirrorMap[i1]);
                }
            }
            fs.Indices = newIndices;
        }
        Console.WriteLine("done");
        f.Write(args[1]);
        return 0;
    }
}
