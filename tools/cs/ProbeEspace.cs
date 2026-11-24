// ProbeEspace - determine dans quel espace sont ecrits les sommets d'un FLVER.
//
// Question : les sommets d'un maillage sont-ils en espace MONDE (modele) ou en
// espace LOCAL du noeud porteur (NodeIndex) ?
//
// Si espace monde  : le centre de la bbox d'un maillage (tete, pied...) est
//                    proche de la position globale de son noeud dans le modele.
// Si espace local  : le centre est proche de (0,0,0), et c'est la position
//                    globale du noeud qui le replace dans le modele.
//
// Usage : ProbeEspace.exe modele.flver
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Numerics;
using SoulsFormats;

internal static class ProbeEspace
{
    private static FLVER2 f;
    private static Matrix4x4[] loc, glo;
    private static bool[] done;
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static Matrix4x4 Global(int i)
    {
        if (done[i]) return glo[i];
        Matrix4x4 m = loc[i];
        int p = f.Nodes[i].ParentIndex;
        if (p >= 0 && p < f.Nodes.Count && p != i) m = Matrix4x4.Multiply(m, Global(p));
        glo[i] = m;
        done[i] = true;
        return m;
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: ProbeEspace.exe modele.flver"); return 2; }
        f = FLVER2.Read(args[0]);
        int n = f.Nodes.Count;
        loc = new Matrix4x4[n]; glo = new Matrix4x4[n]; done = new bool[n];
        for (int i = 0; i < n; i++) loc[i] = f.Nodes[i].ComputeLocalTransform();
        for (int i = 0; i < n; i++) Global(i);

        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("noeuds " + n + "  maillages " + f.Meshes.Count);

        // 1) les noeuds porteurs de maillages : leur position globale
        var porteurs = new SortedSet<int>();
        foreach (FLVER2.Mesh m in f.Meshes) porteurs.Add(m.NodeIndex);

        Console.WriteLine();
        Console.WriteLine("=== noeuds porteurs de maillages (position globale) ===");
        foreach (int i in porteurs)
        {
            Matrix4x4 g = glo[i];
            Vector3 t = new Vector3(g.M41, g.M42, g.M43);
            float ex = (float)Math.Sqrt(g.M11 * g.M11 + g.M12 * g.M12 + g.M13 * g.M13);
            float ey = (float)Math.Sqrt(g.M21 * g.M21 + g.M22 * g.M22 + g.M23 * g.M23);
            float ez = (float)Math.Sqrt(g.M31 * g.M31 + g.M32 * g.M32 + g.M33 * g.M33);
            Console.WriteLine(string.Format(Inv,
                "  noeud {0,4}  {1,-24} T=({2,8:0.###},{3,8:0.###},{4,8:0.###})  echelle=({5,7:0.####},{6,7:0.####},{7,7:0.####})",
                i, f.Nodes[i].Name, t.X, t.Y, t.Z, ex, ey, ez));
        }

        // 2) pour chaque maillage : centre de la bbox des sommets
        Console.WriteLine();
        Console.WriteLine("=== maillages : bbox des sommets lus ===");
        Console.WriteLine("  idx noeud  sommets   centre X    centre Y    centre Z   taille X  taille Y  taille Z");
        for (int mi = 0; mi < f.Meshes.Count; mi++)
        {
            FLVER2.Mesh m = f.Meshes[mi];
            Vector3 mn = new Vector3(float.MaxValue);
            Vector3 mx = new Vector3(float.MinValue);
            foreach (FLVER.Vertex v in m.Vertices)
            {
                mn = Vector3.Min(mn, v.Position);
                mx = Vector3.Max(mx, v.Position);
            }
            Vector3 c = (mn + mx) * 0.5f;
            Console.WriteLine(string.Format(Inv,
                "  {0,3} {1,4} {2,8}   {3,9:0.###} {4,9:0.###} {5,9:0.###}   {6,8:0.###} {7,8:0.###} {8,8:0.###}",
                mi, m.NodeIndex, m.Vertices.Count, c.X, c.Y, c.Z, mx.X - mn.X, mx.Y - mn.Y, mx.Z - mn.Z));
        }

        // 3) pour les noeuds porteurs : bbox des sommets des maillages qui les portent
        Console.WriteLine();
        Console.WriteLine("=== maillages portes par un noeud : centre des sommets vs position du noeud ===");
        for (int mi = 0; mi < f.Meshes.Count; mi++)
        {
            FLVER2.Mesh m = f.Meshes[mi];
            Vector3 mn = new Vector3(float.MaxValue);
            Vector3 mx = new Vector3(float.MinValue);
            foreach (FLVER.Vertex v in m.Vertices)
            {
                mn = Vector3.Min(mn, v.Position);
                mx = Vector3.Max(mx, v.Position);
            }
            Vector3 c = (mn + mx) * 0.5f;
            Matrix4x4 g = glo[m.NodeIndex];
            Vector3 t = new Vector3(g.M41, g.M42, g.M43);
            Console.WriteLine(string.Format(Inv,
                "  mesh {0,3} noeud {1,4} : centre sommets=({2,7:0.##},{3,7:0.##},{4,7:0.##})  position noeud=({5,7:0.##},{6,7:0.##},{7,7:0.##})  ecart={8,7:0.##}",
                mi, m.NodeIndex, c.X, c.Y, c.Z, t.X, t.Y, t.Z, (c - t).Length()));
        }
        return 0;
    }
}
