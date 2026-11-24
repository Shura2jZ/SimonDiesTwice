// FlverProfil.exe -- profil geometrique d'un maillage : ou sont les saillies ?
//
// Sert a determiner l'orientation d'une tete sans se fier a l'oeil :
// on decoupe la hauteur (Y) en tranches et, pour chacune, on mesure la cote
// maximale en Z (l'avant du visage). Le nez produit un pic net ; les orbites
// un creux. Si le pic est au-dessus du milieu, la tete est droite ; en dessous,
// elle est a l'envers.
//
// Usage :
//   FlverProfil.exe <fichier.flver> <maillage> [tranches]
//
// Lecture seule sur l'entree.
using System;
using System.Globalization;
using SoulsFormats;

internal static class FlverProfil
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("usage: FlverProfil.exe <fichier.flver> <maillage> [tranches]");
            return 2;
        }
        int mi = int.Parse(args[1], Inv);
        int tranches = args.Length > 2 ? int.Parse(args[2], Inv) : 12;

        FLVER2 f = FLVER2.Read(args[0]);
        if (mi >= f.Meshes.Count) { Console.WriteLine("maillage hors limites"); return 1; }
        FLVER2.Mesh m = f.Meshes[mi];

        float ymin = float.MaxValue, ymax = float.MinValue;
        float zmin = float.MaxValue, zmax = float.MinValue;
        float xmin = float.MaxValue, xmax = float.MinValue;
        foreach (FLVER.Vertex v in m.Vertices)
        {
            if (v.Position.Y < ymin) ymin = v.Position.Y;
            if (v.Position.Y > ymax) ymax = v.Position.Y;
            if (v.Position.Z < zmin) zmin = v.Position.Z;
            if (v.Position.Z > zmax) zmax = v.Position.Z;
            if (v.Position.X < xmin) xmin = v.Position.X;
            if (v.Position.X > xmax) xmax = v.Position.X;
        }

        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine(string.Format(Inv, "maillage {0}  sommets {1}", mi, m.Vertices.Count));
        Console.WriteLine(string.Format(Inv, "boite   : X {0:0.0000} .. {1:0.0000}   Y {2:0.0000} .. {3:0.0000}   Z {4:0.0000} .. {5:0.0000}",
            xmin, xmax, ymin, ymax, zmin, zmax));

        double pas = (ymax - ymin) / tranches;
        Console.WriteLine();
        Console.WriteLine("  tranche   hauteur%    sommets     Z max     Z moyen   X etendu");

        for (int t = 0; t < tranches; t++)
        {
            double y0 = ymin + t * pas;
            double y1 = y0 + pas;
            int n = 0;
            float bz = float.MinValue;
            float bzY = 0f;
            double sz = 0;
            float bxmin = float.MaxValue, bxmax = float.MinValue;
            foreach (FLVER.Vertex v in m.Vertices)
            {
                float y = v.Position.Y;
                if (t < tranches - 1) { if (y < y0 || y >= y1) continue; }
                else { if (y < y0 || y > y1) continue; }
                n++;
                sz += v.Position.Z;
                if (v.Position.Z > bz) { bz = v.Position.Z; bzY = y; }
                if (v.Position.X < bxmin) bxmin = v.Position.X;
                if (v.Position.X > bxmax) bxmax = v.Position.X;
            }
            if (n == 0) { Console.WriteLine(string.Format(Inv, "  {0,7}   {1,6:0.0}%         0", t, 100.0 * (y0 - ymin) / (ymax - ymin))); continue; }
            Console.WriteLine(string.Format(Inv, "  {0,7}   {1,6:0.0}%  {2,8}  {3,8:0.0000}  {4,8:0.0000}   {5:0.000}/{6:0.000}",
                t, 100.0 * (y0 - ymin) / (ymax - ymin), n, bz, sz / n, bxmin, bxmax));
        }

        // Pic d'avancee : la tranche qui avance le plus en Z.
        int gagnante = -1;
        double meilleur = double.MinValue;
        for (int t = 0; t < tranches; t++)
        {
            double y0 = ymin + t * pas;
            double y1 = y0 + pas;
            double bz = double.MinValue;
            foreach (FLVER.Vertex v in m.Vertices)
            {
                float y = v.Position.Y;
                if (t < tranches - 1) { if (y < y0 || y >= y1) continue; }
                else { if (y < y0 || y > y1) continue; }
                if (v.Position.Z > bz) bz = v.Position.Z;
            }
            if (bz > meilleur) { meilleur = bz; gagnante = t; }
        }
        double pctPic = 100.0 * gagnante / tranches;
        Console.WriteLine();
        Console.WriteLine(string.Format(Inv, "tranche la plus avancee (Z max) : {0} / {1}  =>  hauteur {2:0.0}% depuis le bas",
            gagnante, tranches, pctPic));
        Console.WriteLine(pctPic > 50.0
            ? "=> la saillie est dans la moitie HAUTE : tete droite (nez au-dessus du milieu)."
            : "=> la saillie est dans la moitie BASSE : tete a l'envers (nez sous le milieu).");
        return 0;
    }
}
