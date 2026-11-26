// FlverUvFlip.exe -- inverse le V des coordonnees de texture.
//
// Pourquoi : nos UV viennent du glTF de Simon. Verifie par rendu (Blender, avec
// la texture de Simon) :
//   - lus dans la convention "bas-gauche" (OpenGL, celle de Blender/OBJ), les UV
//     tel que le pipeline les a ecrits donnent un visage DROIT ;
//   - lus dans la convention "haut-gauche" (DirectX, celle de Sekiro et du DDS),
//     ils donnent un visage A L'ENVERS.
// Autrement dit, le pipeline a ecrit un V deja retourne. En jeu, la texture
// d'Isshin se plaquait donc a l'envers sur la tete de Simon.
//
// Correctif : v' = 1 - v. Blender lit 1-v depuis le bas exactement comme le
// moteur lit v depuis le haut : le visage redevient droit, et la texture de
// Simon sera correcte le jour ou on pourra l'installer.
//
// Usage :
//   FlverUvFlip.exe <entree.flver> <sortie.flver> [maillages|tous]
//
// Ne touche ni la geometrie, ni les poids, ni les faces.
// Lecture seule sur l'entree.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Numerics;
using SoulsFormats;

internal static class FlverUvFlip
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("usage: FlverUvFlip.exe <entree.flver> <sortie.flver> [maillages|tous]");
            return 2;
        }
        bool tous = args.Length < 3 || args[2] == "tous";
        var voulus = new HashSet<int>();
        if (!tous) foreach (string s in args[2].Split(',')) voulus.Add(int.Parse(s.Trim(), Inv));

        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier   : " + args[0] + "   maillages : " + f.Meshes.Count);

        int maillages = 0, sommets = 0, canaux = 0;
        for (int mi = 0; mi < f.Meshes.Count; mi++)
        {
            if (!tous && !voulus.Contains(mi)) continue;
            FLVER2.Mesh m = f.Meshes[mi];
            if (m.Vertices.Count == 0) continue;
            maillages++;
            foreach (FLVER.Vertex v in m.Vertices)
            {
                sommets++;
                if (v.UVs == null) continue;
                for (int k = 0; k < v.UVs.Count; k++)
                {
                    Vector3 uv = v.UVs[k];
                    v.UVs[k] = new Vector3(uv.X, 1f - uv.Y, uv.Z);
                    canaux++;
                }
            }
            Console.WriteLine(string.Format(Inv, "  maillage {0,2} : {1,6} sommets, {2} canaux d'UV retournes",
                mi, m.Vertices.Count, m.Vertices[0].UVs != null ? m.Vertices[0].UVs.Count : 0));
        }

        f.Write(args[1]);
        Console.WriteLine("sommets traites : " + sommets + "   canaux : " + canaux);
        Console.WriteLine("ecrit : " + args[1]);
        return 0;
    }
}
