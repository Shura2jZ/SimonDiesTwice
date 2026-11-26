// FlverInfo - inspecte un FLVER (ou un .flver.dcx) avec SoulsFormats et affiche
// tout ce dont on a besoin pour le portage : os, materiaux, maillages, layouts.
//
// Compilation : tools\cs_build.ps1 FlverInfo
// Usage       : FlverInfo.exe modele.flver [--bones] [--mats] [--meshes]
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Numerics;
using SoulsFormats;

internal static class FlverInfo
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static string F(float v) { return v.ToString("0.####", Inv); }
    private static string V3(Vector3 v) { return "(" + F(v.X) + ", " + F(v.Y) + ", " + F(v.Z) + ")"; }

    private static int Main(string[] args)
    {
        if (args.Length == 0) { Console.WriteLine("usage: FlverInfo.exe modele.flver [--bones] [--mats] [--meshes]"); return 2; }
        string path = args[0];
        var opts = new HashSet<string>(args.Skip(1).Select(a => a.ToLowerInvariant()));
        bool onlyBones = opts.Contains("--bones");
        bool onlyMats = opts.Contains("--mats");
        bool onlyMeshes = opts.Contains("--meshes");
        bool everything = !onlyBones && !onlyMats && !onlyMeshes;

        FLVER2 flver = FLVER2.Read(path);
        var fi = new FileInfo(path);

        Console.WriteLine("fichier      : " + fi.Name + "  (" + fi.Length.ToString("N0", Inv) + " octets)");
        Console.WriteLine("version      : 0x" + flver.Header.Version.ToString("X") + "   unicode=" + flver.Header.Unicode + "   bigEndian=" + flver.Header.BigEndian);
        Console.WriteLine("bboite (min) : " + V3(flver.Header.BoundingBoxMin) + "   (max) " + V3(flver.Header.BoundingBoxMax));
        Console.WriteLine("squelette    : " + (flver.Skeletons != null && flver.Skeletons.BaseSkeleton != null ? flver.Skeletons.BaseSkeleton.Count : 0) + " os (base)");
        Console.WriteLine("os (nodes)   : " + flver.Nodes.Count);
        Console.WriteLine("materiaux    : " + flver.Materials.Count);
        Console.WriteLine("maillages    : " + flver.Meshes.Count);
        Console.WriteLine("layouts      : " + flver.BufferLayouts.Count);
        Console.WriteLine("dummies      : " + flver.Dummies.Count);
        Console.WriteLine("gxLists      : " + flver.GXLists.Count);
        Console.WriteLine();

        if (everything || onlyBones)
        {
            Console.WriteLine("=== OS (" + flver.Nodes.Count + ") ===");
            for (int i = 0; i < flver.Nodes.Count; i++)
            {
                var n = flver.Nodes[i];
                Console.WriteLine(string.Format(Inv, "{0,4}  {1,-34} parent={2,4} enfant={3,4} frere={4,4} flags={5} T={6}",
                    i, n.Name, n.ParentIndex, n.FirstChildIndex, n.NextSiblingIndex, n.Flags, V3(n.Translation)));
            }
            Console.WriteLine();
        }

        if (everything || onlyMats)
        {
            Console.WriteLine("=== MATERIAUX (" + flver.Materials.Count + ") ===");
            for (int i = 0; i < flver.Materials.Count; i++)
            {
                var m = flver.Materials[i];
                Console.WriteLine(string.Format(Inv, "{0,4}  {1,-28} MTD={2}  gx={3}", i, m.Name, m.MTD, m.GXIndex));
                foreach (var t in m.Textures)
                    Console.WriteLine("        " + (t.Type != null ? t.Type.PadRight(22) : "?".PadRight(22)) + t.Path);
            }
            Console.WriteLine();
        }

        if (everything || onlyMeshes)
        {
            Console.WriteLine("=== MAILLAGES (" + flver.Meshes.Count + ") ===");
            for (int i = 0; i < flver.Meshes.Count; i++)
            {
                var me = flver.Meshes[i];
                int tris = 0;
                foreach (var fs in me.FaceSets) tris += fs.Indices.Count / 3;
                Console.WriteLine(string.Format(Inv, "{0,4}  noeud={1,4} materiau={2,3} dyn={3} poids={4} sommets={5,7} faces={6,7} bbox={7}..{8}",
                    i, me.NodeIndex, me.MaterialIndex, me.Dynamic, me.UseBoneWeights, me.Vertices.Count, tris,
                    V3(me.BoundingBox.Min), V3(me.BoundingBox.Max)));
                foreach (var vb in me.VertexBuffers)
                {
                    string members = "";
                    if (vb.LayoutIndex >= 0 && vb.LayoutIndex < flver.BufferLayouts.Count)
                        members = string.Join(" ", flver.BufferLayouts[vb.LayoutIndex].Select(lm =>
                            lm.Semantic + (lm.Index > 0 ? lm.Index.ToString(Inv) : "") + ":" + lm.Type).ToArray());
                    Console.WriteLine("        buffer " + vb.BufferIndex + "  layout# " + vb.LayoutIndex + "  [" + members + "]");
                }
                if (me.BoneIndices != null && me.BoneIndices.Count > 0)
                    Console.WriteLine("        os du maillage : " + string.Join(", ", me.BoneIndices.Take(30).Select(b => b.ToString(Inv)).ToArray())
                        + (me.BoneIndices.Count > 30 ? " ..." : ""));
            }
            Console.WriteLine();

            Console.WriteLine("=== LAYOUTS DE SOMMETS (" + flver.BufferLayouts.Count + ") ===");
            for (int i = 0; i < flver.BufferLayouts.Count; i++)
            {
                var bl = flver.BufferLayouts[i];
                Console.WriteLine(string.Format(Inv, "{0,4}  taille={1,3} octets : {2}", i, bl.Size,
                    string.Join("  ", bl.Select(lm => lm.Semantic.ToString() + (lm.Index > 0 ? lm.Index.ToString(Inv) : "")
                        + "(" + lm.Type + ",#" + lm.Stream + ")").ToArray())));
            }
        }

        return 0;
    }
}
