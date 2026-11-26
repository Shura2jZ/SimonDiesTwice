// Sonde 2 : liste toutes les methodes statiques de FLVER2 et de sa classe de base
// FLVER, puis teste le type de matrice renvoye par Node.ComputeLocalTransform().
// Usage : NodeProbe2.exe SoulsFormats.dll modele.flver
using System;
using System.Collections;
using System.Linq;
using System.Reflection;

internal static class NodeProbe2
{
    private static string Sig(MethodInfo m)
    {
        return (m.IsStatic ? "stat " : "inst ") + m.ReturnType.Name + " " + m.Name
            + "(" + string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name).ToArray()) + ")";
    }

    private static int Main(string[] args)
    {
        Assembly asm = Assembly.LoadFrom(args[0]);
        string flverPath = args[1];

        Type f2 = asm.GetType("SoulsFormats.FLVER2");
        Type fbase = asm.GetType("SoulsFormats.FLVER");
        Console.WriteLine("=== FLVER2 : methodes statiques ===");
        foreach (var m in f2.GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.FlattenHierarchy)
                            .OrderBy(x => x.Name)) Console.WriteLine("    " + Sig(m));
        Console.WriteLine("=== FLVER : methodes statiques ===");
        foreach (var m in fbase.GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
                            .OrderBy(x => x.Name)) Console.WriteLine("    " + Sig(m));

        MethodInfo read = f2.GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.FlattenHierarchy)
            .FirstOrDefault(x => x.Name == "Read" && x.GetParameters().Length == 1 && x.GetParameters()[0].ParameterType == typeof(string));
        if (read == null) { Console.WriteLine("!! pas de Read(string) sur FLVER2"); return 3; }
        Console.WriteLine("Read trouve : declare dans " + read.DeclaringType.FullName + " -> " + Sig(read));
        object flver = read.Invoke(null, new object[] { flverPath });

        Type nodeType = asm.GetType("SoulsFormats.FLVER+Node");
        object first = null;
        foreach (object n in (IEnumerable)f2.GetProperty("Nodes").GetValue(flver, null)) { first = n; break; }

        object mat = nodeType.GetMethod("ComputeLocalTransform").Invoke(first, null);
        Console.WriteLine();
        Console.WriteLine("=== ComputeLocalTransform ===");
        Console.WriteLine("    type     : " + mat.GetType().FullName);
        Console.WriteLine("    assembly : " + mat.GetType().Assembly.GetName().Name);
        foreach (var f in mat.GetType().GetFields(BindingFlags.Public | BindingFlags.Instance))
            Console.WriteLine("    field " + f.FieldType.Name + " " + f.Name);
        Console.WriteLine("    valeur   : " + mat);
        return 0;
    }
}
