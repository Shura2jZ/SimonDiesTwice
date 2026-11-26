// FlverVolumes - mesure l'ORIENTATION ABSOLUE d'un maillage, sans jamais
// comparer l'enroulement aux normales stockees (le test "dot(g,n)" est aveugle :
// si on inverse l'enroulement ET les normales, il donne le meme resultat).
//
// Deux mesures independantes, sur le faceset 0 :
//   Vn = volume signe calcule avec les NORMALES stockees (theoreme de la
//        divergence). Si les normales pointent vers l'exterieur d'une surface
//        fermee, Vn > 0.
//   Vg = volume signe calcule avec l'ENROULEMENT des triangles
//        (v0 . (v1 x v2) / 6). Il depend uniquement de l'ordre des sommets.
//   nRadial% = pourcentage de sommets dont la normale s'eloigne du centroide.
//
// Usage : FlverVolumes.exe modele.flver
using System;
using System.Numerics;
using SoulsFormats;

internal static class FlverVolumes
{
    private static void V(Vector3 v, out string s)
    {
        s = string.Format(System.Globalization.CultureInfo.InvariantCulture,
            "({0,8:F3} {1,8:F3} {2,8:F3})", v.X, v.Y, v.Z);
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverVolumes.exe modele.flver"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine();
        Console.WriteLine(string.Format("{0,4} | {1,7} | {2,14} | {3,14} | {4,8} | {5,9} | {6,8}",
            "idx", "somm", "Vn (normales)", "Vg (enroul.)", "signeVn", "signeVg", "nRadial%"));
        int n = 0;
        foreach (FLVER2.Mesh m in f.Meshes)
        {
            if (m.Vertices.Count == 0) { n++; continue; }

            Vector3 c = Vector3.Zero;
            foreach (FLVER.Vertex v in m.Vertices) c += v.Position;
            c /= m.Vertices.Count;

            double vn = 0.0, vg = 0.0;
            long radialPos = 0, radialTot = 0;

            foreach (FLVER.Vertex v in m.Vertices)
            {
                Vector3 d = v.Position - c;
                if (d.LengthSquared() > 1e-12f)
                {
                    radialTot++;
                    if (Vector3.Dot(v.Normal, Vector3.Normalize(d)) > 0f) radialPos++;
                }
            }

            if (m.FaceSets.Count > 0)
            {
                var ix = m.FaceSets[0].Indices;
                for (int t = 0; t + 2 < ix.Count; t += 3)
                {
                    Vector3 a = m.Vertices[ix[t]].Position;
                    Vector3 b = m.Vertices[ix[t + 1]].Position;
                    Vector3 d = m.Vertices[ix[t + 2]].Position;
                    Vector3 nm = (m.Vertices[ix[t]].Normal + m.Vertices[ix[t + 1]].Normal
                                  + m.Vertices[ix[t + 2]].Normal) / 3f;
                    Vector3 cen = (a + b + d) / 3f;
                    float aire = 0.5f * Vector3.Cross(b - a, d - a).Length();
                    vn += Vector3.Dot(cen - c, nm) * aire / 3.0;
                    vg += Vector3.Dot(a, Vector3.Cross(b, d)) / 6.0;
                }
            }

            double radPct = radialTot == 0 ? 0.0 : 100.0 * radialPos / radialTot;
            Console.WriteLine(string.Format(System.Globalization.CultureInfo.InvariantCulture,
                "{0,4} | {1,7} | {2,14:E3} | {3,14:E3} | {4,8} | {5,9} | {6,8:F1}",
                n, m.Vertices.Count, vn, vg, vn > 0 ? "+" : "-", vg > 0 ? "+" : "-", radPct));
            n++;
        }
        return 0;
    }
}
