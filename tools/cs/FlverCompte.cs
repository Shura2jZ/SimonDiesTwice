// FlverCompte - pour chaque maillage : nombre de sommets ecrits, plus grand index
// utilise par les facesets, nombre de sommets distincts references, et donc le
// nombre d'ORPHELINS (sommets ecrits que personne ne reference).
//
// Le jeu derive tres probablement le nombre de sommets d'un maillage de
// max(index)+1 : s'il y a des orphelins, le moteur lit moins de sommets que nous
// n'en avons ecrits et la carte de la section de donnees se decale pour TOUS les
// maillages suivants.
//
// Usage : FlverCompte.exe modele.flver
using System;
using System.Collections.Generic;
using SoulsFormats;

internal static class FlverCompte
{
    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverCompte.exe modele.flver"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier   : " + args[0]);
        Console.WriteLine("maillages : " + f.Meshes.Count + "   noeuds : " + f.Nodes.Count);
        Console.WriteLine();
        Console.WriteLine(string.Format("{0,-4} {1,8} {2,8} {3,8} {4,8} {5,6} {6,9} {7,10}",
            "idx", "sommets", "maxIdx", "max+1", "distinct", "min", "orphelins", "manquants"));
        int totalOrph = 0;
        for (int i = 0; i < f.Meshes.Count; i++)
        {
            var m = f.Meshes[i];
            int max = -1, min = int.MaxValue;
            var vus = new HashSet<int>();
            foreach (var fs in m.FaceSets)
            {
                foreach (int k in fs.Indices)
                {
                    if (k > max) max = k;
                    if (k < min) min = k;
                    vus.Add(k);
                }
            }
            int n = m.Vertices.Count;
            int orph = n - (max + 1);
            int manque = (max + 1) - vus.Count;
            totalOrph += orph > 0 ? orph : 0;
            Console.WriteLine(string.Format("{0,-4} {1,8} {2,8} {3,8} {4,8} {5,6} {6,9} {7,10}",
                i, n, max, max + 1, vus.Count, min == int.MaxValue ? -1 : min, orph, manque));
        }
        Console.WriteLine();
        Console.WriteLine("orphelins au total : " + totalOrph);
        return 0;
    }
}
