// FlverRoundtrip - lit un FLVER puis le reecrit tel quel.
// Sert a verifier si SoulsFormats reconstruit le fichier a l'identique
// (comparaison octet par octet faite ensuite en Python).
//
// Usage : FlverRoundtrip.exe entree.flver sortie.flver
using System;
using System.Diagnostics;
using System.IO;
using SoulsFormats;

internal static class FlverRoundtrip
{
    private static int Main(string[] args)
    {
        if (args.Length < 2) { Console.WriteLine("usage: FlverRoundtrip.exe entree.flver sortie.flver"); return 2; }

        var sw = Stopwatch.StartNew();
        FLVER2 flver = FLVER2.Read(args[0]);
        sw.Stop();
        Console.WriteLine("lecture  : " + sw.ElapsedMilliseconds + " ms  (" + flver.Nodes.Count + " os, "
            + flver.Materials.Count + " materiaux, " + flver.Meshes.Count + " maillages)");

        sw.Restart();
        flver.Write(args[1]);
        sw.Stop();
        Console.WriteLine("ecriture : " + sw.ElapsedMilliseconds + " ms  -> " + args[1]
            + " (" + new FileInfo(args[1]).Length.ToString("N0") + " octets)");
        return 0;
    }
}
