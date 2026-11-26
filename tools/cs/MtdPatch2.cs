// MtdPatch2.exe -- set SSS strength to 0 and diffuse color to white.
using System;
using SoulsFormats;

internal static class MtdPatch2
{
    private static int Main(string[] args)
    {
        MTD m = MTD.Read(args[0]);
        foreach (MTD.Param p in m.Params)
        {
            if (p.Name == "g_SSSStrength")
                p.Value = new float[] { 0.0f, 0.0f, 0.0f };
            if (p.Name == "g_DiffuseMapColor")
                p.Value = new float[] { 1.0f, 1.0f, 1.0f };
        }
        m.Write(args[1]);
        Console.WriteLine("ecrit : " + args[1]);
        MTD m2 = MTD.Read(args[1]);
        foreach (MTD.Param p in m2.Params)
            if (p.Name == "g_SSSStrength" || p.Name == "g_DiffuseMapColor")
                Console.WriteLine("  " + p.Name + " = " + p.Value);
        return 0;
    }
}
