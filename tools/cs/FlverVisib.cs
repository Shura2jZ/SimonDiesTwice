// FlverVisib.exe -- un maillage est-il DESSINE mais CACHE, ou pas dessine du tout ?
//
// On place une camera virtuelle dans 26 directions autour du centre de la boite
// du maillage cible, on lance un rayon vers chacun de ses sommets (echantillonnes)
// et on regarde si un AUTRE maillage intercepte le rayon avant lui.
//
// Aucun autre maillage n'intercepte  -> le maillage est visible de l'exterieur :
//                                       s'il n'apparait pas en jeu, il n'est PAS dessine.
// Tous les autres interceptent      -> le maillage est enferme : il est dessine
//                                       mais dissimule, il faut retirer les
//                                       maillages qui le couvrent.
//
// Usage : FlverVisib.exe modele.flver [cibles=4,5] [dist=3] [echantillons=120]
//
// Lecture seule.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Numerics;
using SoulsFormats;

internal static class FlverVisib
{
    private sealed class Tri
    {
        public Vector3 A, B, C;
        public int Maillage;
    }

    private sealed class Bloc
    {
        public Vector3 Min, Max;
        public List<Tri> Triangles = new List<Tri>();
    }

    private static bool RayonTriangle(Vector3 o, Vector3 d, Tri t, out float tt)
    {
        tt = 0f;
        Vector3 e1 = t.B - t.A;
        Vector3 e2 = t.C - t.A;
        Vector3 p = Vector3.Cross(d, e2);
        float det = Vector3.Dot(e1, p);
        if (det > -1e-9f && det < 1e-9f) return false;
        float inv = 1f / det;
        Vector3 tv = o - t.A;
        float u = Vector3.Dot(tv, p) * inv;
        if (u < -1e-6f || u > 1f + 1e-6f) return false;
        Vector3 q = Vector3.Cross(tv, e1);
        float v = Vector3.Dot(d, q) * inv;
        if (v < -1e-6f || u + v > 1f + 1e-6f) return false;
        float t0 = Vector3.Dot(e2, q) * inv;
        if (t0 <= 1e-4f || t0 >= 1f - 1e-3f) return false;
        tt = t0;
        return true;
    }

    private static bool CroiseBoite(Vector3 o, Vector3 d, Vector3 min, Vector3 max)
    {
        float tmin = 0f, tmax = 1f;
        for (int a = 0; a < 3; a++)
        {
            float oa = a == 0 ? o.X : (a == 1 ? o.Y : o.Z);
            float da = a == 0 ? d.X : (a == 1 ? d.Y : d.Z);
            float lo = a == 0 ? min.X : (a == 1 ? min.Y : min.Z);
            float hi = a == 0 ? max.X : (a == 1 ? max.Y : max.Z);
            if (Math.Abs(da) < 1e-9f)
            {
                if (oa < lo || oa > hi) return false;
            }
            else
            {
                float t1 = (lo - oa) / da;
                float t2 = (hi - oa) / da;
                if (t1 > t2) { float s = t1; t1 = t2; t2 = s; }
                if (t1 > tmin) tmin = t1;
                if (t2 < tmax) tmax = t2;
                if (tmin > tmax) return false;
            }
        }
        return true;
    }

    private static Bloc Construire(SoulsFormats.FLVER2 f, int i)
    {
        var m = f.Meshes[i];
        var b = new Bloc();
        Vector3 mn = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue);
        Vector3 mx = new Vector3(float.MinValue, float.MinValue, float.MinValue);
        for (int k = 0; k < m.Vertices.Count; k++)
        {
            Vector3 p = m.Vertices[k].Position;
            if (p.X < mn.X) mn.X = p.X;
            if (p.Y < mn.Y) mn.Y = p.Y;
            if (p.Z < mn.Z) mn.Z = p.Z;
            if (p.X > mx.X) mx.X = p.X;
            if (p.Y > mx.Y) mx.Y = p.Y;
            if (p.Z > mx.Z) mx.Z = p.Z;
        }
        b.Min = mn;
        b.Max = mx;
        if (m.FaceSets.Count > 0)
        {
            var idx = m.FaceSets[0].Indices;
            for (int k = 0; k + 2 < idx.Count; k += 3)
            {
                var t = new Tri();
                t.A = m.Vertices[idx[k]].Position;
                t.B = m.Vertices[idx[k + 1]].Position;
                t.C = m.Vertices[idx[k + 2]].Position;
                t.Maillage = i;
                b.Triangles.Add(t);
            }
        }
        return b;
    }

    private static bool Croisent(Bloc a, Bloc b)
    {
        return !(a.Max.X < b.Min.X || a.Min.X > b.Max.X
              || a.Max.Y < b.Min.Y || a.Min.Y > b.Max.Y
              || a.Max.Z < b.Min.Z || a.Min.Z > b.Max.Z);
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage: FlverVisib.exe modele.flver [cibles=4,5] [dist=3] [echantillons=120]");
            return 2;
        }
        string chemin = args[0];
        string[] morceaux = (args.Length > 1 ? args[1] : "4,5").Split(',');
        int[] cibles = new int[morceaux.Length];
        for (int i = 0; i < morceaux.Length; i++) cibles[i] = int.Parse(morceaux[i], CultureInfo.InvariantCulture);
        float dist = args.Length > 2 ? float.Parse(args[2], CultureInfo.InvariantCulture) : 3f;
        int echant = args.Length > 3 ? int.Parse(args[3], CultureInfo.InvariantCulture) : 120;

        FLVER2 f = FLVER2.Read(chemin);
        int nm = f.Meshes.Count;
        Console.WriteLine("fichier : " + chemin + "   maillages : " + nm);

        var blocs = new Bloc[nm];
        for (int i = 0; i < nm; i++) blocs[i] = Construire(f, i);

        // 26 directions
        var dirs = new List<Vector3>();
        var noms = new List<string>();
        for (int x = -1; x <= 1; x++)
            for (int y = -1; y <= 1; y++)
                for (int z = -1; z <= 1; z++)
                {
                    if (x == 0 && y == 0 && z == 0) continue;
                    dirs.Add(Vector3.Normalize(new Vector3(x, y, z)));
                    noms.Add((x == 0 ? "" : (x > 0 ? "+X" : "-X")) + (y == 0 ? "" : (y > 0 ? "+Y" : "-Y"))
                             + (z == 0 ? "" : (z > 0 ? "+Z" : "-Z")));
                }

        foreach (int cible in cibles)
        {
            var b = blocs[cible];
            Vector3 centre = (b.Min + b.Max) * 0.5f;
            Console.WriteLine();
            Console.WriteLine(string.Format(CultureInfo.InvariantCulture,
                "=== cible maillage {0} : {1} sommets, {2} triangles, boite ({3:0.###},{4:0.###},{5:0.###})..({6:0.###},{7:0.###},{8:0.###})",
                cible, f.Meshes[cible].Vertices.Count, b.Triangles.Count,
                b.Min.X, b.Min.Y, b.Min.Z, b.Max.X, b.Max.Y, b.Max.Z));

            // occultants = maillages dont la boite croise celle de la cible
            var occultants = new List<int>();
            for (int i = 0; i < nm; i++)
                if (i != cible && b.Triangles.Count > 0 && Croisent(blocs[i], b)) occultants.Add(i);
            Console.Write("occultants possibles :");
            foreach (int i in occultants) Console.Write(" " + i);
            Console.WriteLine();

            // echantillon de sommets
            var ech = new List<int>();
            int pas = Math.Max(1, f.Meshes[cible].Vertices.Count / echant);
            for (int k = 0; k < f.Meshes[cible].Vertices.Count; k += pas) ech.Add(k);
            nSommets = ech.Count;

            var vu = new int[ech.Count];
            var blocages = new Dictionary<int, int>();
            var parDirection = new int[dirs.Count];

            for (int di = 0; di < dirs.Count; di++)
            {
                Vector3 cam = centre + dirs[di] * dist;
                for (int e = 0; e < ech.Count; e++)
                {
                    Vector3 sommet = f.Meshes[cible].Vertices[ech[e]].Position;
                    Vector3 d = sommet - cam;
                    bool cache = false;
                    int qui = -1;
                    foreach (int i in occultants)
                    {
                        if (!CroiseBoite(cam, d, blocs[i].Min, blocs[i].Max)) continue;
                        foreach (Tri t in blocs[i].Triangles)
                        {
                            float tt;
                            if (RayonTriangle(cam, d, t, out tt)) { cache = true; qui = i; break; }
                        }
                        if (cache) break;
                    }
                    if (cache)
                    {
                        int v;
                        blocages.TryGetValue(qui, out v);
                        blocages[qui] = v + 1;
                    }
                    else
                    {
                        vu[e]++;
                        parDirection[di]++;
                    }
                }
            }

            Console.WriteLine();
            Console.WriteLine(string.Format(CultureInfo.InvariantCulture, "{0,-8} {1,10} {2,10}", "direction", "visibles", "%"));
            for (int di = 0; di < dirs.Count; di++)
            {
                Console.WriteLine(string.Format(CultureInfo.InvariantCulture, "{0,-8} {1,10} {2,9:0.#}%",
                    noms[di], parDirection[di], 100.0 * parDirection[di] / Math.Max(1, nSommets)));
            }
            int jamais = 0, toujours = 0;
            foreach (int v in vu)
            {
                if (v == 0) jamais++;
                if (v == dirs.Count) toujours++;
            }
            Console.WriteLine();
            Console.WriteLine(string.Format(CultureInfo.InvariantCulture,
                "sommets jamais vus depuis AUCUNE direction : {0}/{1} ({2:0.#}%)",
                jamais, ech.Count, 100.0 * jamais / Math.Max(1, ech.Count)));
            Console.WriteLine(string.Format(CultureInfo.InvariantCulture,
                "sommets vus depuis TOUTES les directions   : {0}/{1} ({2:0.#}%)",
                toujours, ech.Count, 100.0 * toujours / Math.Max(1, ech.Count)));
            Console.WriteLine("maillages qui occultent :");
            var liste = new List<KeyValuePair<int, int>>(blocages);
            liste.Sort(delegate (KeyValuePair<int, int> a, KeyValuePair<int, int> c)
            {
                return c.Value.CompareTo(a.Value);
            });
            foreach (var kv in liste)
            {
                var om = f.Meshes[kv.Key];
                string mat = om.MaterialIndex < f.Materials.Count ? f.Materials[om.MaterialIndex].Name : "?";
                string noeud = "";
                if (om.NodeIndex >= 0 && om.NodeIndex < f.Nodes.Count) noeud = f.Nodes[om.NodeIndex].Name;
                Console.WriteLine(string.Format(CultureInfo.InvariantCulture,
                    "   maillage {0,2} ({1,6} rayons bloques)  mat {2} {3}  noeud {4}",
                    kv.Key, kv.Value, om.MaterialIndex, mat, noeud));
            }
        }
        return 0;
    }

    private static int nSommets = 0;
}
