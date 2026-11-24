using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Numerics;
using SoulsFormats;

internal static class FlverWeaponLocal
{
    static Matrix4x4[] world;
    static Matrix4x4 Global(FLVER2 f, int i, bool[] done)
    {
        if (done[i]) return world[i];
        Matrix4x4 m = f.Nodes[i].ComputeLocalTransform();
        int p = f.Nodes[i].ParentIndex;
        if (p >= 0 && p < f.Nodes.Count && p != i) m = Matrix4x4.Multiply(m, Global(f, p, done));
        done[i] = true;
        return world[i] = m;
    }
    static void Main(string[] args)
    {
        var f = FLVER2.Read(args[0]);
        world = new Matrix4x4[f.Nodes.Count]; var done = new bool[f.Nodes.Count];
        for (int i = 0; i < f.Nodes.Count; i++) Global(f, i, done);
        int bone = Array.FindIndex(f.Nodes.ToArray(), n => n.Name == "R_Katana");
        Matrix4x4 inv; if (bone < 0 || !Matrix4x4.Invert(world[bone], out inv)) throw new Exception("R_Katana non invertible");
        var ci = CultureInfo.InvariantCulture;
        foreach (string ss in args[1].Split(','))
        {
            int slot = int.Parse(ss, ci); var m = f.Meshes[slot];
            var count = new Dictionary<int,int>(); var bb = new Dictionary<int,Vector3[]>();
            var exact = new Dictionary<int, Vector3[]>();
            foreach (var v in m.Vertices)
                for (int k=0;k<4;k++) if (v.BoneWeights[k]>0)
                {
                    int bi=v.BoneIndices[k];
                    if (!count.ContainsKey(bi)) { count[bi]=0; bb[bi]=new[]{new Vector3(float.MaxValue),new Vector3(float.MinValue)}; exact[bi]=new[]{new Vector3(float.MaxValue),new Vector3(float.MinValue)}; }
                    count[bi]++; bb[bi][0]=Vector3.Min(bb[bi][0],v.Position);bb[bi][1]=Vector3.Max(bb[bi][1],v.Position);
                    Matrix4x4 ib; Matrix4x4.Invert(world[bi], out ib);
                    var lp=Vector3.Transform(v.Position,ib);
                    exact[bi][0]=Vector3.Min(exact[bi][0],lp);exact[bi][1]=Vector3.Max(exact[bi][1],lp);
                }
            Console.WriteLine("SLOT {0} mat {1} meshNode {2} verts {3}",slot,m.MaterialIndex,m.NodeIndex,m.Vertices.Count);
            foreach(var kv in count)
            {
                Vector3 lo=Vector3.Transform(bb[kv.Key][0],inv),hi=Vector3.Transform(bb[kv.Key][1],inv);
                if(kv.Key==bone || slot==10 || slot==27 || slot==30)
                    Console.WriteLine(" bone {0} {1} n={2} modelBBox=({3:R},{4:R},{5:R})..({6:R},{7:R},{8:R}) katanaLocalBBoxApprox=({9:R},{10:R},{11:R})..({12:R},{13:R},{14:R}) exactBoneLocal=({15:R},{16:R},{17:R})..({18:R},{19:R},{20:R})",kv.Key,f.Nodes[kv.Key].Name,kv.Value,bb[kv.Key][0].X,bb[kv.Key][0].Y,bb[kv.Key][0].Z,bb[kv.Key][1].X,bb[kv.Key][1].Y,bb[kv.Key][1].Z,lo.X,lo.Y,lo.Z,hi.X,hi.Y,hi.Z,exact[kv.Key][0].X,exact[kv.Key][0].Y,exact[kv.Key][0].Z,exact[kv.Key][1].X,exact[kv.Key][1].Y,exact[kv.Key][1].Z);
            }
            Vector3 l=new Vector3(float.MaxValue),h=new Vector3(float.MinValue);
            foreach(var v in m.Vertices){var p=Vector3.Transform(v.Position,inv);l=Vector3.Min(l,p);h=Vector3.Max(h,p);}
            Console.WriteLine(" all katanaLocalBBox=({0:R},{1:R},{2:R})..({3:R},{4:R},{5:R})",l.X,l.Y,l.Z,h.X,h.Y,h.Z);
        }
    }
}
