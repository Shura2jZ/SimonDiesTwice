// FlverTout - dump REFLEXIF complet d'un FLVER : tous les membres publics
// (proprietes ET champs) que SoulsFormats expose, y compris ceux que nos autres
// sondes ne regardent pas. But : reperer un champ qui differe entre la vanille et
// notre build sans qu'on l'ait jamais compare.
//
// Usage : FlverTout.exe modele.flver [idxMaillage...]
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Numerics;
using System.Reflection;
using SoulsFormats;

internal static class FlverTout
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static string Res(object o)
    {
        if (o == null) return "null";
        Type t = o.GetType();
        if (o is string) return "\"" + o + "\"";
        if (o is bool || o is int || o is short || o is byte || o is sbyte
            || o is uint || o is ushort || o is long || o is ulong || o is float || o is double)
            return Convert.ToString(o, Inv);
        if (o is Vector2) { Vector2 v = (Vector2)o; return string.Format(Inv, "({0:G6} {1:G6})", v.X, v.Y); }
        if (o is Vector3) { Vector3 v = (Vector3)o; return string.Format(Inv, "({0:G6} {1:G6} {2:G6})", v.X, v.Y, v.Z); }
        if (o is Vector4) { Vector4 v = (Vector4)o; return string.Format(Inv, "({0:G6} {1:G6} {2:G6} {3:G6})", v.X, v.Y, v.Z, v.W); }
        if (o is Matrix4x4) { Matrix4x4 m = (Matrix4x4)o; return string.Format(Inv, "T({0:G6} {1:G6} {2:G6})", m.M41, m.M42, m.M43); }
        if (o is ICollection) return "<" + t.Name + " n=" + ((ICollection)o).Count + ">";
        if (o is IEnumerable) return "<" + t.Name + ">";
        return "<" + t.Name + ">";
    }

    private static void Dump(string prefix, object o, int depth, int maxDepth)
    {
        if (o == null) { Console.WriteLine(prefix + " = null"); return; }
        Type t = o.GetType();
        string simple = Res(o);
        if (simple[0] == '<' && simple.EndsWith(">"))
        {
            Console.WriteLine(prefix + " = " + simple);
            if (depth >= maxDepth) return;
            // on ne descend que dans les types SoulsFormats
            if (!t.FullName.StartsWith("SoulsFormats")) return;
            List<string> enfants = new List<string>();
            foreach (PropertyInfo p in t.GetProperties(BindingFlags.Public | BindingFlags.Instance))
            {
                if (p.GetIndexParameters().Length != 0) continue;
                object v = null;
                try { v = p.GetValue(o); } catch { continue; }
                Dump(prefix + "." + p.Name, v, depth + 1, maxDepth);
            }
            foreach (FieldInfo fi in t.GetFields(BindingFlags.Public | BindingFlags.Instance))
            {
                object v = null;
                try { v = fi.GetValue(o); } catch { continue; }
                Dump(prefix + "." + fi.Name, v, depth + 1, maxDepth);
            }
            if (t.IsGenericType && t.GetGenericArguments().Length == 1
                && typeof(IEnumerable).IsAssignableFrom(t))
            {
                int k = 0;
                foreach (object el in (IEnumerable)o)
                {
                    Dump(prefix + "[" + k + "]", el, depth + 1, maxDepth);
                    if (++k >= 4) { Console.WriteLine(prefix + "..."); break; }
                }
            }
            return;
        }
        Console.WriteLine(prefix + " = " + simple);
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverTout.exe modele.flver [idxMaillage...]"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine();
        Console.WriteLine("########## NIVEAU FLVER ##########");
        Dump("flver", f, 0, 1);
        Console.WriteLine();

        List<int> idx = new List<int>();
        for (int i = 1; i < args.Length; i++) idx.Add(int.Parse(args[i], Inv));
        if (idx.Count == 0) idx.Add(0);

        foreach (int mi in idx)
        {
            if (mi < 0 || mi >= f.Meshes.Count) continue;
            Console.WriteLine("########## MAILLAGE [" + mi + "] ##########");
            Dump("M", f.Meshes[mi], 0, 3);
            Console.WriteLine();
        }
        return 0;
    }
}
