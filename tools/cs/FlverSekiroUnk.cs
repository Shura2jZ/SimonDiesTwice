// FlverSekiroUnk - dump du bloc "SekiroUnk" (present uniquement dans Sekiro) :
// deux listes de membres { short[4] Unk00 ; int Index }. SoulsFormats le lit et
// le reecrit tel quel, sans comprendre son sens ("peut-etre des indices d'os").
// Mesure : nombre de membres, contenu, et Index croissant ou non.
//
// Usage : FlverSekiroUnk.exe modele.flver
using System;
using System.Globalization;
using System.Linq;
using SoulsFormats;

internal static class FlverSekiroUnk
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static void Liste(string nom, System.Collections.Generic.List<FLVER2.SekiroUnkStruct.Member> ms)
    {
        Console.WriteLine(nom + " : " + ms.Count + " membre(s)");
        for (int i = 0; i < ms.Count; i++)
        {
            var m = ms[i];
            Console.WriteLine(string.Format(Inv, "   [{0,3}] unk00 = [{1}]   index = {2}",
                i,
                string.Join(", ", m.Unk00.Select(x => x.ToString(Inv)).ToArray()),
                m.Index));
        }
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverSekiroUnk.exe modele.flver"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("maillages=" + f.Meshes.Count + "  materiaux=" + f.Materials.Count
            + "  noeuds=" + f.Nodes.Count + "  dummies=" + f.Dummies.Count
            + "  tampons=" + f.Meshes.Sum(m => m.VertexBuffers.Count));
        Console.WriteLine();
        Liste("Members1", f.SekiroUnk.Members1);
        Console.WriteLine();
        Liste("Members2", f.SekiroUnk.Members2);
        return 0;
    }
}
