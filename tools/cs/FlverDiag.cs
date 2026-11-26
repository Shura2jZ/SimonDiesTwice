// FlverDiag.exe -- vidage structurel complet d'un FLVER, pour comparer un
// fichier modde au fichier d'origine.
//
// Usage :
//     FlverDiag.exe <fichier.flver> [sortie.txt]
//
// Affiche, en-tete, dispositions de sommets (avec la taille de chaque
// disposition), puis pour chaque maillage : tous ses champs, ses tampons de
// sommets (avec leurs champs internes) et ses facesets, et les 2 premiers
// sommets avec tous leurs champs.

using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using SoulsFormats;

internal static class FlverDiag
{
    private static TextWriter w;

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage : FlverDiag.exe <fichier.flver> [sortie.txt]");
            return 2;
        }

        if (args.Length > 1)
        {
            w = new StreamWriter(args[1]);
        }
        else
        {
            w = Console.Out;
        }

        FLVER2 f = FLVER2.Read(args[0]);

        w.WriteLine("fichier : " + args[0]);
        w.WriteLine("=== en-tete ===");
        Dump(f.Header, "  ");

        w.WriteLine("os (nodes) : " + f.Nodes.Count);
        w.WriteLine("materiaux  : " + f.Materials.Count);
        w.WriteLine("maillages  : " + f.Meshes.Count);
        w.WriteLine("dispos.    : " + f.BufferLayouts.Count);
        w.WriteLine("dummies    : " + f.Dummies.Count);

        w.WriteLine("=== dispositions de sommets ===");
        for (int i = 0; i < f.BufferLayouts.Count; i++)
        {
            FLVER2.BufferLayout bl = f.BufferLayouts[i];
            int taille = 0;
            foreach (FLVER.LayoutMember lm in bl)
            {
                taille += TailleDe(lm.Type);
            }
            w.WriteLine("  [" + i + "] " + bl.Count + " membres, taille " + taille + " octets");
            foreach (FLVER.LayoutMember lm in bl)
            {
                w.WriteLine("        " + lm.Semantic + "[" + lm.Index + "] = " + lm.Type
                            + " (" + TailleDe(lm.Type) + " octets)");
            }
        }

        w.WriteLine("=== maillages ===");
        for (int i = 0; i < f.Meshes.Count; i++)
        {
            FLVER2.Mesh m = f.Meshes[i];
            w.WriteLine("  [" + i + "]");
            w.WriteLine("      MaterialIndex = " + m.MaterialIndex
                        + "  NodeIndex = " + m.NodeIndex
                        + "  Dynamic = " + m.Dynamic
                        + "  UseBoneWeights = " + m.UseBoneWeights);
            w.WriteLine("      BoneIndices (palette) : " + m.BoneIndices.Count + " -> "
                        + Liste(m.BoneIndices));
            w.WriteLine("      BoundingBox : " + Fmt(m.BoundingBox.Min) + " .. "
                        + Fmt(m.BoundingBox.Max) + "  Unk=" + Fmt(m.BoundingBox.Unk));
            w.WriteLine("      sommets : " + m.Vertices.Count);
            for (int b = 0; b < m.VertexBuffers.Count; b++)
            {
                w.WriteLine("      tampon [" + b + "] :");
                Dump(m.VertexBuffers[b], "          ");
            }
            for (int s = 0; s < m.FaceSets.Count; s++)
            {
                FLVER2.FaceSet fs = m.FaceSets[s];
                w.WriteLine("      faceset [" + s + "] flags=" + fs.Flags
                            + " cull=" + fs.CullBackfaces
                            + " unk06=" + fs.Unk06
                            + " strip=" + fs.TriangleStrip
                            + " indices=" + fs.Indices.Count
                            + " triangles=" + (fs.Indices.Count / 3));
            }
            int montre = Math.Min(2, m.Vertices.Count);
            for (int v = 0; v < montre; v++)
            {
                w.WriteLine("      sommet [" + v + "] :");
                Dump(m.Vertices[v], "          ");
            }
        }

        if (w != Console.Out)
        {
            w.Flush();
            w.Close();
            Console.WriteLine("ecrit dans " + args[1]);
        }
        return 0;
    }

    private static string Liste(IList liste)
    {
        string s = "";
        for (int i = 0; i < liste.Count && i < 12; i++)
        {
            s += liste[i] + " ";
        }
        if (liste.Count > 12) { s += "..."; }
        return s;
    }

    private static string Fmt(object o)
    {
        if (o == null) { return "null"; }
        System.Numerics.Vector3 v = (System.Numerics.Vector3)o;
        return "(" + v.X.ToString("0.####") + ", " + v.Y.ToString("0.####")
             + ", " + v.Z.ToString("0.####") + ")";
    }

    private static int TailleDe(FLVER.LayoutType t)
    {
        string n = t.ToString();
        if (n.StartsWith("Float") || n.StartsWith("Double")) { return 4 * int.Parse(n.Substring(n.Length - 1)); }
        if (n.StartsWith("UByte") || n.StartsWith("Byte")) { return 4; }
        if (n.StartsWith("Short")) { return 8; }
        if (n.StartsWith("UShort")) { return 8; }
        if (n.StartsWith("Int")) { return 16; }
        return -1;
    }

    // Vidage generique par reflexion : chaque propriete et champ public.
    private static void Dump(object o, string indent)
    {
        if (o == null) { w.WriteLine(indent + "null"); return; }
        Type t = o.GetType();
        foreach (PropertyInfo p in t.GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            if (p.GetIndexParameters().Length > 0) { continue; }
            object val;
            try { val = p.GetValue(o, null); }
            catch { continue; }
            w.WriteLine(indent + p.Name + " = " + Texte(val));
        }
        foreach (FieldInfo fi in t.GetFields(BindingFlags.Public | BindingFlags.Instance))
        {
            object val = fi.GetValue(o);
            w.WriteLine(indent + fi.Name + " = " + Texte(val));
        }
    }

    private static string Texte(object val)
    {
        if (val == null) { return "null"; }
        if (val is string) { return "\"" + val + "\""; }
        if (val is float) { return ((float)val).ToString("0.#####"); }
        if (val is double) { return ((double)val).ToString("0.#####"); }
        IList liste = val as IList;
        if (liste != null)
        {
            string s = "[";
            for (int i = 0; i < liste.Count && i < 8; i++)
            {
                s += Texte(liste[i]) + (i + 1 < liste.Count && i + 1 < 8 ? ", " : "");
            }
            if (liste.Count > 8) { s += ", ..."; }
            return s + "] (" + liste.Count + ")";
        }
        return val.ToString();
    }
}
