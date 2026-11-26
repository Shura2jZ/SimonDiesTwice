// FlverWinding -- teste l'ORIENTATION des triangles d'un FLVER.
//
// Pourquoi : aucun de nos tests n'a jamais verifie le sens d'enroulement
// (winding) des faces. Or nos rendus hors-jeu utilisent renderMode "Both"
// (les deux faces, donc sans test de face cachee) : une inversion totale du
// sens des triangles y est parfaitement invisible, alors qu'en jeu, avec
// cull=True, elle rend le personnage "creux" : on ne voit plus que l'interieur
// (grandes surfaces sombres) et les bords (fines lignes claires).
//
// Deux mesures independantes par maillage :
//   A) volume signe  V = somme dot(p0, cross(p1,p2))/6   sur les triangles.
//      Pour un maillage ferme, V>0 si l'enroulement est sortant (convention
//      habituelle), V<0 s'il est rentrant. Comparer vanille et notre build :
//      si les signes sont opposes, l'enroulement est inverse.
//   B) coherence locale : dot(normale geometrique de la face, moyenne des
//      normales stockees aux 3 sommets). Doit etre > 0 partout en vanille.
//   C) sortance : dot(normale de la face, centre_triangle - centre_maillage).
//
// Usage : FlverWinding.exe modele.flver [maillages...]
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Numerics;
using SoulsFormats;

internal static class FlverWinding
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverWinding.exe modele.flver [maillages...]"); return 2; }

        FLVER2 f = FLVER2.Read(args[0]);
        var voulus = new List<int>();
        for (int i = 1; i < args.Length; i++) voulus.Add(int.Parse(args[i]));

        Console.WriteLine("fichier   : " + args[0]);
        Console.WriteLine("maillages : " + f.Meshes.Count);
        Console.WriteLine();
        Console.WriteLine("maill   mat   sommets   triangles   volumeSigne      A:dot(face,norm)   A>0      B:sortance   B>0");

        double volTot = 0; int triTot = 0, aPosTot = 0, bPosTot = 0;

        for (int mi = 0; mi < f.Meshes.Count; mi++)
        {
            if (voulus.Count > 0 && !voulus.Contains(mi)) continue;
            FLVER2.Mesh m = f.Meshes[mi];
            List<FLVER.Vertex> vs = m.Vertices;
            if (vs.Count == 0) continue;

            // centre du maillage (moyenne des sommets)
            Vector3 centre = Vector3.Zero;
            for (int i = 0; i < vs.Count; i++) centre += vs[i].Position;
            centre /= vs.Count;

            double volume = 0;
            int tri = 0, aPos = 0, bPos = 0;
            double sommeA = 0, sommeB = 0;

            foreach (FLVER2.FaceSet fs in m.FaceSets)
            {
                // une seule fois par jeu d'indices distinct (nos 6 facesets sont identiques)
                if ((fs.Flags & (FLVER2.FaceSet.FSFlags.LodLevel1 | FLVER2.FaceSet.FSFlags.LodLevel2
                                | FLVER2.FaceSet.FSFlags.MotionBlur)) != 0) continue;

                List<int> idx = fs.Indices;
                for (int t = 0; t + 2 < idx.Count; t += 3)
                {
                    int i0 = idx[t], i1 = idx[t + 1], i2 = idx[t + 2];
                    if (i0 < 0 || i1 < 0 || i2 < 0 || i0 >= vs.Count || i1 >= vs.Count || i2 >= vs.Count) continue;
                    Vector3 p0 = vs[i0].Position, p1 = vs[i1].Position, p2 = vs[i2].Position;
                    Vector3 g = Vector3.Cross(p1 - p0, p2 - p0);
                    if (g.LengthSquared() < 1e-12f) continue;
                    Vector3 gn = Vector3.Normalize(g);

                    volume += Vector3.Dot(p0, Vector3.Cross(p1, p2)) / 6.0;

                    Vector3 avgN = vs[i0].Normal + vs[i1].Normal + vs[i2].Normal;
                    if (avgN.LengthSquared() > 1e-12f)
                    {
                        double da = Vector3.Dot(gn, Vector3.Normalize(avgN));
                        sommeA += da;
                        if (da > 0) aPos++;
                    }

                    Vector3 c = (p0 + p1 + p2) / 3f;
                    Vector3 ext = c - centre;
                    if (ext.LengthSquared() > 1e-12f)
                    {
                        double db = Vector3.Dot(gn, Vector3.Normalize(ext));
                        sommeB += db;
                        if (db > 0) bPos++;
                    }
                    tri++;
                }
            }

            if (tri == 0) continue;
            volTot += volume; triTot += tri; aPosTot += aPos; bPosTot += bPos;

            Console.WriteLine(string.Format(Inv,
                "{0,4}  {1,4}  {2,7}  {3,9}   {4,14:0.######}   {5,15:0.0000}   {6,5:0.0}%   {7,10:0.0000}   {8,5:0.0}%",
                mi, m.MaterialIndex, vs.Count, tri, volume,
                tri > 0 ? sommeA / tri : 0, tri > 0 ? 100.0 * aPos / tri : 0,
                tri > 0 ? sommeB / tri : 0, tri > 0 ? 100.0 * bPos / tri : 0));
        }

        Console.WriteLine();
        Console.WriteLine(string.Format(Inv,
            "ENSEMBLE : volume signe {0:0.####}   triangles {1}   A>0 {2:0.0}%   B>0 {3:0.0}%",
            volTot, triTot, triTot > 0 ? 100.0 * aPosTot / triTot : 0, triTot > 0 ? 100.0 * bPosTot / triTot : 0));
        return 0;
    }
}
