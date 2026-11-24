using System;using System.Reflection;
class P {
  static void Affiche(Type t) {
    Console.WriteLine("== " + t.FullName + (t.IsEnum ? "  (enum, base " + Enum.GetUnderlyingType(t).Name + ")" : ""));
    if (t.IsEnum) { foreach (var n in Enum.GetNames(t)) Console.WriteLine("     " + n); return; }
    foreach (var m in t.GetMembers(BindingFlags.Public|BindingFlags.Instance|BindingFlags.Static)) {
      if (m is MethodInfo && m.Name != ".ctor") continue;
      Console.WriteLine("     " + m.MemberType + " " + (m as FieldInfo != null ? (m as FieldInfo).FieldType.Name : (m as PropertyInfo != null ? (m as PropertyInfo).PropertyType.Name : "")) + " " + m.Name);
    }
  }
  static void Main(string[] a) {
    var asm = Assembly.LoadFrom(a[0]);
    Affiche(asm.GetType("SoulsFormats.TAE3+Event"));
    foreach (var n in new string[]{"ModelMask","ChangeDrawMask","HideModelMask","HideWeapon","SwitchWeapon1","PlayFFX","BonePos","BoneFixOn1"})
      Affiche(asm.GetType("SoulsFormats.TAE3+Event+" + n));
  }
}
