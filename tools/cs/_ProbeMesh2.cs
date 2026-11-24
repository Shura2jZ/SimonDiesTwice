using System;using System.Collections;using System.Reflection;
class P {
  static void Main(string[] a) {
    var asm = Assembly.LoadFrom(a[1]);
    var t = asm.GetType("SoulsFormats.FLVER2+Mesh");
    Console.WriteLine("=== membres de FLVER2.Mesh contenant 'Bone' ou 'Index' ou 'Vert' ===");
    foreach (var m in t.GetMembers(BindingFlags.Public|BindingFlags.Instance))
      Console.WriteLine("   " + m.MemberType + " " + m.Name + "   " + (m as PropertyInfo != null ? ((PropertyInfo)m).PropertyType.ToString() : (m as FieldInfo != null ? ((FieldInfo)m).FieldType.ToString() : "")));
    var vb = asm.GetType("SoulsFormats.FLVER2+VertexBuffer");
    Console.WriteLine("=== membres de FLVER2.VertexBuffer ===");
    if (vb != null) foreach (var m in vb.GetMembers(BindingFlags.Public|BindingFlags.Instance))
      Console.WriteLine("   " + m.MemberType + " " + m.Name + "   " + (m as PropertyInfo != null ? ((PropertyInfo)m).PropertyType.ToString() : (m as FieldInfo != null ? ((FieldInfo)m).FieldType.ToString() : "")));
  }
}
