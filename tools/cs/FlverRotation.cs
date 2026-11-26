// FlverRotation.exe -- quelle transformation relie deux nuages de points ?
//
// Compare les sommets d'un maillage FLVER (notre build) a un TSV de positions
// (le modele source exporte par FModel), dans le meme ordre. On teste les 48
// matrices de permutation signee (24 rotations + 24 reflexions), avec une
// echelle uniforme, et on affiche les meilleures.
//
// Interet : repond sans ambiguite a "la piece est-elle tournee, et de combien ?"
//
// Usage :
//   FlverRotation.exe <fichier.flver> <maillage> <positions.tsv>
//
// Lecture seule.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Numerics;
using SoulsFormats;

internal static class FlverRotation
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 3)
        {
            Console.WriteLine("usage: FlverRotation.exe <fichier.flver> <maillage> <positions.tsv>");
            return 2;
        }
        int mi = int.Parse(args[1], Inv);

        FLVER2 f = FLVER2.Read(args[0]);
        FLVER2.Mesh m = f.Meshes[mi];
        var dest = new List<Vector3>();
        foreach (FLVER.Vertex v in m.Vertices) dest.Add(v.Position);

        var src = new List<Vector3>();
        foreach (string ligne in File.ReadLines(args[2]))
        {
            if (ligne.Length == 0 || ligne[0] == '#') continue;
            string[] champs = ligne.Split('\t');
            if (champs.Length < 4) continue;
            src.Add(new Vector3(
                float.Parse(champs[1], Inv),
                float.Parse(champs[2], Inv),
                float.Parse(champs[3], Inv)));
        }

        Console.WriteLine("flver    : " + args[0] + "  maillage " + mi + "  " + dest.Count + " sommets");
        Console.WriteLine("source   : " + args[2] + "  " + src.Count + " sommets");
        if (src.Count != dest.Count)
        {
            Console.WriteLine("!! nombres differents : la comparaison sommet a sommet n'est pas valable");
            return 1;
        }

        Vector3 cs = Vector3.Zero, cd = Vector3.Zero;
        foreach (Vector3 p in src) cs += p;
        foreach (Vector3 p in dest) cd += p;
        cs /= src.Count;
        cd /= dest.Count;

        int[][] permutations = new int[][]
        {
            new int[] { 0, 1, 2 }, new int[] { 0, 2, 1 }, new int[] { 1, 0, 2 },
            new int[] { 1, 2, 0 }, new int[] { 2, 0, 1 }, new int[] { 2, 1, 0 },
        };

        var resultats = new List<Tuple<double, string, double>>();
        foreach (int[] perm in permutations)
        {
            for (int signes = 0; signes < 8; signes++)
            {
                float sx = ((signes & 1) == 0) ? 1f : -1f;
                float sy = ((signes & 2) == 0) ? 1f : -1f;
                float sz = ((signes & 4) == 0) ? 1f : -1f;
                float[] s = { sx, sy, sz };

                double numerateur = 0.0, denominateur = 0.0;
                for (int i = 0; i < src.Count; i++)
                {
                    Vector3 p = src[i] - cs;
                    Vector3 q = dest[i] - cd;
                    Vector3 r = new Vector3(s[0] * Composante(p, perm[0]),
                                            s[1] * Composante(p, perm[1]),
                                            s[2] * Composante(p, perm[2]));
                    numerateur += Vector3.Dot(r, q);
                    denominateur += r.LengthSquared();
                }
                double echelle = denominateur > 0 ? numerateur / denominateur : 0.0;
                if (echelle <= 0) continue;

                double carres = 0.0;
                for (int i = 0; i < src.Count; i++)
                {
                    Vector3 p = src[i] - cs;
                    Vector3 q = dest[i] - cd;
                    Vector3 r = new Vector3(s[0] * Composante(p, perm[0]),
                                            s[1] * Composante(p, perm[1]),
                                            s[2] * Composante(p, perm[2]));
                    carres += (r * (float)echelle - q).LengthSquared();
                }
                double rms = Math.Sqrt(carres / src.Count);

                double det = s[0] * s[1] * s[2] * DeterminantPermutation(perm);
                string nom = Nommer(perm, s) + (det < 0 ? "  (reflexion)" : "");
                resultats.Add(Tuple.Create(rms, nom, echelle));
            }
        }

        resultats.Sort((a, b) => a.Item1.CompareTo(b.Item1));
        Console.WriteLine();
        Console.WriteLine("  ecart RMS    echelle   transformation");
        for (int i = 0; i < Math.Min(6, resultats.Count); i++)
        {
            Console.WriteLine(string.Format(Inv, "  {0,9:0.0000} m  x{1,6:0.0000}   {2}",
                resultats[i].Item1, resultats[i].Item2, resultats[i].Item3));
        }

        // Repere : la transformation identite, pour situer les autres.
        foreach (var r in resultats)
        {
            if (r.Item2 == "identite")
            {
                Console.WriteLine();
                Console.WriteLine(string.Format(Inv, "  identite (aucune transformation) : {0:0.0000} m  x{1:0.0000}",
                    r.Item1, r.Item3));
                break;
            }
        }
        return 0;
    }

    private static float Composante(Vector3 v, int axe)
    {
        if (axe == 0) return v.X;
        if (axe == 1) return v.Y;
        return v.Z;
    }

    private static int DeterminantPermutation(int[] p)
    {
        // signature de la permutation
        int inversions = 0;
        for (int i = 0; i < p.Length; i++)
            for (int j = i + 1; j < p.Length; j++)
                if (p[i] > p[j]) inversions++;
        return (inversions % 2 == 0) ? 1 : -1;
    }

    private static string Nommer(int[] perm, float[] s)
    {
        string[] axes = { "X", "Y", "Z" };
        var morceaux = new List<string>();
        for (int i = 0; i < 3; i++)
        {
            string signe = s[i] > 0 ? "+" : "-";
            morceaux.Add(signe + axes[perm[i]]);
        }
        string nom = string.Join("", morceaux);
        bool identite = perm[0] == 0 && perm[1] == 1 && perm[2] == 2
                        && s[0] > 0 && s[1] > 0 && s[2] > 0;
        return identite ? "identite" : nom;
    }
}
