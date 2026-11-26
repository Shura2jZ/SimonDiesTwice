// FlverComplete - complete la liste de sommets d'un maillage jusqu'a un nombre
// cible, en CLONANT le premier sommet (sommets en trop non references, donc sans
// effet sur le rendu ni sur la palette d'os du maillage).
//
// But : le seul ecart structurel qui reste entre nos builds et la vanille est le
// NOMBRE DE SOMMETS du maillage remplace (6 182 au lieu de 8 589 pour la tete).
// Or dans tous les FLVER qui fonctionnent (vanille et mods communautaires), le
// nombre de sommets par maillage est identique a celui d'origine. Ce test remet
// le compte d'origine et ne change RIEN d'autre.
//
// Note : dans ce fork de SoulsFormats, FLVER.Vertex.Write se sert d'une file
// interne (colorQueue/tangentQueue/uvQueue) comme brouillon et la vide. Un meme
// objet sommet ne peut donc etre ecrit qu'UNE fois : il faut de vrais clones.
//
// Usage : FlverComplete.exe <entree.flver> <emplacement> <nombre cible> <sortie.flver>
using System;
using System.Collections.Generic;
using System.Globalization;
using SoulsFormats;

internal static class FlverComplete
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    // clone complet d'un sommet (champs publics seulement ; les files privees
    // restent nulles, ce qui est l'etat normal apres une lecture).
    private static FLVER.Vertex Cloner(FLVER.Vertex src)
    {
        FLVER.Vertex d = new FLVER.Vertex();
        d.Position = src.Position;
        d.Normal = src.Normal;
        d.NormalW = src.NormalW;
        d.Bitangent = src.Bitangent;
        d.BoneWeights = src.BoneWeights;
        d.BoneIndices = src.BoneIndices;
        d.UVs = new List<System.Numerics.Vector3>(src.UVs);
        d.Tangents = new List<System.Numerics.Vector4>(src.Tangents);
        d.Colors = new List<FLVER.VertexColor>(src.Colors);
        return d;
    }

    private static int Main(string[] args)
    {
        if (args.Length < 4)
        {
            Console.WriteLine("usage: FlverComplete.exe <entree.flver> <emplacement> <nombre cible> <sortie.flver>");
            return 2;
        }

        FLVER2 f = FLVER2.Read(args[0]);
        int slot = int.Parse(args[1], Inv);
        int cible = int.Parse(args[2], Inv);

        if (slot < 0 || slot >= f.Meshes.Count)
        {
            Console.WriteLine("emplacement hors bornes : " + slot + " (maillages : " + f.Meshes.Count + ")");
            return 3;
        }

        List<FLVER.Vertex> v = f.Meshes[slot].Vertices;
        Console.WriteLine("fichier     : " + args[0]);
        Console.WriteLine("emplacement : " + slot + "   materiau " + f.Meshes[slot].MaterialIndex
            + "   noeud " + f.Meshes[slot].NodeIndex);
        Console.WriteLine("sommets     : " + v.Count.ToString(Inv) + " -> cible " + cible.ToString(Inv));

        if (v.Count > cible)
        {
            Console.WriteLine("REFUS : la cible est plus petite que le maillage (on ne retire pas de sommets).");
            return 4;
        }

        FLVER.Vertex proto = v[0];
        int ajoutes = 0;
        while (v.Count < cible)
        {
            v.Add(Cloner(proto));
            ajoutes++;
        }

        Console.WriteLine("sommets ajoutes : " + ajoutes.ToString(Inv) + "  (clones du sommet 0, non references)");
        Console.WriteLine("facesets : " + f.Meshes[slot].FaceSets.Count.ToString(Inv));

        f.Write(args[3]);
        Console.WriteLine("ecrit       : " + args[3]);
        return 0;
    }
}
