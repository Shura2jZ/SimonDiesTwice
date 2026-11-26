// Affiche l'API publique des types FLVER2 de SoulsFormats (noms exacts des champs
// et proprietes), pour ecrire nos outils sans deviner.
// Compile par tools\cs_build.ps1, execute par tools\cs_run.ps1.
using System;
using System.Linq;
using System.Reflection;

internal static class DumpApi
{
    private static void Dump(Type t, int depth)
    {
        string pad = new string(' ', depth * 2);
        Console.WriteLine(pad + "== " + t.FullName + (t.IsEnum ? " (enum)" : ""));
        if (t.IsEnum)
        {
            foreach (string n in Enum.GetNames(t)) Console.WriteLine(pad + "   " + n + " = " + Convert.ToInt64(Enum.Parse(t, n)));
            return;
        }
        foreach (var f in t.GetFields(BindingFlags.Public | BindingFlags.Instance).OrderBy(x => x.Name))
            Console.WriteLine(pad + "   field " + Short(f.FieldType) + "  " + f.Name);
        foreach (var p in t.GetProperties(BindingFlags.Public | BindingFlags.Instance).OrderBy(x => x.Name))
        {
            string acc = (p.CanRead ? "get" : "") + (p.CanWrite ? "/set" : "");
            Console.WriteLine(pad + "   prop  " + Short(p.PropertyType) + "  " + p.Name + "  [" + acc + "]");
        }
        foreach (var m in t.GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly).OrderBy(x => x.Name))
            Console.WriteLine(pad + "   stat  " + Short(m.ReturnType) + "  " + m.Name + "(" + string.Join(", ", m.GetParameters().Select(x => Short(x.ParameterType) + " " + x.Name).ToArray()) + ")");
        foreach (var m in t.GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly)
                              .Where(x => !x.IsSpecialName).OrderBy(x => x.Name))
            Console.WriteLine(pad + "   meth  " + Short(m.ReturnType) + "  " + m.Name + "(" + string.Join(", ", m.GetParameters().Select(x => Short(x.ParameterType) + " " + x.Name).ToArray()) + ")");
        if (depth > 0)
        {
            foreach (var n in t.GetNestedTypes(BindingFlags.Public).OrderBy(x => x.Name))
                if (!n.IsEnum || n.Name.ToLower().Contains("flag")) Dump(n, depth - 1);
        }
    }

    private static string Short(Type t)
    {
        if (t == null) return "?";
        if (t.IsGenericType)
            return t.Name.Split('`')[0] + "<" + string.Join(",", t.GetGenericArguments().Select(Short).ToArray()) + ">";
        return t.Name;
    }

    private static int Main(string[] args)
    {
        Assembly asm = Assembly.LoadFrom(args.Length > 0 ? args[0] : "SoulsFormats.dll");

        if (args.Length > 1)
        {
            // mode filtre : dump les types dont le nom contient l'un des arguments
            foreach (var t in asm.GetTypes().Where(x => args.Skip(1).Any(f => x.Name.Contains(f))).OrderBy(x => x.FullName))
                Dump(t, 0);
            return 0;
        }

        Type flver2 = asm.GetType("SoulsFormats.FLVER2");
        Dump(flver2, 1);
        Console.WriteLine();
        Console.WriteLine("=== methodes statiques de FLVER2 ===");
        foreach (var m in flver2.GetMethods(BindingFlags.Public | BindingFlags.Static).OrderBy(x => x.Name))
            Console.WriteLine("    " + Short(m.ReturnType) + " " + m.Name + "(" + string.Join(", ", m.GetParameters().Select(x => Short(x.ParameterType) + " " + x.Name).ToArray()) + ")");
        return 0;
    }
}
