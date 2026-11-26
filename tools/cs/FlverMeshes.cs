// FlverMeshes - detail des maillages d'un FLVER : noeud porteur, materiau, indicateurs,
// facesets (drapeaux et nombre de triangles) et etendue reelle des sommets.
//
// L'etendue reelle permet de distinguer les maillages du personnage (autour de
// l'origine, ~2 m de haut) de ceux des armes (coordonnees locales, valeurs extremes).
//
// Usage : FlverMeshes.exe modele.flver
using System;
using System.Globalization;
using System.Linq;
using System.Numerics;
using SoulsFormats;

internal static class FlverMeshes
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    private static string F(float v) { return v.ToString("0.####", Inv); }
    private static string P(Vector3 v) { return "(" + F(v.X) + ", " + F(v.Y) + ", " + F(v.Z) + ")"; }

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverMeshes.exe modele.flver"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);

        Console.WriteLine("maillages : " + f.Meshes.Count + "   materiaux : " + f.Materials.Count + "   os : " + f.Nodes.Count);
        Console.WriteLine();
        for (int i = 0; i < f.Meshes.Count; i++)
        {
            var m = f.Meshes[i];
            string nodeName = (m.NodeIndex >= 0 && m.NodeIndex < f.Nodes.Count) ? f.Nodes[m.NodeIndex].Name : "?";
            string matName = (m.MaterialIndex >= 0 && m.MaterialIndex < f.Materials.Count) ? f.Materials[m.MaterialIndex].Name : "?";
            Vector3 lo = new Vector3(float.MaxValue), hi = new Vector3(float.MinValue);
            foreach (var v in m.Vertices) { lo = Vector3.Min(lo, v.Position); hi = Vector3.Max(hi, v.Position); }

            Console.WriteLine(string.Format(Inv, "[{0,2}] noeud={1,4} ({2})  materiau={3,2} ({4})  dyn={5} poids={6} sommets={7,6}",
                i, m.NodeIndex, nodeName, m.MaterialIndex, matName, m.Dynamic, m.UseBoneWeights, m.Vertices.Count));
            Console.WriteLine("      etendue reelle : " + P(lo) + " .. " + P(hi)
                + "   (hauteur " + F(hi.Y - lo.Y) + ")");
            Console.WriteLine("      os du maillage : " + (m.BoneIndices == null || m.BoneIndices.Count == 0 ? "(vide)"
                : string.Join(",", m.BoneIndices.Take(12).Select(b => b.ToString(Inv)).ToArray())));
            Console.WriteLine("      buffers : " + string.Join(" | ", m.VertexBuffers.Select(vb =>
                "layout#" + vb.LayoutIndex + " buf#" + vb.BufferIndex).ToArray()));
            foreach (var fs in m.FaceSets)
                Console.WriteLine("      faceset flags=" + fs.Flags + " strip=" + fs.TriangleStrip + " cull=" + fs.CullBackfaces
                    + " unk=" + fs.Unk06 + " indices=" + fs.Indices.Count + " (" + (fs.Indices.Count / 3) + " triangles)");
        }
        Console.WriteLine();
        Console.WriteLine("=== materiaux : nom, MTD, nb textures ===");
        for (int i = 0; i < f.Materials.Count; i++)
            Console.WriteLine(string.Format(Inv, "[{0,2}] {1,-26} mtd={2}  textures={3}",
                i, f.Materials[i].Name, f.Materials[i].MTD.Replace("N:\\NTC\\data\\Material\\mtd\\", ""), f.Materials[i].Textures.Count));
        return 0;
    }
}
