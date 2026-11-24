// FlverMtdSwap.exe -- change le chemin MTD d'un materiau dans un FLVER.
// Usage : FlverMtdSwap.exe <entree.flver> <sortie.flver> <index_materiau> <nouveau_mtd>
using System;
using SoulsFormats;

internal static class FlverMtdSwap
{
    private static int Main(string[] args)
    {
        FLVER2 f = FLVER2.Read(args[0]);
        int idx = int.Parse(args[2]);
        f.Materials[idx].MTD = args[3];
        f.Write(args[1]);
        Console.WriteLine("materiau " + idx + " : MTD = " + f.Materials[idx].MTD);
        return 0;
    }
}
