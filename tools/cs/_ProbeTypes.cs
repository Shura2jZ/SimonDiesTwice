using System;using System.Reflection;
class P {
  static void Main(string[] a) {
    var asm = Assembly.LoadFrom(a[0]);
    foreach (var nom in new string[]{"SoulsFormats.FLVER2","SoulsFormats.FLVER2+Texture","SoulsFormats.FLVER+VertexBoneWeights"}) {
      var t = asm.GetType(nom);
      Console.WriteLine("== " + nom + (t == null ? "  (ABSENT)" : ""));
      if (t == null) continue;
      foreach (var m in t.GetMembers(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.DeclaredOnly)) {
        string ty = "";
        if (m is FieldInfo) ty = ((FieldInfo)m).FieldType.Name;
        else if (m is PropertyInfo) ty = ((PropertyInfo)m).PropertyType.Name;
        else continue;
        Console.WriteLine("     " + ty + "  " + m.Name);
      }
    }
  }
}
