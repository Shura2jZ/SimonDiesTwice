using System;
using System.Linq;
using System.Reflection;
using SoulsFormats;
internal static class P3 {
  private static int Main() {
    Type t = typeof(FLVER.VertexColor);
    Console.WriteLine("=== " + t.FullName + " ===");
    Console.WriteLine("-- champs --");
    foreach (var f in t.GetFields(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)) Console.WriteLine("   " + f.FieldType.Name + "  " + f.Name);
    Console.WriteLine("-- proprietes --");
    foreach (var q in t.GetProperties(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)) Console.WriteLine("   " + q.PropertyType.Name + "  " + q.Name);
    Console.WriteLine("-- constructeurs --");
    foreach (var c in t.GetConstructors()) Console.WriteLine("   (" + string.Join(", ", c.GetParameters().Select(x => x.ParameterType.Name + " " + x.Name)) + ")");
    return 0;
  }
}
