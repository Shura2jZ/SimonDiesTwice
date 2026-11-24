using System;
using System.IO;

internal static class Clm2Elements
{
    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("usage: Clm2Elements.exe <entree.clm2> <nb elements>");
            return 2;
        }
        string src = args[0];
        int nb = int.Parse(args[1]);
        byte[] data = File.ReadAllBytes(src);
        Console.WriteLine("taille entree: " + data.Length);
        // En-tete CLM2 : on cherche le nombre d'elements
        // Format: magic "CLM2", version, count, ...
        int count = BitConverter.ToInt32(data, 8);
        Console.WriteLine("elements actuels: " + count);
        return 0;
    }
}
