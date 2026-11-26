// FlverEnroule.exe -- remet tous les triangles dans le sens attendu par Sekiro.
//
// Convention mesuree sur le modele vanille (33 maillages) : la normale
// geometrique cross(b-a, c-a) pointe vers l'INTERIEUR, c'est-a-dire a l'oppose
// des normales de sommet : dot(face, norme_sommet) = -0,98 en moyenne, et 0 %
// des triangles sont du mauvais cote.
//
// Notre chaine d'export a inverse une partie des triangles (miroir gauche/droite
// par reflexion d'un axe) : 44 % des maillages 3, 6 et 7, et 6,5 % de la tete.
// Resultat en jeu : avec le rejet des faces arriere, ces triangles disparaissent
// -> trous dans les habits et crane ouvert vu de dos.
//
// La correction est locale et sans ambiguite : pour chaque triangle, on compare
// la normale geometrique a la moyenne des normales de ses trois sommets. Si le
// produit scalaire est positif, le triangle est a l'envers : on echange deux
// indices. L'operation est idempotente (un triangle corrige ne repasse plus).
//
// Les facesets multiples d'un maillage (niveaux de detail) sont traites par la
// meme regle, ce qui garde les niveaux coherents entre eux.
//
// Usage :
//   FlverEnroule.exe <entree.flver> <sortie.flver>
//
// Lecture seule sur l'entree.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Numerics;
using SoulsFormats;

internal static class FlverEnroule
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("usage: FlverEnroule.exe <entree.flver> <sortie.flver> [maillages]");
            Console.WriteLine("  maillages : liste separee par des virgules (defaut : tous)");
            return 2;
        }

        // On ne touche que les maillages demandes : les maillages d'Isshin ont
        // quelques triangles volontairement retournes (pieces double face), les
        // corriger les rendrait invisibles depuis l'exterieur.
        bool tous = args.Length < 3 || args[2] == "tous";
        var voulus = new HashSet<int>();
        if (!tous) foreach (string s in args[2].Split(',')) voulus.Add(int.Parse(s.Trim(), Inv));

        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier   : " + args[0] + "   maillages : " + f.Meshes.Count);
        Console.WriteLine("  maill  triangles  retournes   avant  apres");

        int totalRetournes = 0;
        for (int mi = 0; mi < f.Meshes.Count; mi++)
        {
            if (!tous && !voulus.Contains(mi)) continue;
            FLVER2.Mesh m = f.Meshes[mi];
            if (m.Vertices.Count == 0) continue;

            int avant = CompteEnvers(m);
            int triangles = 0;
            int retournes = 0;

            foreach (FLVER2.FaceSet fs in m.FaceSets)
            {
                List<int> idx = fs.Indices;
                for (int t = 0; t + 2 < idx.Count; t += 3)
                {
                    triangles++;
                    Vector3 p0 = m.Vertices[idx[t]].Position;
                    Vector3 p1 = m.Vertices[idx[t + 1]].Position;
                    Vector3 p2 = m.Vertices[idx[t + 2]].Position;
                    Vector3 n = Vector3.Cross(p1 - p0, p2 - p0);
                    if (n.LengthSquared() < 1e-20f) continue;
                    Vector3 vn = m.Vertices[idx[t]].Normal + m.Vertices[idx[t + 1]].Normal + m.Vertices[idx[t + 2]].Normal;
                    if (vn.LengthSquared() < 1e-20f) continue;
                    if (Vector3.Dot(n, vn) <= 0f) continue;

                    int tampon = idx[t + 1];
                    idx[t + 1] = idx[t + 2];
                    idx[t + 2] = tampon;
                    retournes++;
                }
            }

            int apres = CompteEnvers(m);
            totalRetournes += retournes;
            if (retournes > 0 || avant > 0)
            {
                Console.WriteLine(string.Format(Inv, "  {0,5}  {1,9}  {2,10}  {3,5:0.0}%  {4,5:0.0}%",
                    mi, triangles, retournes, 100.0 * avant / Math.Max(1, triangles), 100.0 * apres / Math.Max(1, triangles)));
            }
        }

        f.Write(args[1]);
        Console.WriteLine("triangles retournes : " + totalRetournes);
        Console.WriteLine("ecrit : " + args[1]);
        return 0;
    }

    // Nombre de triangles dont la normale geometrique est du meme cote que les
    // normales de sommet (c'est-a-dire a l'envers selon la convention Sekiro).
    private static int CompteEnvers(FLVER2.Mesh m)
    {
        int n = 0;
        foreach (FLVER2.FaceSet fs in m.FaceSets)
        {
            List<int> idx = fs.Indices;
            for (int t = 0; t + 2 < idx.Count; t += 3)
            {
                Vector3 p0 = m.Vertices[idx[t]].Position;
                Vector3 p1 = m.Vertices[idx[t + 1]].Position;
                Vector3 p2 = m.Vertices[idx[t + 2]].Position;
                Vector3 g = Vector3.Cross(p1 - p0, p2 - p0);
                if (g.LengthSquared() < 1e-20f) continue;
                Vector3 vn = m.Vertices[idx[t]].Normal + m.Vertices[idx[t + 1]].Normal + m.Vertices[idx[t + 2]].Normal;
                if (Vector3.Dot(g, vn) > 0f) n++;
            }
        }
        return n;
    }
}
