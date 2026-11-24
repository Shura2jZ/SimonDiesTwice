// Sonde : verifie que SoulsFormats.dll (cible .NET Framework 4.8) peut etre
// chargee et utilisee depuis un petit programme compile avec csc.exe.
// Compile par tools/build_cs.ps1, execute par tools/run_cs.ps1.
using System;
using System.Linq;
using System.Reflection;

internal static class ProbeDll
{
    private static int Main(string[] args)
    {
        string dll = args.Length > 0 ? args[0] : "SoulsFormats.dll";
        Assembly asm = Assembly.LoadFrom(dll);
        Console.WriteLine("assembly   : " + asm.FullName);
        Console.WriteLine("runtime    : " + Environment.Version);

        var types = asm.GetExportedTypes()
            .Where(t => t.Name.StartsWith("FLVER") || t.Name.StartsWith("BND") || t.Name.StartsWith("DCX"))
            .Select(t => t.FullName)
            .OrderBy(n => n);
        Console.WriteLine("types FLVER/BND/DCX :");
        foreach (string t in types) Console.WriteLine("    " + t);
        return 0;
    }
}
