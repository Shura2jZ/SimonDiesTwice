using System;
using System.Linq;
using System.Reflection;
using SoulsFormats;
internal static class P {
  private static int Main() {
    Type t = typeof(FLVER2.BufferLayout);
    Console.WriteLine("=== " + t.FullName + " ===");
    foreach (var p in t.GetProperties(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)) Console.WriteLine("  prop " + p.PropertyType.FullName + "  " + p.Name);
    foreach (var fi in t.GetFields(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)) Console.WriteLine("  champ " + fi.FieldType.FullName + "  " + fi.Name);
    Console.WriteLine();
    Console.WriteLine("=== types imbriques de BufferLayout ===");
    foreach (var n in t.GetNestedTypes(BindingFlags.Public|BindingFlags.NonPublic)) Console.WriteLine("  " + n.FullName);
    Console.WriteLine();
    Console.WriteLine("=== FLVER2 nested (filtre) ===");
    foreach (var n in typeof(FLVER2).GetNestedTypes(BindingFlags.Public|BindingFlags.NonPublic)) if (n.Name.ToLower().Contains("layout") || n.Name.ToLower().Contains("member")) Console.WriteLine("  " + n.FullName);
    return 0;
  }
}
