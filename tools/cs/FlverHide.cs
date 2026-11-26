// FlverHide.exe -- rend un maillage INVISIBLE en jeu, sans toucher a la
// structure du fichier.
//
// Pourquoi pas simplement vider les facesets : le moteur derive probablement le
// nombre de sommets d'un maillage de (plus grand indice + 1) (voir FlverCompte).
// Un maillage sans indice aurait donc 0 sommet, ce qui risquerait de decaler la
// lecture. On garde donc les indices, les facesets, les tampons et les compteurs
// EXACTEMENT tels quels, et on rend la geometrie DEGENEREE :
//
//   - tous les sommets du maillage sont amenes au meme point ;
//   - tous recoivent le meme os unique, avec le poids 1 (donc ils restent
//     confondus quelle que soit la pose, la deformation par os etant rigide) ;
//   - unk06 (taille de la palette d'os du maillage) passe a 1, valeur conforme
//     a son sens mesure : nombre d'index d'os distincts non nuls.
//
// Tous les triangles ont alors une surface nulle : rien n'est rasterise, le
// maillage disparait, et aucune autre donnee du fichier ne bouge.
//
// Usage : FlverHide.exe <entree.flver> <sortie.flver> <maillages, ex: 0,1,2,8>
//
// Lecture seule sur l'entree.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Numerics;
using SoulsFormats;

internal static class FlverHide
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 3)
        {
            Console.WriteLine("usage: FlverHide.exe <entree.flver> <sortie.flver> <maillages, ex: 0,1,2,8>");
            return 2;
        }

        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0] + "   maillages : " + f.Meshes.Count);

        string[] morceaux = args[2].Split(',');
        foreach (string morceau in morceaux)
        {
            int i = int.Parse(morceau.Trim(), Inv);
            if (i < 0 || i >= f.Meshes.Count)
            {
                Console.WriteLine("REFUS : maillage hors bornes : " + i);
                return 3;
            }
            var m = f.Meshes[i];

            // os a utiliser : le premier index d'os non nul du maillage, sinon 147
            // (tete), qui existe dans tous les squelettes de personnage.
            int os = 147;
            bool trouve = false;
            for (int k = 0; k < m.Vertices.Count && !trouve; k++)
            {
                for (int c = 0; c < 4; c++)
                {
                    int b = Convert.ToInt32(m.Vertices[k].BoneIndices[c]);
                    if (b != 0) { os = b; trouve = true; break; }
                }
            }

            Vector3 avantMin = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue);
            Vector3 avantMax = new Vector3(float.MinValue, float.MinValue, float.MinValue);
            foreach (var v in m.Vertices)
            {
                Vector3 p = v.Position;
                if (p.X < avantMin.X) avantMin.X = p.X;
                if (p.Y < avantMin.Y) avantMin.Y = p.Y;
                if (p.Z < avantMin.Z) avantMin.Z = p.Z;
                if (p.X > avantMax.X) avantMax.X = p.X;
                if (p.Y > avantMax.Y) avantMax.Y = p.Y;
                if (p.Z > avantMax.Z) avantMax.Z = p.Z;
            }

            foreach (var v in m.Vertices)
            {
                v.Position = new Vector3(0f, 0f, 0f);
                for (int c = 0; c < 4; c++)
                {
                    v.BoneIndices[c] = (byte)os;
                    v.BoneWeights[c] = (c == 0) ? 1f : 0f;
                }
            }

            foreach (var fs in m.FaceSets) fs.Unk06 = 1;

            m.BoundingBox.Min = new Vector3(0f, 0f, 0f);
            m.BoundingBox.Max = new Vector3(0f, 0f, 0f);
            m.BoundingBox.Unk = new Vector3(0f, 0f, 0f);

            string materiau = m.MaterialIndex < f.Materials.Count ? f.Materials[m.MaterialIndex].Name : "?";
            string noeud = (m.NodeIndex >= 0 && m.NodeIndex < f.Nodes.Count) ? f.Nodes[m.NodeIndex].Name : "?";
            Console.WriteLine(string.Format(Inv,
                "  maillage {0,2} : {1,6} sommets ramenes au meme point (os {2}), facesets {3} -> unk06=1   mat {4} {5}   noeud {6}",
                i, m.Vertices.Count, os, m.FaceSets.Count, m.MaterialIndex, materiau, noeud));
            Console.WriteLine(string.Format(Inv, "              boite avant ({0:0.###},{1:0.###},{2:0.###})..({3:0.###},{4:0.###},{5:0.###})",
                avantMin.X, avantMin.Y, avantMin.Z, avantMax.X, avantMax.Y, avantMax.Z));
        }

        f.Write(args[1]);
        Console.WriteLine("ecrit : " + args[1]);
        return 0;
    }
}
