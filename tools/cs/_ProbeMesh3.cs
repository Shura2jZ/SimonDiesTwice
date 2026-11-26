using System;using System.Reflection;
class P {
  static void Un(string nom) {
    var t = typeof(SoulsFormats.FLVER2).Assembly.GetType(nom);
    Console.WriteLine("== " + nom + (t == null ? "   (ABSENT)" : ""));
    if (t == null) return;
    foreach (var m in t.GetMembers(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.DeclaredOnly)) {
      string ty = "";
      if (m is FieldInfo) ty = ((FieldInfo)m).FieldType.Name;
      else if (m is PropertyInfo) ty = ((PropertyInfo)m).PropertyType.Name;
      else continue;
      if (m.Name.Contains("k__BackingField")) continue;
      Console.WriteLine("     " + ty + "  " + m.Name);
    }
  }
  static void Main() {
    Un("SoulsFormats.FLVER2+Mesh");
    Un("SoulsFormats.FLVER2+FaceSet");
    Un("SoulsFormats.FLVER2+VertexBuffer");
    Un("SoulsFormats.FLVER2+BufferLayout");
    Un("SoulsFormats.FLVER2+Material");
    Un("SoulsFormats.FLVER2+SkeletonSet");
    Un("SoulsFormats.FLVER2+SkeletonSet+Bone");
    Un("SoulsFormats.FLVER+Node");
    Un("SoulsFormats.FLVER+Vertex");
  }
}
