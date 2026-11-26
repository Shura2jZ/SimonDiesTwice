// FlverCulls - liste, pour chaque maillage, les proprietes de chaque faceset :
// drapeaux, bande (strip), faces cachees (cull), unk06 et nombre d'indices.
//
// But : le sens d'enroulement des triangles de la vanille est *rentrant* au sens
// de la regle de la main droite (le produit vectoriel pointe a l'oppose de la
// normale stockee). Le rendu depend donc entierement du drapeau "cull". Si l'on
// change ce drapeau, on enleve la mauvaise face et le personnage se voit
// par-dedans.
//
// Usage : FlverCulls.exe modele.flver
using System;
using System.Globalization;
using SoulsFormats;

internal static class FlverCulls
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverCulls.exe modele.flver"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine();
        Console.WriteLine(string.Format(Inv, "{0,-10} {1,-12} {2,-10}", "maill", "materiau", "noeud"));
        for (int i = 0; i < f.Meshes.Count; i++)
        {
            FLVER2.Mesh m = f.Meshes[i];
            Console.WriteLine(string.Format(Inv, "[{0,2}] {1,-32} mat {2,2} ({3,-24}) noeud {4,3} ({5})  sommets {6}",
                i, f.Nodes[m.NodeIndex].Name, m.MaterialIndex,
                f.Materials[m.MaterialIndex].MTD.Substring(Math.Max(0, f.Materials[m.MaterialIndex].MTD.LastIndexOf('\\') + 1)),
                m.NodeIndex, f.Nodes[m.NodeIndex].Name, m.Vertices.Count));
            for (int j = 0; j < m.FaceSets.Count; j++)
            {
                FLVER2.FaceSet fs = m.FaceSets[j];
                Console.WriteLine(string.Format(Inv,
                    "     fs{0} drapeaux 0x{1:X8}  bande {2,-5}  cull {3,-5}  unk06 {4,3}  indices {5}",
                    j, (uint)fs.Flags, fs.TriangleStrip, fs.CullBackfaces, fs.Unk06, fs.Indices.Count));
            }
        }
        return 0;
    }
}
