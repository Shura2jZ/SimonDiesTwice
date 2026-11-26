// FlverChamps - affiche par reflexion TOUS les champs et proprietes de chaque
// maillage (et de ses facesets / tampons de sommets) d'un FLVER.
// But : comparer le fichier vanille et notre fichier quand on ne sait plus quoi
// regarder -- un champ oublie est un champ suspect.
//
// Usage : FlverChamps.exe modele.flver [i0 i1 ...]
using System;
using System.Collections;
using System.Reflection;
using System.Text;
using SoulsFormats;

internal static class FlverChamps
{
    private static string Val(object o)
    {
        if (o == null) return "null";
        IFormattable fo = o as IFormattable;
        if (o is float || o is double) return ((IFormattable)o).ToString(null, System.Globalization.CultureInfo.InvariantCulture);
        if (o is string) return (string)o;
        ICollection c = o as ICollection;
        if (c != null) return "<" + o.GetType().Name + " n=" + c.Count + ">";
        return o.ToString();
    }

    private static void Ligne(object o, string prefixe)
    {
        Type t = o.GetType();
        var sb = new StringBuilder();
        foreach (PropertyInfo p in t.GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            if (p.GetIndexParameters().Length > 0) continue;
            object v; try { v = p.GetValue(o, null); } catch { v = "!"; }
            sb.Append(p.Name).Append('=').Append(Val(v)).Append("  ");
        }
        foreach (FieldInfo fi in t.GetFields(BindingFlags.Public | BindingFlags.Instance))
        {
            object v; try { v = fi.GetValue(o); } catch { v = "!"; }
            sb.Append(fi.Name).Append('=').Append(Val(v)).Append("  ");
        }
        Console.WriteLine(prefixe + sb.ToString().TrimEnd());
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverChamps.exe modele.flver [i0 i1 ...]"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("types : Mesh=" + typeof(FLVER2.Mesh).FullName
                          + "  FaceSet=" + typeof(FLVER2.FaceSet).FullName
                          + "  VertexBuffer=" + typeof(FLVER2.VertexBuffer).FullName);
        int[] cibles;
        if (args.Length > 1)
        {
            cibles = new int[args.Length - 1];
            for (int i = 1; i < args.Length; i++) cibles[i - 1] = int.Parse(args[i]);
        }
        else
        {
            cibles = new int[f.Meshes.Count];
            for (int i = 0; i < cibles.Length; i++) cibles[i] = i;
        }
        foreach (int i in cibles)
        {
            if (i < 0 || i >= f.Meshes.Count) continue;
            FLVER2.Mesh m = f.Meshes[i];
            Console.WriteLine();
            Console.WriteLine("maillage [" + i + "]");
            Ligne(m, "   M  ");
            foreach (FLVER2.VertexBuffer vb in m.VertexBuffers)
                Ligne(vb, "   VB ");
            int k = 0;
            foreach (FLVER2.FaceSet fs in m.FaceSets)
            {
                Ligne(fs, "   FS" + k + " ");
                k++;
            }
            Console.WriteLine("   (sommets " + m.Vertices.Count + ")");
        }
        return 0;
    }
}
