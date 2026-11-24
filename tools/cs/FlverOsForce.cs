// FlverOsForce - force TOUS les sommets d'un maillage sur UN SEUL os, avec un
// poids de 1, et met a jour unk06 (taille de la palette d'os du maillage) en
// consequence.
//
// But : tester si le defaut vient de la REPARTITION DES POIDS sur les os.
// Notre tete utilise 9 os dont les clavicules et les bras (L_Clavicle,
// R_Clavicle, L/R_UpperArm, L/R_UpArmTwist1) ; AUCUN maillage de tete de la
// vanille n'utilise ces os. Le mode de panne documente dans FlverInject.cs est
// exactement "le skinning explose : geometrie geante couvrant l'ecran".
//
// Si le rendu redevient normal avec un seul os, la repartition des poids est en
// cause ; sinon elle est innocente.
//
// Usage : FlverOsForce.exe <entree.flver> <emplacement> <indice d'os> <sortie.flver>
using System;
using System.Globalization;
using SoulsFormats;

internal static class FlverOsForce
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 4)
        {
            Console.WriteLine("usage: FlverOsForce.exe <entree.flver> <emplacement> <indice d'os> <sortie.flver>");
            return 2;
        }

        FLVER2 f = FLVER2.Read(args[0]);
        int slot = int.Parse(args[1], Inv);
        byte os = byte.Parse(args[2], Inv);

        if (slot < 0 || slot >= f.Meshes.Count)
        {
            Console.WriteLine("emplacement hors bornes : " + slot);
            return 3;
        }

        FLVER2.Mesh m = f.Meshes[slot];
        Console.WriteLine("fichier     : " + args[0]);
        Console.WriteLine("emplacement : " + slot + "   materiau " + m.MaterialIndex
                          + "   noeud " + m.NodeIndex + "   sommets " + m.Vertices.Count);
        Console.WriteLine("os force    : " + os + "   (" + f.Nodes[os].Name + ")");

        foreach (FLVER.Vertex v in m.Vertices)
        {
            v.BoneIndices[0] = os;
            v.BoneIndices[1] = 0;
            v.BoneIndices[2] = 0;
            v.BoneIndices[3] = 0;
            v.BoneWeights[0] = 1.0f;
            v.BoneWeights[1] = 0.0f;
            v.BoneWeights[2] = 0.0f;
            v.BoneWeights[3] = 0.0f;
        }

        foreach (FLVER2.FaceSet fs in m.FaceSets)
        {
            fs.Unk06 = 1;
        }

        Console.WriteLine("facesets    : " + m.FaceSets.Count + "   unk06 force a 1");
        f.Write(args[3]);
        Console.WriteLine("ecrit       : " + args[3]);
        return 0;
    }
}
