// FlverSommets - affiche, pour chaque maillage d'un FLVER, les premiers sommets
// avec la pleine precision, afin de retrouver leurs octets dans le fichier et
// donc de localiser le vrai debut des donnees de sommets.
//
// Usage : FlverSommets.exe <modele.flver> [nbParMaillage] [maxMaillages]
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Numerics;
using SoulsFormats;

internal static class FlverSommets
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage: FlverSommets.exe <modele.flver> [nbParMaillage] [maxMaillages]");
            return 2;
        }
        int nb = args.Length > 1 ? int.Parse(args[1], Inv) : 3;
        int maxi = args.Length > 2 ? int.Parse(args[2], Inv) : 5;

        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("maillages : " + f.Meshes.Count);
        Console.WriteLine();

        for (int i = 0; i < f.Meshes.Count && i < maxi; i++)
        {
            FLVER2.Mesh m = f.Meshes[i];
            int disp = m.VertexBuffers.Count > 0 ? m.VertexBuffers[0].LayoutIndex : -1;
            int tail = (disp >= 0 && disp < f.BufferLayouts.Count) ? f.BufferLayouts[disp].Size : -1;
            Vector3 lo = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue);
            Vector3 hi = new Vector3(float.MinValue, float.MinValue, float.MinValue);
            foreach (FLVER.Vertex vv in m.Vertices)
            {
                lo = Vector3.Min(lo, vv.Position);
                hi = Vector3.Max(hi, vv.Position);
            }
            Console.WriteLine("maillage[" + i + "] materiau " + m.MaterialIndex + "  sommets " + m.Vertices.Count
                + "  noeud " + m.NodeIndex + "  disposition " + disp + " (taille " + tail + ")");
            Console.WriteLine(string.Format(Inv, "  boite reelle : min ({0} {1} {2})  max ({3} {4} {5})",
                lo.X.ToString("R", Inv), lo.Y.ToString("R", Inv), lo.Z.ToString("R", Inv),
                hi.X.ToString("R", Inv), hi.Y.ToString("R", Inv), hi.Z.ToString("R", Inv)));
            Console.WriteLine(string.Format(Inv, "  taille       : ({0} {1} {2})   centre : ({3} {4} {5})",
                (hi.X - lo.X).ToString("R", Inv), (hi.Y - lo.Y).ToString("R", Inv), (hi.Z - lo.Z).ToString("R", Inv),
                ((hi.X + lo.X) * 0.5f).ToString("R", Inv), ((hi.Y + lo.Y) * 0.5f).ToString("R", Inv),
                ((hi.Z + lo.Z) * 0.5f).ToString("R", Inv)));
            Console.WriteLine(string.Format(Inv, "  declare      : min ({0} {1} {2})  max ({3} {4} {5})  unk ({6} {7} {8})",
                m.BoundingBox.Min.X.ToString("R", Inv), m.BoundingBox.Min.Y.ToString("R", Inv), m.BoundingBox.Min.Z.ToString("R", Inv),
                m.BoundingBox.Max.X.ToString("R", Inv), m.BoundingBox.Max.Y.ToString("R", Inv), m.BoundingBox.Max.Z.ToString("R", Inv),
                m.BoundingBox.Unk.X.ToString("R", Inv), m.BoundingBox.Unk.Y.ToString("R", Inv), m.BoundingBox.Unk.Z.ToString("R", Inv)));
            Console.WriteLine();
            for (int k = 0; k < nb && k < m.Vertices.Count; k++)
            {
                FLVER.Vertex v = m.Vertices[k];
                Console.WriteLine(string.Format(Inv, "  sommet[{0}] pos = {1} {2} {3}",
                    k, v.Position.X.ToString("R", Inv), v.Position.Y.ToString("R", Inv), v.Position.Z.ToString("R", Inv)));
                Console.WriteLine(string.Format(Inv, "             nor = {0} {1} {2} (w {3})",
                    v.Normal.X.ToString("R", Inv), v.Normal.Y.ToString("R", Inv), v.Normal.Z.ToString("R", Inv), v.NormalW));
                Console.WriteLine(string.Format(Inv, "             os = {0} {1} {2} {3}   poids = {4} {5} {6} {7}",
                    v.BoneIndices[0], v.BoneIndices[1], v.BoneIndices[2], v.BoneIndices[3],
                    v.BoneWeights[0].ToString("R", Inv), v.BoneWeights[1].ToString("R", Inv),
                    v.BoneWeights[2].ToString("R", Inv), v.BoneWeights[3].ToString("R", Inv)));
                if (v.UVs.Count > 0)
                    Console.WriteLine(string.Format(Inv, "             uv0 = {0} {1}",
                        v.UVs[0].X.ToString("R", Inv), v.UVs[0].Y.ToString("R", Inv)));
                if (v.Colors.Count > 0)
                    Console.WriteLine("             couleur = " + v.Colors[0]);
            }
            Console.WriteLine();
        }
        return 0;
    }
}
