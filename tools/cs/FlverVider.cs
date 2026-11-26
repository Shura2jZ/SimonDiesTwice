// FlverVider.exe -- vide les maillages dont l'index n'est pas dans la liste.
// But : le FLVER vanilla d'Isshin a 33 emplacements de maillages, referencés par
// les masques de dessin des animations (.tae). Un modele qui n'a que 5
// maillages fait lire le moteur hors tableau -> geometrie parasite.
// On garde donc les 33 emplacements, mais on vide ceux qu'on n'utilise pas.
//
// Usage : FlverVider.exe <flver> <sortie> <liste slots a garder, ex: 3,4,5,7,8,9>
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using SoulsFormats;

internal static class FlverVider
{
    private static int Main(string[] args)
    {
        if (args.Length < 3)
        {
            Console.WriteLine("usage: FlverVider.exe <flver> <sortie> <slots a garder>");
            return 2;
        }
        FLVER2 f = FLVER2.Read(args[0]);
        var garder = new HashSet<int>();
        foreach (string s in args[2].Split(','))
            garder.Add(int.Parse(s.Trim(), CultureInfo.InvariantCulture));

        for (int i = 0; i < f.Meshes.Count; i++)
        {
            var m = f.Meshes[i];
            if (garder.Contains(i)) continue;
            int nbV = m.Vertices.Count;
            int nbF = m.FaceSets.Count;
            m.Vertices.Clear();
            m.FaceSets.Clear();
            if (m.BoundingBox != null)
            {
                m.BoundingBox.Min = new System.Numerics.Vector3(0, 0, 0);
                m.BoundingBox.Max = new System.Numerics.Vector3(0, 0, 0);
            }
            Console.WriteLine("  emplacement " + i + " vide (" + nbV + " sommets, " + nbF + " facesets)  mat " + m.MaterialIndex);
        }

        // recap
        Console.WriteLine("emplacements total : " + f.Meshes.Count);
        for (int i = 0; i < f.Meshes.Count; i++)
        {
            var m = f.Meshes[i];
            string etat = m.Vertices.Count == 0 ? "VIDE" : m.Vertices.Count + " sommets";
            Console.WriteLine("  [" + i + "] mat " + m.MaterialIndex + "  noeud " + m.NodeIndex + "  " + etat);
        }

        f.Write(args[1]);
        Console.WriteLine("ecrit : " + args[1]);
        return 0;
    }
}
