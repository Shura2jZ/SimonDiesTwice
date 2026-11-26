using System;using System.Reflection;
class P {
  static void Det(Type t) {
    if (t == null) { Console.WriteLine("   (type absents)"); return; }
    Console.WriteLine("== " + t.FullName + "   base = " + (t.BaseType == null ? "-" : t.BaseType.FullName));
    foreach (var m in t.GetMembers(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.Static)) {
      if (m.DeclaringType != t) continue;
      string ty = "";
      if (m is FieldInfo) ty = ((FieldInfo)m).FieldType.Name;
      else if (m is PropertyInfo) ty = ((PropertyInfo)m).PropertyType.Name;
      else continue;
      if (m.Name.Contains("k__BackingField")) continue;
      Console.WriteLine("     " + ty + "  " + m.Name);
    }
  }
  static void Main() {
    var asm = typeof(SoulsFormats.FLVER2).Assembly;
    Det(typeof(SoulsFormats.FLVER2).GetNestedType("BufferLayout", BindingFlags.Public|BindingFlags.NonPublic));
    Det(asm.GetType("SoulsFormats.FLVER+BufferLayout"));
    Det(asm.GetType("SoulsFormats.FLVER+LayoutMember"));
    Det(asm.GetType("SoulsFormats.LayoutType"));
    Det(asm.GetType("SoulsFormats.FLVER+LayoutType"));
    // membres declares dans FLVER2.BufferLayout, herite compris
    var bl = typeof(SoulsFormats.FLVER2).GetNestedType("BufferLayout", BindingFlags.Public|BindingFlags.NonPublic);
    Console.WriteLine("== tous les membres vus depuis " + bl.FullName);
    foreach (var m in bl.GetMembers(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)) {
      string ty = "";
      if (m is FieldInfo) ty = ((FieldInfo)m).FieldType.Name;
      else if (m is PropertyInfo) ty = ((PropertyInfo)m).PropertyType.Name;
      else continue;
      if (m.Name.Contains("k__BackingField")) continue;
      Console.WriteLine("     " + ty + "  " + m.Name + "   (declare dans " + m.DeclaringType.Name + ")");
    }
  }
}
