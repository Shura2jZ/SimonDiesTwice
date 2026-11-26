// MtdPatch.exe -- modifie les params d'un MTD (SSS width/strength a zero).
using System;
using SoulsFormats;

internal static class MtdPatch
{
    private static int Main(string[] args)
    {
        // args: <entree.mtd> <sortie.mtd>
        MTD m = MTD.Read(args[0]);
        foreach (MTD.Param p in m.Params)
        {
            if (p.Name == "g_SSSWidth")
                p.Value = 0.0f;
            if (p.Name == "g_SSSStrength")
                p.Value = new float[] { 0.0f, 0.0f, 0.0f };
        }
        m.Write(args[1]);
        Console.WriteLine("ecrit : " + args[1]);
        // verification
        MTD m2 = MTD.Read(args[1]);
        foreach (MTD.Param p in m2.Params)
            if (p.Name == "g_SSSWidth" || p.Name == "g_SSSStrength")
                Console.WriteLine("  " + p.Name + " = " + p.Value);
        return 0;
    }
}
