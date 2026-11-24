// FlverEdges.exe -- montre, pour chaque maillage d'un FLVER :
//   - le nombre d'indices de faces et le nombre d'indices d'ARETES (EdgeIndexGroups) ;
//   - les champs de chaque tampon de sommets (dont EdgeCompressed).
//
// C'est la piste "aretes" : le rendu du contour/protrusion des personnages FromSoft
// utilise une deuxieme liste d'indices. Si un maillage en a une et que l'autre non
// (ou si elle pointe hors du maillage), la passe d'aretes relie des sommets
// quelconques : grandes droites et polygones geants a l'ecran.
//
// Usage : FlverEdges.exe <fichier.flver>

using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using SoulsFormats;

internal static class FlverEdges
{
    private static string Champ(object o, string nom)
    {
        FieldInfo fi = o.GetType().GetField(nom, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (fi == null) return "?";
        object v = fi.GetValue(o);
        return v == null ? "null" : v.ToString();
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverEdges.exe <fichier.flver>"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier   : " + args[0]);
        Console.WriteLine("maillages : " + f.Meshes.Count);

        FieldInfo fEdge = typeof(FLVER2.FaceSet).GetField("<EdgeIndexGroups>k__BackingField",
            BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (fEdge == null) { Console.WriteLine("pas de champ EdgeIndexGroups"); return 1; }
        Console.WriteLine("champ EdgeIndexGroups : " + fEdge.FieldType.FullName);
        foreach (Type t in fEdge.FieldType.GetGenericArguments())
        {
            Console.WriteLine("    element : " + t.FullName);
            foreach (Type t2 in t.GetGenericArguments()) Console.WriteLine("        sous-element : " + t2.FullName);
        }
        Console.WriteLine();

        int i = 0;
        foreach (FLVER2.Mesh m in f.Meshes)
        {
            int totInd = 0, totBord = 0, fsAvecBord = 0, maxBord = 0, pgroupeMax = 0;
            foreach (FLVER2.FaceSet fs in m.FaceSets)
            {
                totInd += fs.Indices.Count;
                object eg = fEdge.GetValue(fs);
                if (eg == null) continue;
                int groupes = 0, total = 0;
                foreach (object g in (IEnumerable)eg)
                {
                    groupes++;
                    int c = 0;
                    if (g is IEnumerable) { foreach (object _ in (IEnumerable)g) c++; }
                    else if (g != null) c = 1;
                    total += c;
                    if (c > maxBord) maxBord = c;
                }
                if (total > 0) fsAvecBord++;
                if (groupes > pgroupeMax) pgroupeMax = groupes;
                totBord += total;
            }
            Console.WriteLine("[" + i + "] mat " + m.MaterialIndex + "  noeud " + m.NodeIndex
                              + "  sommets " + m.Vertices.Count + "  facesets " + m.FaceSets.Count
                              + "  indices de faces " + totInd
                              + "  |  indices d'aretes " + totBord
                              + " (facesets concernes " + fsAvecBord + ", groupes max " + pgroupeMax
                              + ", groupe le plus gros " + maxBord + ")");
            foreach (FLVER2.VertexBuffer vb in m.VertexBuffers)
            {
                Console.WriteLine("        tampon : disposition " + vb.LayoutIndex
                                  + "  index " + vb.BufferIndex
                                  + "  bordCompresse " + vb.EdgeCompressed
                                  + "  tailleSommet " + Champ(vb, "VertexSize")
                                  + "  nbSommets " + Champ(vb, "VertexCount")
                                  + "  offset " + Champ(vb, "BufferOffset"));
            }
            i++;
        }
        return 0;
    }
}
