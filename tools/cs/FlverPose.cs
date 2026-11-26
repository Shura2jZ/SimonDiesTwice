// FlverPose.exe -- fabrique un fichier de pose pour le CLI de rendu (--pose).
//
// Le CLI du FLVER Editor applique la deformation exacte du jeu :
//     sommet_deforme = somme_j  poids_j * pose_j * (bind_j)^-1 * sommet
// ou bind_j est la transformation globale du noeud j dans le FLVER lui-meme
// (la pose de reference) et pose_j celle du fichier de pose.
//
// Autrement dit : si on lui donne en pose la liste des noeuds du FLVER
// elle-meme, le rendu doit etre identique au rendu sans pose. Et si on lui
// donne une pose differente, on voit exactement ce que le jeu affiche.
//
// C'est donc un moyen de reproduire l'anomalie hors du jeu, et de comparer
// le modele d'origine et le modele modifie avec la meme pose.
//
// Usage :
//     FlverPose.exe <modele.flver> <sortie.json> identite
//     FlverPose.exe <modele.flver> <sortie.json> tout <angle_degres>
//     FlverPose.exe <modele.flver> <sortie.json> os <angle_degres> <nom1,nom2,...>
//     FlverPose.exe <modele.flver> lister

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Numerics;
using System.Reflection;
using System.Web.Script.Serialization;
using SoulsFormats;

internal static class FlverPose
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("usage: FlverPose.exe <modele.flver> <sortie.json> identite|tout|os [angle] [noms]");
            return 2;
        }

        FLVER2 f = FLVER2.Read(args[0]);

        if (args[1] == "lister")
        {
            Console.WriteLine("proprietes de FLVER.Node :");
            foreach (PropertyInfo p in typeof(FLVER.Node).GetProperties(BindingFlags.Public | BindingFlags.Instance))
            {
                Console.WriteLine("   " + p.PropertyType.Name + " " + p.Name + (p.CanWrite ? "" : "   (lecture seule)"));
            }
            return 0;
        }

        string mode = args.Length > 2 ? args[2] : "identite";
        float angle = args.Length > 3 ? float.Parse(args[3], Inv) : 0f;
        HashSet<string> noms = new HashSet<string>();
        if (args.Length > 4)
        {
            foreach (string s in args[4].Split(',')) { if (s.Trim().Length > 0) noms.Add(s.Trim()); }
        }

        float rad = angle * (float)Math.PI / 180f;
        int touches = 0;
        if (mode != "identite")
        {
            for (int i = 0; i < f.Nodes.Count; i++)
            {
                FLVER.Node nd = f.Nodes[i];
                bool touche = (mode == "tout") || noms.Contains(nd.Name);
                if (!touche) { continue; }
                nd.Rotation = new Vector3(nd.Rotation.X + rad, nd.Rotation.Y, nd.Rotation.Z);
                touches++;
                if (noms.Contains(nd.Name))
                {
                    Console.WriteLine("   os [" + i + "] " + nd.Name + "  rotation locale ("
                                      + nd.Rotation.X.ToString("0.#####", Inv) + ", "
                                      + nd.Rotation.Y.ToString("0.#####", Inv) + ", "
                                      + nd.Rotation.Z.ToString("0.#####", Inv) + ")");
                }
            }
        }
        Console.WriteLine("noeuds touches : " + touches + " / " + f.Nodes.Count);

        string json = new JavaScriptSerializer { MaxJsonLength = Int32.MaxValue }.Serialize(f.Nodes);
        File.WriteAllText(args[1], json);
        Console.WriteLine("ecrit : " + args[1] + "  (" + json.Length + " caracteres)");
        return 0;
    }
}
