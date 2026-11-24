// MtdSwapTex.exe -- remplace les chemins de textures dans un MTD.
// Usage : MtdSwapTex.exe <entree.mtd> <sortie.mtd> <ancien> <nouveau> [<ancien2> <nouveau2> ...]
using System;
using SoulsFormats;

internal static class MtdSwapTex
{
    private static int Main(string[] args)
    {
        MTD m = MTD.Read(args[0]);
        for (int i = 2; i + 1 < args.Length; i += 2)
        {
            string a = args[i], b = args[i + 1];
            foreach (MTD.Texture t in m.Textures)
            {
                if (t.Path != null) t.Path = t.Path.Replace(a, b);
            }
        }
        m.Write(args[1]);
        Console.WriteLine("ecrit : " + args[1]);
        MTD m2 = MTD.Read(args[1]);
        foreach (MTD.Texture t in m2.Textures)
            Console.WriteLine("  Type=" + t.Type + " Path=" + t.Path);
        return 0;
    }
}
