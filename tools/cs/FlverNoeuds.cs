// FlverNoeuds - remplace le NodeIndex (noeud de maillage) de certains
// emplacements d'un FLVER.
//
// But : rendre chaque couple (materiau, noeud) unique. Dans la vanille comme
// dans les mods communautaires qui fonctionnent, aucun maillage ne partage son
// couple (materiau, noeud) avec un autre. Un noeud peut etre reutilise, mais
// jamais avec le meme materiau.
//
// Usage : FlverNoeuds.exe <entree.flver> <sortie.flver> <emplacement:noeud,...>
using System;
using System.Globalization;
using SoulsFormats;

internal static class FlverNoeuds
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 3)
        {
            Console.WriteLine("usage: FlverNoeuds.exe <entree.flver> <sortie.flver> <emplacement:noeud,...>");
            return 2;
        }

        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0] + " (" + f.Meshes.Count + " maillages)");

        foreach (string spec in args[2].Split(','))
        {
            string[] p = spec.Split(':');
            int slot = int.Parse(p[0], Inv);
            int node = int.Parse(p[1], Inv);
            if (slot < 0 || slot >= f.Meshes.Count)
            {
                Console.WriteLine("emplacement hors bornes : " + slot);
                return 3;
            }
            Console.WriteLine(string.Format(Inv, "  emplacement {0,2} (mat {1,2}) : noeud {2,3} -> {3,3}",
                slot, f.Meshes[slot].MaterialIndex, f.Meshes[slot].NodeIndex, node));
            f.Meshes[slot].NodeIndex = node;
        }

        f.Write(args[1]);
        Console.WriteLine("ecrit : " + args[1]);
        return 0;
    }
}
