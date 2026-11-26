// FlverAddHair4.exe -- ajoute le cheveux comme 6ème mesh (materiau 5 = fur shader)
// dans le FLVER, sans toucher aux 5 maillages existants. Le CLM2 doit etre
// mis a jour pour avoir 6 elements.
using System;
using System.Collections.Generic;
using System.Numerics;
using SoulsFormats;

internal static class FlverAddHair4
{
    private static int Main(string[] args)
    {
        string src = args[0], dst = args[1];
        FLVER2 f = FLVER2.Read(src);

        int boneHead = 147;
        var newVerts = new List<FLVER.Vertex>();
        var newTris = new List<int>();

        // Dôme de cheveux sur le crâne
        float headY = 2.10f;
        float headR = 0.22f;
        float domeH = 0.16f;
        int rings = 7;
        int segs = 20;

        List<int>[] rings_vert = new List<int>[64];
        for (int i = 0; i < 64; i++) rings_vert[i] = new List<int>();

        List<int> domeTop = new List<int>();
        for (int r = 0; r <= rings; r++)
        {
            float t = (float)r / rings;
            float y = headY + t * domeH;
            float rad = headR * (1.0f - t * 0.45f);
            List<int> ring = new List<int>();
            for (int s = 0; s < segs; s++)
            {
                float a = (float)s / segs * 2.0f * (float)Math.PI;
                float x = (float)Math.Cos(a) * rad;
                float z = (float)Math.Sin(a) * rad;
                int vi = newVerts.Count;
                newVerts.Add(MakeVert(new Vector3(x, y, z), boneHead));
                ring.Add(vi);
            }
            if (r == 0) domeTop.AddRange(ring);
            if (r > 0)
            {
                var prev = rings_vert[r - 1];
                for (int s = 0; s < segs; s++)
                {
                    int s0 = prev[s];
                    int s1 = prev[(s + 1) % segs];
                    int s2 = ring[(s + 1) % segs];
                    int s3 = ring[s];
                    newTris.Add(s0); newTris.Add(s1); newTris.Add(s2);
                    newTris.Add(s0); newTris.Add(s2); newTris.Add(s3);
                }
            }
            rings_vert[r] = ring;
        }

        int apex = newVerts.Count;
        newVerts.Add(MakeVert(new Vector3(0, headY + domeH, 0), boneHead));
        for (int s = 0; s < segs; s++)
        {
            int s0 = domeTop[s];
            int s1 = domeTop[(s + 1) % segs];
            newTris.Add(apex); newTris.Add(s1); newTris.Add(s0);
        }

        // Mèches à l'arrière
        int tailStart = newVerts.Count;
        int tailSegs = 10;
        int tailRings = 5;
        int vertsPerTailRing = tailSegs + 1;
        for (int r = 0; r <= tailRings; r++)
        {
            float t = (float)r / tailRings;
            float y = headY - t * 0.12f;
            float z = headR + t * 0.30f;
            float rad = headR * (1.0f - t * 0.3f);
            for (int s = 0; s <= tailSegs; s++)
            {
                float a = (float)s / tailSegs * (float)Math.PI;
                float x = (float)Math.Cos(a) * rad;
                float zz = (float)Math.Sin(a) * rad * 0.5f + z;
                newVerts.Add(MakeVert(new Vector3(x, y, zz), boneHead));
            }
        }
        for (int r = 0; r < tailRings; r++)
        {
            for (int s = 0; s < tailSegs; s++)
            {
                int i0 = tailStart + r * vertsPerTailRing + s;
                int i1 = tailStart + r * vertsPerTailRing + s + 1;
                int i2 = tailStart + (r + 1) * vertsPerTailRing + s + 1;
                int i3 = tailStart + (r + 1) * vertsPerTailRing + s;
                newTris.Add(i0); newTris.Add(i1); newTris.Add(i2);
                newTris.Add(i0); newTris.Add(i2); newTris.Add(i3);
            }
        }

        // 6ème mesh avec materiau 5 (fur shader)
        var hairMesh = new FLVER2.Mesh
        {
            MaterialIndex = 5,
            NodeIndex = 199,
            Dynamic = 1,
            UseBoneWeights = true,
            BoneIndices = new List<int> { boneHead },
        };
        hairMesh.VertexBuffers = new List<FLVER2.VertexBuffer>();
        hairMesh.VertexBuffers.Add(new FLVER2.VertexBuffer(7));
        foreach (var v in newVerts)
            hairMesh.Vertices.Add(v);
        hairMesh.FaceSets = new List<FLVER2.FaceSet>
        {
            new FLVER2.FaceSet
            {
                Flags = (FLVER2.FaceSet.FSFlags)0,
                TriangleStrip = false,
                CullBackfaces = true,
                Unk06 = 1,
                Indices = newTris
            }
        };
        hairMesh.BoundingBox = new FLVER2.Mesh.BoundingBoxes();

        // bbox
        Vector3 min = new Vector3(float.MaxValue), max = new Vector3(float.MinValue);
        foreach (var v in newVerts)
        {
            min = Vector3.Min(min, v.Position);
            max = Vector3.Max(max, v.Position);
        }
        hairMesh.BoundingBox.Min = min;
        hairMesh.BoundingBox.Max = max;

        f.Meshes.Add(hairMesh);

        Console.WriteLine("nouveaux vertices: " + newVerts.Count);
        Console.WriteLine("nouveaux triangles: " + (newTris.Count / 3));
        Console.WriteLine("total maillages: " + f.Meshes.Count);
        Console.WriteLine("mesh cheveux: materiau 5 (fur), node 199, os 147");

        f.Write(dst);
        Console.WriteLine("ecrit: " + dst);
        return 0;
    }

    static FLVER.Vertex MakeVert(Vector3 pos, int bone)
    {
        var v = new FLVER.Vertex(0, 0, 0);
        v.Position = pos;
        v.Normal = Vector3.UnitY;
        v.NormalW = 0;
        v.Tangents = new List<Vector4> { new Vector4(1, 0, 0, 1) };
        v.BoneIndices = new FLVER.VertexBoneIndices();
        v.BoneIndices[0] = (byte)bone;
        v.BoneIndices[1] = 0;
        v.BoneIndices[2] = 0;
        v.BoneIndices[3] = 0;
        v.BoneWeights = new FLVER.VertexBoneWeights();
        v.BoneWeights[0] = 100;
        v.BoneWeights[1] = 0;
        v.BoneWeights[2] = 0;
        v.BoneWeights[3] = 0;
        v.UVs = new List<Vector3> { new Vector3(0.5f, 0.1f, 0), new Vector3(0.5f, 0.1f, 0) };
        v.Colors = new List<FLVER.VertexColor> { new FLVER.VertexColor(255, 255, 255, 255) };
        return v;
    }
}
