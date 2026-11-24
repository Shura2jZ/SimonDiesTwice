// FlverOrient - test ABSOLU de l'orientation des normales, valable meme pour
// une surface OUVERTE (un volume signe ne veut rien dire pour un manteau).
//
// Idee : chaque sommet est pondere a des os qui se trouvent A L'INTERIEUR du
// corps. Une normale correcte (tournee vers l'exterieur) doit donc s'eloigner
// de la position moyenne de ces os :
//     s = dot(normale, position_sommet - position_os_pesee)
// On compte la part de sommets avec s > 0 (attendu : tres majoritaire) et la
// moyenne de s (attendu : > 0).
//
// Aucune comparaison a l'enroulement : ce test detecte une inversion qui
// toucherait les normales ET l'enroulement en meme temps.
//
// Usage : FlverOrient.exe modele.flver
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Numerics;
using SoulsFormats;

internal static class FlverOrient
{
    private static FLVER2 g_f;
    private static Matrix4x4[] g_glob;
    private static bool[] g_fait;

    private static Matrix4x4 Global(int i)
    {
        if (g_fait[i]) return g_glob[i];
        Matrix4x4 m = g_f.Nodes[i].ComputeLocalTransform();  // local (FLVER.Node)
        int p = g_f.Nodes[i].ParentIndex;
        if (p >= 0 && p < g_f.Nodes.Count && p != i) m = Matrix4x4.Multiply(m, Global(p));
        g_glob[i] = m;
        g_fait[i] = true;
        return m;
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverOrient.exe modele.flver"); return 2; }
        g_f = FLVER2.Read(args[0]);
        g_glob = new Matrix4x4[g_f.Nodes.Count];
        g_fait = new bool[g_f.Nodes.Count];

        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine();
        Console.WriteLine(string.Format("{0,4} | {1,7} | {2,9} | {3,9} | {4,9} | {5,9}",
            "idx", "somm", "s>0", "moy s", "med |d|", "os moyen"));
        int n = 0;
        foreach (FLVER2.Mesh m in g_f.Meshes)
        {
            if (m.Vertices.Count == 0) { n++; continue; }
            int pos = 0, tot = 0;
            double somme = 0.0;
            double sommeD = 0.0;
            foreach (FLVER.Vertex v in m.Vertices)
            {
                Vector3 osPos = Vector3.Zero;
                float sommePoids = 0f;
                bool ok = true;
                for (int k = 0; k < 4; k++)
                {
                    int bi = v.BoneIndices[k];
                    float w = v.BoneWeights[k];
                    if (w <= 0f) continue;
                    if (bi < 0 || bi >= g_f.Nodes.Count) { ok = false; break; }
                    Matrix4x4 g = Global(bi);
                    osPos += new Vector3(g.M41, g.M42, g.M43) * w;
                    sommePoids += w;
                }
                if (!ok || sommePoids <= 1e-6f) continue;
                osPos /= sommePoids;
                Vector3 d = v.Position - osPos;
                float len = d.Length();
                if (len < 1e-6f) continue;
                float s = Vector3.Dot(v.Normal, d / len);
                tot++;
                somme += s;
                sommeD += len;
                if (s > 0f) pos++;
            }
            if (tot == 0) { n++; continue; }
            Console.WriteLine(string.Format(CultureInfo.InvariantCulture,
                "{0,4} | {1,7} | {2,8:F1}% | {3,9:F3} | {4,9:F3} | {5,9:F3}",
                n, m.Vertices.Count, 100.0 * pos / tot, somme / tot, sommeD / tot, 0.0));
            n++;
        }
        return 0;
    }
}
