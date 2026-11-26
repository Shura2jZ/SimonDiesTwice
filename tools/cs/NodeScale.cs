// NodeScale.exe -- verifie les echelles et les translations des os d'un FLVER.
//
// Une echelle != 1 sur un noeud a un effet enorme au skinning : la transformation
// inverse de pose de reference divise (ou multiplie) l'ecart entre le sommet et
// l'os. Un os d'echelle 0.01 transforme un ecart de 0.4 m en 40 m : le modele
// explose a l'ecran des qu'il est anime, alors qu'il reste impeccable au repos.
//
// Usage : NodeScale.exe <fichier.flver>

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Numerics;
using SoulsFormats;

internal static class NodeScale
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: NodeScale.exe <fichier.flver>"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("noeuds  : " + f.Nodes.Count);

        float mnx = 1e30f, mxx = -1e30f, mny = 1e30f, mxy = -1e30f, mnz = 1e30f, mxz = -1e30f;
        List<string> anormaux = new List<string>();
        int i = 0;
        foreach (FLVER.Node nd in f.Nodes)
        {
            Vector3 s = nd.Scale;
            if (s.X < mnx) mnx = s.X; if (s.X > mxx) mxx = s.X;
            if (s.Y < mny) mny = s.Y; if (s.Y > mxy) mxy = s.Y;
            if (s.Z < mnz) mnz = s.Z; if (s.Z > mxz) mxz = s.Z;
            float d = Math.Max(Math.Abs(s.X - 1f), Math.Max(Math.Abs(s.Y - 1f), Math.Abs(s.Z - 1f)));
            if (d > 0.001f)
            {
                anormaux.Add("    [" + i + "] " + nd.Name + "  echelle ("
                             + s.X.ToString("0.######", Inv) + ", "
                             + s.Y.ToString("0.######", Inv) + ", "
                             + s.Z.ToString("0.######", Inv) + ")");
            }
            i++;
        }
        Console.WriteLine("echelle X : " + mnx.ToString("0.######", Inv) + " .. " + mxx.ToString("0.######", Inv));
        Console.WriteLine("echelle Y : " + mny.ToString("0.######", Inv) + " .. " + mxy.ToString("0.######", Inv));
        Console.WriteLine("echelle Z : " + mnz.ToString("0.######", Inv) + " .. " + mxz.ToString("0.######", Inv));
        Console.WriteLine("noeuds d'echelle differente de 1 : " + anormaux.Count);
        int montre = 0;
        foreach (string s in anormaux) { if (montre++ >= 40) { Console.WriteLine("    ... (" + (anormaux.Count - 40) + " autres)"); break; } Console.WriteLine(s); }
        return 0;
    }
}
