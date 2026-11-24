// TaeInfo - premier contact avec les fichiers .tae (evenements d'animation)
// via SoulsFormats. Affiche la forme de l'objet obtenu, puis agrege les types
// d'evenements et les petits arguments entiers, pour reperer les evenements
// qui referencent un indice de maillage (valeur 0..32).
//
// Le compilateur disponible est celui du framework 4.0 (C# 5) : syntaxe
// volontairement conservatrice.
//
// Usage : TaeInfo.exe <fichier.tae> [--detail]
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection;
using SoulsFormats;

internal static class TaeInfo
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static object Champ(object o, string nom)
    {
        if (o == null) return null;
        Type t = o.GetType();
        PropertyInfo p = t.GetProperty(nom, BindingFlags.Public | BindingFlags.Instance);
        if (p == null)
            p = t.GetProperty(nom, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
        if (p == null) return null;
        try { return p.GetValue(o, null); }
        catch { return null; }
    }

    private static IEnumerable Aplati(object v)
    {
        if (v == null) return null;
        ICollection c = v as ICollection;
        if (c != null) return c;
        Array a = v as Array;
        if (a != null) return a;
        IEnumerable e = v as IEnumerable;
        return e;
    }

    private static string TypeMembres(object o)
    {
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        PropertyInfo[] props = o.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance);
        foreach (PropertyInfo p in props)
        {
            object v;
            try { v = p.GetValue(o, null); }
            catch { continue; }
            ICollection c = v as ICollection;
            if (c != null) sb.Append(p.Name).Append('[').Append(c.Count).Append("] ");
            else sb.Append(p.Name).Append('=').Append(v).Append(' ');
        }
        return sb.ToString().Trim();
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage: TaeInfo.exe <fichier.tae> [--detail]");
            return 2;
        }
        bool detail = args.Length > 1 && args[1] == "--detail";

        object tae;
        try
        {
            System.Reflection.Assembly asm = typeof(FLVER2).Assembly;
            Type taeType = asm.GetType("SoulsFormats.TAE3", false);
            if (taeType == null) taeType = asm.GetType("SoulsFormats.TAE", true);
            MethodInfo read = null;
            foreach (MethodInfo candidate in taeType.GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.FlattenHierarchy))
            {
                ParameterInfo[] parameters = candidate.GetParameters();
                if (candidate.Name == "Read" && parameters.Length == 1 &&
                    parameters[0].ParameterType == typeof(string)) { read = candidate; break; }
            }
            if (read == null) throw new MissingMethodException(taeType.FullName, "Read(string)");
            tae = read.Invoke(null, new object[] { args[0] });
        }
        catch (Exception e) { Console.WriteLine("TAE.Read a echoue : " + e.GetBaseException().Message); return 1; }

        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("type    : " + tae.GetType().FullName);
        Console.WriteLine();
        Console.WriteLine("=== proprietes racine ===");
        PropertyInfo[] racine = tae.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance);
        foreach (PropertyInfo p in racine)
        {
            object v;
            try { v = p.GetValue(tae, null); }
            catch { continue; }
            ICollection c = v as ICollection;
            Console.WriteLine("  " + p.Name + " : " + (c != null ? c.Count + " elements" : (v == null ? "null" : v.ToString())));
        }

        object animations = Champ(tae, "Animations");
        IEnumerable listeAnim = Aplati(animations);
        if (listeAnim == null)
        {
            Console.WriteLine("(pas de liste d'animations)");
            return 0;
        }

        int nbAnim = 0;
        SortedDictionary<int, int> comptes = new SortedDictionary<int, int>();
        SortedDictionary<int, int> petits = new SortedDictionary<int, int>();
        Dictionary<int, List<string>> exemples = new Dictionary<int, List<string>>();

        foreach (object anim in listeAnim)
        {
            nbAnim++;
            IEnumerable listeEv = Aplati(Champ(anim, "Events"));
            if (listeEv == null) continue;
            foreach (object ev in listeEv)
            {
                object t = Champ(ev, "Type");
                int type = (t == null) ? -1 : Convert.ToInt32(t, Inv);
                if (!comptes.ContainsKey(type))
                {
                    comptes[type] = 0;
                    exemples[type] = new List<string>();
                }
                comptes[type]++;
                if (exemples[type].Count < 3) exemples[type].Add(TypeMembres(ev));

                // arguments : on fouille les collections de parametres/args
                string[] candidats = new string[] { "Parameters", "Args", "Arguments", "Params" };
                foreach (string nom in candidats)
                {
                    IEnumerable listeP = Aplati(Champ(ev, nom));
                    if (listeP == null) continue;
                    foreach (object par in listeP)
                    {
                        object val = par;
                        object v2 = Champ(par, "Value");
                        if (v2 != null) val = v2;
                        if (val is int)
                        {
                            int iv = (int)val;
                            if (iv >= 0 && iv <= 32)
                            {
                                if (!petits.ContainsKey(type)) petits[type] = 0;
                                petits[type]++;
                            }
                        }
                    }
                }
            }
        }

        Console.WriteLine();
        Console.WriteLine("animations : " + nbAnim);
        Console.WriteLine();
        Console.WriteLine("=== types d'evenements (occurrences, dont arguments entiers 0..32) ===");
        List<KeyValuePair<int, int>> ordre = comptes.ToList();
        ordre.Sort(delegate(KeyValuePair<int, int> a, KeyValuePair<int, int> b) { return b.Value.CompareTo(a.Value); });
        foreach (KeyValuePair<int, int> kv in ordre)
        {
            int type = kv.Key;
            int petit = petits.ContainsKey(type) ? petits[type] : 0;
            Console.WriteLine(string.Format(Inv, "  type {0,4} {1,8} occurrences   args 0..32 : {2}",
                type, kv.Value, petit));
        }

        if (detail)
        {
            Console.WriteLine();
            Console.WriteLine("=== exemples ===");
            foreach (KeyValuePair<int, List<string>> kv in exemples)
            {
                foreach (string e in kv.Value)
                    Console.WriteLine("  type " + kv.Key + " : " + e);
            }
        }
        return 0;
    }
}
