// Clm2Tool.exe -- lecture / reecriture des fichiers CLM2 (donnees de tissu
// simule accompagneant un FLVER de personnage).
//
// Chaque "mesh" CLM2 correspond a un maillage du FLVER, dans le meme ordre.
// Comme nous remplacons les 33 maillages d'Isshin par 5 maillages, les donnees
// de tissu decrivent des maillages qui n'existent plus : le simulateur tire des
// sommets au hasard et le tissu explose (grandes aiguilles blanches en jeu).
//
// Usage :
//   Clm2Tool.exe info <fichier.clm2>
//   Clm2Tool.exe roundtrip <entree.clm2> <sortie.clm2>
//   Clm2Tool.exe vide <entree.clm2> <sortie.clm2>
//
// "vide" conserve le nombre de maillages et l'entete, mais supprime toutes les
// entrees : plus aucun tissu simule.

using System;
using System.Collections.Generic;
using System.IO;
using SoulsFormats;

internal static class Clm2Tool
{
    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("usage : Clm2Tool.exe info|roundtrip|vide <entree> [sortie]");
            return 2;
        }

        string commande = args[0];
        string entree = args[1];
        CLM2 clm = CLM2.Read(entree);

        if (commande == "info")
        {
            Console.WriteLine("fichier     : " + entree);
            Console.WriteLine("compression : " + clm.Compression);
            Console.WriteLine("maillages   : " + clm.Meshes.Count);
            for (int i = 0; i < clm.Meshes.Count; i++)
            {
                CLM2.Mesh m = clm.Meshes[i];
                Console.Write("  [" + i + "] " + m.Count + " entrees");
                int n = Math.Min(m.Count, 8);
                for (int j = 0; j < n; j++)
                {
                    Console.Write("  (" + m[j].Unk00 + ", " + m[j].Unk02 + ")");
                }
                Console.WriteLine();
            }
            return 0;
        }

        if (args.Length < 3)
        {
            Console.WriteLine("usage : Clm2Tool.exe " + commande + " <entree> <sortie>");
            return 2;
        }
        string sortie = args[2];

        if (commande == "roundtrip")
        {
            clm.Write(sortie);
            byte[] a = File.ReadAllBytes(entree);
            byte[] b = File.ReadAllBytes(sortie);
            bool identique = a.Length == b.Length;
            int premierEcart = -1;
            if (identique)
            {
                for (int i = 0; i < a.Length; i++)
                {
                    if (a[i] != b[i])
                    {
                        identique = false;
                        premierEcart = i;
                        break;
                    }
                }
            }
            else
            {
                premierEcart = Math.Min(a.Length, b.Length);
            }
            Console.WriteLine("entree : " + a.Length + " octets, sortie : " + b.Length + " octets");
            Console.WriteLine("identique : " + (identique ? "OUI" : "NON (premier ecart a 0x"
                              + premierEcart.ToString("X") + ")"));
            return 0;
        }

        if (commande == "vide")
        {
            int total = 0;
            foreach (CLM2.Mesh m in clm.Meshes)
            {
                total += m.Count;
                m.Clear();
            }
            clm.Write(sortie);
            Console.WriteLine("entree        : " + entree + " (" + total + " entrees sur "
                              + clm.Meshes.Count + " maillages)");
            Console.WriteLine("ecrit         : " + sortie + " ("
                              + new FileInfo(sortie).Length + " octets, toutes entrees supprimees)");
            CLM2 verif = CLM2.Read(sortie);
            int reste = 0;
            foreach (CLM2.Mesh m in verif.Meshes)
            {
                reste += m.Count;
            }
            Console.WriteLine("relecture     : " + verif.Meshes.Count + " maillages, "
                              + reste + " entrees restantes");
            Entete(sortie);
            return 0;
        }

        if (commande == "reduire")
        {
            int cible = int.Parse(args[3]);
            int total = 0;
            foreach (CLM2.Mesh m in clm.Meshes)
            {
                total += m.Count;
                m.Clear();
            }
            if (clm.Meshes.Count > cible)
            {
                clm.Meshes.RemoveRange(cible, clm.Meshes.Count - cible);
            }
            clm.Write(sortie);
            Console.WriteLine("entree        : " + entree + " (" + total + " entrees sur "
                              + cible + " maillages conserves)");
            Console.WriteLine("ecrit         : " + sortie + " ("
                              + new FileInfo(sortie).Length + " octets)");
            CLM2 verif = CLM2.Read(sortie);
            Console.WriteLine("relecture     : " + verif.Meshes.Count + " maillages");
            Entete(sortie);
            return 0;
        }

        Console.WriteLine("commande inconnue : " + commande);
        return 2;
    }

    // Affiche les mots 32 bits de l'entete, pour verifier ce que le writer a
    // reellement ecrit (nombre de maillages, champs inconnus).
    private static void Entete(string chemin)
    {
        byte[] b = File.ReadAllBytes(chemin);
        Console.Write("entete (32 bits) : ");
        for (int i = 0; i < 40 && i + 4 <= b.Length; i += 4)
        {
            Console.Write(BitConverter.ToUInt32(b, i) + " ");
        }
        Console.WriteLine();
        Console.Write("apres le champ 40 : ");
        for (int i = 0x17C; i + 4 <= b.Length; i += 4)
        {
            uint v = BitConverter.ToUInt32(b, i);
            if (v != 0)
            {
                Console.Write("0x" + i.ToString("X") + "=" + v + " ");
            }
        }
        Console.WriteLine();
    }
}
