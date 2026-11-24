// FlverBbox - compare, pour chaque maillage :
//   - la boite reellement occupee par les sommets  (calculee)
//   - les trois vecteurs stockes Min / Max / Unk    (lus par SoulsFormats)
// Si les deux ne coincident pas en vanille, c'est que le champ stocke N'EST PAS
// une boite englobante en espace modele (et l'injecteur qui la "recalcule" ecrit
// alors des nombres que le moteur interprete autrement).
//
// Usage : FlverBbox.exe modele.flver
using System;
using System.Globalization;
using System.Numerics;
using SoulsFormats;

internal static class FlverBbox
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    private static string P(Vector3 v)
    {
        return string.Format(Inv, "({0,9:G4} {1,9:G4} {2,9:G4})", v.X, v.Y, v.Z);
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverBbox.exe modele.flver"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine();
        Console.WriteLine("observes : min/max calcules sur les sommets");
        Console.WriteLine("stockes  : Mesh.BoundingBox.Min / .Max / .Unk");
        Console.WriteLine();
        int n = 0;
        foreach (FLVER2.Mesh m in f.Meshes)
        {
            Vector3 lo = new Vector3(float.MaxValue), hi = new Vector3(float.MinValue);
            foreach (FLVER.Vertex v in m.Vertices)
            {
                lo = Vector3.Min(lo, v.Position);
                hi = Vector3.Max(hi, v.Position);
            }
            if (m.Vertices.Count == 0) { lo = Vector3.Zero; hi = Vector3.Zero; }
            Console.WriteLine("maillage [" + n + "]  " + m.Vertices.Count + " sommets");
            Console.WriteLine("   calcule min " + P(lo) + "  max " + P(hi));
            Console.WriteLine("   stocke  min " + P(m.BoundingBox.Min) + "  max " + P(m.BoundingBox.Max));
            Console.WriteLine("   stocke  Unk " + P(m.BoundingBox.Unk));
            n++;
        }
        return 0;
    }
}
