// FlverEntete040 - recalcule les deux compteurs de faces de l'en-tete d'un FLVER.
//
// Mesure (regle verifiee exactement sur la vanille de c5400) :
//   offset 0x40 = nombre de TRIANGLES des facesets SANS le drapeau MotionBlur
//                 (0x80000000), soit somme des indices hors MB / 3
//                 Vanille : 786 978 / 3 = 262 326
//   offset 0x44 = nombre de TRIANGLES de TOUS les facesets
//                 Vanille : 1 687 458 / 3 = 562 486
//
// SoulsFormats ecrit la meme valeur (le total) dans les deux champs a chaque
// lecture/ecriture. L'injecteur corrige 0x40, mais tout passage ulterieur par
// SoulsFormats (FlverComplete, FlverOsForce, ...) ecrase de nouveau le champ.
// Cet outil doit donc etre la DERNIERE etape avant l'empaquetage.
//
// Usage : FlverEntete040.exe <entree.flver> <sortie.flver>
//         FlverEntete040.exe <fichier.flver> --en-place
using System;
using System.Globalization;
using System.IO;
using SoulsFormats;

internal static class FlverEntete040
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("usage: FlverEntete040.exe <entree.flver> <sortie.flver>");
            Console.WriteLine("       FlverEntete040.exe <fichier.flver> --en-place");
            return 2;
        }

        string entre = args[0];
        bool enPlace = args[1] == "--en-place";
        string sortie = enPlace ? entre : args[1];

        FLVER2 f = FLVER2.Read(entre);

        int facesHorsMb = 0;
        int facesTotales = 0;
        int facesets = 0;
        foreach (FLVER2.Mesh mm in f.Meshes)
        {
            foreach (FLVER2.FaceSet fs in mm.FaceSets)
            {
                facesets++;
                int nbFaces = fs.Indices.Count / 3;
                facesTotales += nbFaces;
                if (((uint)fs.Flags & 0x80000000u) == 0)
                {
                    facesHorsMb += nbFaces;
                }
            }
        }

        byte[] octets = File.ReadAllBytes(entre);
        if (octets.Length < 0x48) { Console.WriteLine("fichier trop court"); return 3; }
        int avant40 = BitConverter.ToInt32(octets, 0x40);
        int avant44 = BitConverter.ToInt32(octets, 0x44);

        Array.Copy(BitConverter.GetBytes(facesHorsMb), 0, octets, 0x40, 4);
        Array.Copy(BitConverter.GetBytes(facesTotales), 0, octets, 0x44, 4);
        File.WriteAllBytes(sortie, octets);

        Console.WriteLine("facesets : " + facesets + "   maillages : " + f.Meshes.Count);
        Console.WriteLine("0x40 : " + avant40.ToString(Inv) + " -> " + facesHorsMb.ToString(Inv)
                          + (avant40 == facesHorsMb ? "   (deja conforme)" : "   CORRIGE"));
        Console.WriteLine("0x44 : " + avant44.ToString(Inv) + " -> " + facesTotales.ToString(Inv)
                          + (avant44 == facesTotales ? "   (deja conforme)" : "   CORRIGE"));
        Console.WriteLine("ecrit : " + sortie);
        return 0;
    }
}
