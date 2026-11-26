// FlverSections - liste toutes les sections de la racine d'un FLVER et leur
// taille, pour reperer une section perdue ou modifiee entre le modele
// d'origine et le modele modifie. Detaille en plus la section "skeleton"
// (FLVER2.Skeletons), jamais imprimee par les autres outils.
//
// Usage : FlverSections.exe <modele.flver>
using System;
using System.Collections;
using System.Globalization;
using System.Reflection;
using SoulsFormats;

internal static class FlverSections
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverSections.exe <modele.flver>"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine();

        Console.WriteLine("=== sections de la racine FLVER2 ===");
        foreach (PropertyInfo p in typeof(FLVER2).GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            object v;
            try { v = p.GetValue(f); } catch { continue; }
            var c = v as ICollection;
            if (c != null)
                Console.WriteLine(string.Format(Inv, "  {0,-18} {1,6} elements   ({2})",
                    p.Name, c.Count, v.GetType().Name));
            else
                Console.WriteLine(string.Format(Inv, "  {0,-18} {1}", p.Name, v));
        }
        Console.WriteLine();

        Console.WriteLine("=== section skeleton ===");
        object racineSquelette = f.Skeletons;
        if (racineSquelette == null)
        {
            Console.WriteLine("  (absente)");
        }
        else
        {
            Console.WriteLine("  type : " + racineSquelette.GetType().FullName);
            foreach (PropertyInfo q in racineSquelette.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
            {
                object w;
                try { w = q.GetValue(racineSquelette); } catch { continue; }
                var c2 = w as ICollection;
                if (c2 != null)
                {
                    Console.WriteLine("    " + q.Name + " : " + c2.Count + " elements");
                    int k = 0;
                    foreach (object e in c2)
                    {
                        if (k >= 12) { Console.WriteLine("      ... (" + (c2.Count - 12) + " de plus)"); break; }
                        Console.WriteLine("      [" + k + "] " + Decrire(e));
                        k++;
                    }
                }
                else
                {
                    Console.WriteLine("    " + q.Name + " : " + w);
                }
            }
        }
        return 0;
    }

    private static string Decrire(object e)
    {
        if (e == null) return "null";
        var t = e.GetType();
        if (t.IsPrimitive || t == typeof(string)) return e.ToString();
        var sb = new System.Text.StringBuilder();
        foreach (PropertyInfo p in t.GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            object v;
            try { v = p.GetValue(e); } catch { continue; }
            sb.Append(p.Name).Append('=').Append(v).Append(' ');
        }
        return sb.ToString().Trim();
    }
}
