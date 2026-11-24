// FlverMembres - introspection : liste les membres publics du type FLVER2 du DLL
// SoulsFormats reellement utilise pour lire/ecrire nos FLVER, ainsi que ses types
// imbriques. Sert a savoir si le bloc specifique a Sekiro ("SekiroUnk") est
// compris (champs typés, offsets recalcules) ou recopie tel quel (octets bruts,
// donc offsets absolus figés).
//
// Usage : FlverMembres.exe
using System;
using System.Linq;
using System.Reflection;
using SoulsFormats;

internal static class FlverMembres
{
    private static int Main(string[] args)
    {
        Type t = typeof(FLVER2);
        Console.WriteLine("assembly : " + t.Assembly.FullName);
        Console.WriteLine("emplacement : " + t.Assembly.Location);
        Console.WriteLine();
        Console.WriteLine("=== proprietes / champs d'instance de FLVER2 ===");
        foreach (var p in t.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance).OrderBy(p => p.Name))
            Console.WriteLine("  " + (p.GetMethod != null && p.GetMethod.IsPublic ? "pub " : "int ") + p.PropertyType.Name + "  " + p.Name);
        Console.WriteLine();
        Console.WriteLine("=== types imbriques de FLVER2 ===");
        foreach (var n in t.GetNestedTypes(BindingFlags.Public | BindingFlags.NonPublic).OrderBy(n => n.Name))
            Console.WriteLine("  " + n.Name);
        return 0;
    }
}
