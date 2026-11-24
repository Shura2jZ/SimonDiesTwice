// FlverUv - etendue des UV par maillage. La disposition 7 d'Isshin contient
// "UV:Short4" = 8 octets, soit DEUX jeux d'UV. Tous les outils precedents
// n'imprimaient que UV0. On mesure donc UV1 et on compte les sommets ou
// UV1 differe de UV0 : si la vanille a un UV1 constant (ou identique a UV0),
// un UV1 different chez nous constitue une deviation a corriger.
//
// Usage : FlverUv.exe modele.flver
using System;
using System.Globalization;
using SoulsFormats;

internal static class FlverUv
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverUv.exe modele.flver"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        for (int i = 0; i < f.Meshes.Count; i++)
        {
            FLVER2.Mesh m = f.Meshes[i];
            if (m.Vertices.Count == 0) continue;
            int nb = m.Vertices[0].UVs.Count;
            Console.Write(string.Format(Inv, "[{0,2}] mat={1,2} sommets={2,6} nbUV={3}",
                i, m.MaterialIndex, m.Vertices.Count, nb));
            for (int u = 0; u < nb; u++)
            {
                float loU = float.MaxValue, hiU = float.MinValue, loV = float.MaxValue, hiV = float.MinValue;
                foreach (FLVER.Vertex v in m.Vertices)
                {
                    var uv = v.UVs[u];
                    if (uv.X < loU) loU = uv.X;
                    if (uv.X > hiU) hiU = uv.X;
                    if (uv.Y < loV) loV = uv.Y;
                    if (uv.Y > hiV) hiV = uv.Y;
                }
                Console.Write(string.Format(Inv, "   UV{0} u {1:0.####}..{2:0.####}  v {3:0.####}..{4:0.####}",
                    u, loU, hiU, loV, hiV));
            }
            if (nb > 1)
            {
                int differents = 0;
                foreach (FLVER.Vertex v in m.Vertices)
                    if (v.UVs[0].X != v.UVs[1].X || v.UVs[0].Y != v.UVs[1].Y) differents++;
                Console.Write("   UV1 != UV0 sur " + differents + " sommets");
            }
            Console.WriteLine();
        }
        return 0;
    }
}
