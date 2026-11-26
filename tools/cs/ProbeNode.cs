// ProbeNode.cs -- affiche la structure de FLVER2.Node (champs disponibles).
using System;
using System.Linq;
using System.Reflection;
using SoulsFormats;

internal static class ProbeNode
{
    private static int Main(string[] args)
    {
        var t = typeof(FLVER2).Assembly.GetType("SoulsFormats.FLVER2+Node");
        if (t == null)
        {
            foreach (var ty in typeof(FLVER2).Assembly.GetTypes())
                if (ty.Name == "Node") { t = ty; break; }
        }
        Console.WriteLine("type : " + (t == null ? "?" : t.FullName));
        if (t != null)
        {
            foreach (var f in t.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
                Console.WriteLine("  champ " + f.FieldType.Name + " " + f.Name);
            foreach (var p in t.GetProperties())
                Console.WriteLine("  prop  " + p.PropertyType.Name + " " + p.Name);
        }
        return 0;
    }
}
