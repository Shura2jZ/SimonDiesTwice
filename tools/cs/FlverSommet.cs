// FlverSommet - inspection complete d'un sommet, y compris ses champs PRIVES.
//
// Raison : dans ce fork de SoulsFormats, FLVER.Vertex.Write leve
// "InvalidOperationException: Queue empty" lorsqu'on ecrit deux fois le meme
// objet sommet. Le sommet porte donc une file interne consommee a l'ecriture.
// Si cette file contient des OCTETS BRUTS rejoues tels quels, alors le moteur
// (qui lit les octets) peut voir autre chose que mes sondes (qui lisent les
// champs decodes) -- et tous mes controles hors jeu passeraient a cote du defaut.
//
// Usage : FlverSommet.exe <flver> [emplacement] [indice]
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using SoulsFormats;

internal static class FlverSommet
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static string Decrire(object val, int max)
    {
        if (val == null) return "null";
        if (val is string) return (string)val;
        if (val is IEnumerable && !(val is Vector4Dummy))
        {
            IEnumerable e = (IEnumerable)val;
            List<string> parts = new List<string>();
            int n = 0, total = 0;
            foreach (object o in e)
            {
                total++;
                if (n < max) parts.Add(o == null ? "null" : o.ToString());
                n++;
            }
            string s = string.Join(", ", parts.ToArray());
            if (total > max) s += " ... (+" + (total - max) + ")";
            return "[" + total + "] " + s;
        }
        return val.ToString();
    }

    private sealed class Vector4Dummy { }

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverSommet.exe <flver> [emplacement] [indice]"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        int slot = args.Length > 1 ? int.Parse(args[1], Inv) : 4;
        int idx = args.Length > 2 ? int.Parse(args[2], Inv) : 0;

        object m = f.Meshes[slot];
        Type tm = m.GetType();
        IList verts = (IList)tm.GetProperty("Vertices").GetValue(m, null);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("maillage " + slot + " : " + verts.Count + " sommets, materiau "
            + tm.GetProperty("MaterialIndex").GetValue(m, null));
        object v = verts[idx];
        Type tv = v.GetType();
        Console.WriteLine("type sommet : " + tv.FullName);
        Console.WriteLine();

        FieldInfo[] champs = tv.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        Array.Sort(champs, delegate (FieldInfo a, FieldInfo b) { return string.CompareOrdinal(a.Name, b.Name); });

        foreach (FieldInfo fi in champs)
        {
            object val = null;
            try { val = fi.GetValue(v); } catch (Exception ex) { val = "<" + ex.GetType().Name + ">"; }
            Console.WriteLine("  " + (fi.IsPublic ? "PUB  " : "priv ") + fi.Name.PadRight(22)
                + " " + fi.FieldType.Name.PadRight(22) + " = " + Decrire(val, 16));
        }

        // les mêmes champs pour deux autres sommets, afin de voir ce qui varie
        foreach (int j in new int[] { 1, 2 })
        {
            if (j >= verts.Count) break;
            object w = verts[j];
            Console.WriteLine();
            Console.WriteLine("--- sommet " + j + " (champs susceptibles de varier) ---");
            foreach (FieldInfo fi in champs)
            {
                object a = null, b = null;
                try { a = fi.GetValue(v); } catch { }
                try { b = fi.GetValue(w); } catch { }
                string sa = Decrire(a, 8), sb = Decrire(b, 8);
                if (sa != sb)
                    Console.WriteLine("  " + fi.Name.PadRight(22) + "  [0]=" + sa + "   [" + j + "]=" + sb);
            }
        }

        return 0;
    }
}
