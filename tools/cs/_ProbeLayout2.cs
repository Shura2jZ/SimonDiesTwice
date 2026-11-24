using System;
using System.Linq;
using System.Reflection;
using SoulsFormats;
internal static class P2 {
  private static int Main() {
    Type t = typeof(FLVER.LayoutMember);
    Console.WriteLine("=== " + t.FullName + " ===");
    foreach (var p in t.GetProperties(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)) Console.WriteLine("  prop " + p.PropertyType.FullName + "  " + p.Name);
    Console.WriteLine();
    FLVER2 f = FLVER2.Read(@"C:\Users\marou\Documents\Default Project\_work\extracted\c5400.chrbnd\c5400.flver");
    for (int i = 0; i < f.BufferLayouts.Count; i++) {
      var bl = f.BufferLayouts[i];
      Console.WriteLine("agencement[" + i + "] taille=" + bl.Size + " membres=" + bl.Count);
      foreach (var m in bl) {
        var sb = new System.Text.StringBuilder("   ");
        foreach (var q in m.GetType().GetProperties(BindingFlags.Public|BindingFlags.Instance)) { object v; try { v = q.GetValue(m, null); } catch { v = "?"; } sb.Append(q.Name + "=" + v + "  "); }
        Console.WriteLine(sb.ToString().TrimEnd());
      }
      Console.WriteLine();
    }
    return 0;
  }
}
