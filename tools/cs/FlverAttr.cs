// FlverAttr.exe -- statistiques des attributs de sommets d'un FLVER.
//
// Compare ce qui doit etre compare : pour chaque maillage, la plage et la
// repartition des attributs qui pilotent le rendu cote nuanceur de sommets :
//   - la couleur de sommet (souvent detournee : masque, poids de tissu, occlusion)
//   - la composante W de la normale et de la tangente (souvent un drapeau)
//   - la somme des poids d'ossature
//   - l'etendue des indices d'ossature
//
// L'idee : un attribut dont la repartition differe radicalement de celle du
// maillage d'origine portant le meme materiau est un suspect.
//
// Usage : FlverAttr.exe <fichier.flver> [liste de maillages, ex. 3,4,7]

using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using SoulsFormats;

internal static class FlverAttr
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static double Champ(object o, string nom)
    {
        if (o == null) return 0;
        FieldInfo fi = o.GetType().GetField(nom, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (fi == null) return 0;
        object v = fi.GetValue(o);
        return v == null ? 0 : Convert.ToDouble(v);
    }

    private static int Nb(object o)
    {
        if (o == null) return 0;
        PropertyInfo pi = o.GetType().GetProperty("Length", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (pi != null) return Convert.ToInt32(pi.GetValue(o, null));
        return 0;
    }

    private static double Elt(object o, int k)
    {
        PropertyInfo pi = o.GetType().GetProperty("Item", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (pi != null) return Convert.ToDouble(pi.GetValue(o, new object[] { k }));
        string nom = (new string[] { "A", "B", "C", "D" })[k];
        return Champ(o, nom);
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverAttr.exe <fichier.flver> [maillages]"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        List<int> cibles = new List<int>();
        if (args.Length > 1) { foreach (string s in args[1].Split(',')) cibles.Add(int.Parse(s)); }
        else { for (int i = 0; i < f.Meshes.Count; i++) cibles.Add(i); }

        Console.WriteLine("fichier : " + args[0]);

        foreach (int i in cibles)
        {
            if (i < 0 || i >= f.Meshes.Count) continue;
            FLVER2.Mesh m = f.Meshes[i];

            double cRmin = 1e9, cRmax = -1e9, cGmin = 1e9, cGmax = -1e9;
            double cBmin = 1e9, cBmax = -1e9, cAmin = 1e9, cAmax = -1e9;
            double sR = 0, sG = 0, sB = 0, sA = 0;
            Dictionary<int, int> nw = new Dictionary<int, int>();
            Dictionary<int, int> tw = new Dictionary<int, int>();
            Dictionary<string, int> couleurs = new Dictionary<string, int>();
            double pmin = 1e9, pmax = -1e9, pmm = 0;
            int nSansPoids = 0, osMax = 0;
            double umin = 1e9, umax = -1e9, vmin = 1e9, vmax = -1e9;
            long n = 0;

            foreach (FLVER.Vertex v in m.Vertices)
            {
                n++;
                if (v.Colors != null && v.Colors.Count > 0)
                {
                    object c = v.Colors[0];
                    double r = Champ(c, "R"), g = Champ(c, "G"), b = Champ(c, "B"), a = Champ(c, "A");
                    if (r < cRmin) cRmin = r; if (r > cRmax) cRmax = r;
                    if (g < cGmin) cGmin = g; if (g > cGmax) cGmax = g;
                    if (b < cBmin) cBmin = b; if (b > cBmax) cBmax = b;
                    if (a < cAmin) cAmin = a; if (a > cAmax) cAmax = a;
                    sR += r; sG += g; sB += b; sA += a;
                    string cle = Octet(r) + "," + Octet(g) + "," + Octet(b) + "," + Octet(a);
                    int cpt; couleurs.TryGetValue(cle, out cpt); couleurs[cle] = cpt + 1;
                }
                if (!nw.ContainsKey(v.NormalW)) nw[v.NormalW] = 0;
                nw[v.NormalW]++;

                if (v.Tangents != null && v.Tangents.Count > 0)
                {
                    int w = (int)Champ(v.Tangents[0], "W");
                    if (!tw.ContainsKey(w)) tw[w] = 0;
                    tw[w]++;
                }

                double sm = 0;
                int nbP = Nb(v.BoneWeights);
                for (int k = 0; k < nbP; k++) sm += Elt(v.BoneWeights, k);
                if (sm < pmin) pmin = sm;
                if (sm > pmax) pmax = sm;
                pmm += sm;
                if (sm < 1e-6) nSansPoids++;

                int nbI = Nb(v.BoneIndices);
                for (int k = 0; k < nbI; k++)
                {
                    int bi = (int)Elt(v.BoneIndices, k);
                    if (bi > osMax) osMax = bi;
                }

                if (v.UVs != null && v.UVs.Count > 0)
                {
                    object u = v.UVs[0];
                    double ux = Champ(u, "X"), uy = Champ(u, "Y");
                    if (ux < umin) umin = ux; if (ux > umax) umax = ux;
                    if (uy < vmin) vmin = uy; if (uy > vmax) vmax = uy;
                }
            }

            Console.WriteLine();
            Console.WriteLine("=== maillage " + i + "   materiau " + m.MaterialIndex
                              + "   sommets " + n + "   disposition "
                              + (m.VertexBuffers.Count > 0 ? m.VertexBuffers[0].LayoutIndex.ToString() : "?")
                              + "   tampons " + m.VertexBuffers.Count + " ===");
            Console.WriteLine("    couleur R : " + cRmin.ToString("0.####", Inv) + " .. " + cRmax.ToString("0.####", Inv)
                              + "   moyenne " + (sR / n).ToString("0.####", Inv));
            Console.WriteLine("    couleur G : " + cGmin.ToString("0.####", Inv) + " .. " + cGmax.ToString("0.####", Inv)
                              + "   moyenne " + (sG / n).ToString("0.####", Inv));
            Console.WriteLine("    couleur B : " + cBmin.ToString("0.####", Inv) + " .. " + cBmax.ToString("0.####", Inv)
                              + "   moyenne " + (sB / n).ToString("0.####", Inv));
            Console.WriteLine("    couleur A : " + cAmin.ToString("0.####", Inv) + " .. " + cAmax.ToString("0.####", Inv)
                              + "   moyenne " + (sA / n).ToString("0.####", Inv));
            Console.WriteLine("    couleurs distinctes (octets) : " + couleurs.Count);
            int montre = 0;
            foreach (KeyValuePair<string, int> kv in couleurs)
            {
                if (montre++ >= 6) { Console.WriteLine("        ... (" + (couleurs.Count - 6) + " autres)"); break; }
                Console.WriteLine("        (" + kv.Key + ")  x" + kv.Value);
            }
            Console.WriteLine("    W de normale  : " + Repr(nw));
            Console.WriteLine("    W de tangente : " + Repr(tw));
            Console.WriteLine("    somme des poids : " + pmin.ToString("0.#####", Inv) + " .. " + pmax.ToString("0.#####", Inv)
                              + "   moyenne " + (pmm / n).ToString("0.#####", Inv)
                              + "   sommets sans poids " + nSansPoids);
            Console.WriteLine("    indice d'os max : " + osMax);
            Console.WriteLine("    UV0 : u " + umin.ToString("0.###", Inv) + " .. " + umax.ToString("0.###", Inv)
                              + "   v " + vmin.ToString("0.###", Inv) + " .. " + vmax.ToString("0.###", Inv));
        }
        return 0;
    }

    private static int Octet(double x)
    {
        int b = (int)Math.Round(x * 255.0);
        if (b < 0) b = 0;
        if (b > 255) b = 255;
        return b;
    }

    private static string Repr(Dictionary<int, int> d)
    {
        List<int> cles = new List<int>(d.Keys);
        cles.Sort();
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        int montre = 0;
        foreach (int k in cles)
        {
            if (montre++ >= 6) { sb.Append(" ... (" + (cles.Count - 6) + " autres)"); break; }
            sb.Append(k + " (x" + d[k] + ")  ");
        }
        return sb.ToString();
    }
}
