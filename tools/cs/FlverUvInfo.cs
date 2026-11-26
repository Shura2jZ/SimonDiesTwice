// FlverUvInfo.exe -- etat des canaux d'UV d'un maillage.
//
// Question traitee : le layout 40 octets stocke les UV en 4 entiers 16 bits, ce
// que SoulsFormats relit comme DEUX canaux. Avant de retourner le V des deux,
// il faut savoir si le second canal est une copie du premier (auquel cas le
// retourner est sans effet) ou une vraie deuxieme jeu d'UV (auquel cas il ne
// faut peut-etre pas y toucher).
//
// Usage :
//   FlverUvInfo.exe <fichier.flver> <maillages|tous>
//
// Lecture seule.
using System;
using System.Collections.Generic;
using System.Globalization;
using SoulsFormats;

internal static class FlverUvInfo
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("usage: FlverUvInfo.exe <fichier.flver> <maillages|tous>");
            return 2;
        }
        bool tous = args[1] == "tous";
        var voulus = new HashSet<int>();
        if (!tous) foreach (string s in args[1].Split(',')) voulus.Add(int.Parse(s.Trim(), Inv));

        FLVER2 f = FLVER2.Read(args[0]);
        for (int mi = 0; mi < f.Meshes.Count; mi++)
        {
            if (!tous && !voulus.Contains(mi)) continue;
            FLVER2.Mesh m = f.Meshes[mi];
            if (m.Vertices.Count == 0) continue;

            int canaux = m.Vertices[0].UVs != null ? m.Vertices[0].UVs.Count : 0;
            int identiques = 0, ecartes = 0;
            double[] umin = new double[canaux], umax = new double[canaux];
            double[] vmin = new double[canaux], vmax = new double[canaux];
            for (int k = 0; k < canaux; k++)
            {
                umin[k] = vmin[k] = double.MaxValue;
                umax[k] = vmax[k] = double.MinValue;
            }

            foreach (FLVER.Vertex v in m.Vertices)
            {
                if (v.UVs == null) continue;
                for (int k = 0; k < v.UVs.Count && k < canaux; k++)
                {
                    umin[k] = Math.Min(umin[k], v.UVs[k].X);
                    umax[k] = Math.Max(umax[k], v.UVs[k].X);
                    vmin[k] = Math.Min(vmin[k], v.UVs[k].Y);
                    vmax[k] = Math.Max(vmax[k], v.UVs[k].Y);
                }
                if (canaux >= 2)
                {
                    if (v.UVs[0] == v.UVs[1]) identiques++;
                    else ecartes++;
                }
            }

            Console.WriteLine(string.Format(Inv, "maillage {0,2} : {1,6} sommets, {2} canaux", mi, m.Vertices.Count, canaux));
            for (int k = 0; k < canaux; k++)
            {
                Console.WriteLine(string.Format(Inv, "   canal {0} : u {1,7:0.0000} .. {2,7:0.0000}   v {3,7:0.0000} .. {4,7:0.0000}",
                    k, umin[k], umax[k], vmin[k], vmax[k]));
            }
            if (canaux >= 2)
            {
                Console.WriteLine(string.Format(Inv, "   canal 2 identique au canal 1 : {0} sommets ; different : {1}",
                    identiques, ecartes));
            }
        }
        return 0;
    }
}
