// FlverDump - represente textuellement TOUT le contenu structurel d'un FLVER2 :
// en-tete, materiaux, dummies, listes de commandes graphiques, agencements de
// sommets (avec leurs membres), os, et en-tetes de maillages.
//
// Sert a comparer deux fichiers par simple diff textuel. La geometrie
// (positions, poids) est volontairement exclue : elle est deja validee.
//
// Usage : FlverDump.exe <modele.flver> > dump.txt
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection;
using SoulsFormats;

internal static class FlverDump
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static string V3(System.Numerics.Vector3 v)
    {
        return string.Format(Inv, "({0:0.#####} {1:0.#####} {2:0.#####})", v.X, v.Y, v.Z);
    }

    /// <summary>Membres d'un agencement de sommets, cherches dans toute la hierarchie.</summary>
    private static IEnumerable MembresLayout(object bl)
    {
        Type t = bl.GetType();
        foreach (PropertyInfo p in t.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
        {
            if (p.Name != "Members") continue;
            object v = null;
            try { v = p.GetValue(bl, null); } catch { }
            if (v is IEnumerable) return (IEnumerable)v;
        }
        foreach (FieldInfo fi in t.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
        {
            if (fi.Name != "Members") continue;
            object v = null;
            try { v = fi.GetValue(bl); } catch { }
            if (v is IEnumerable) return (IEnumerable)v;
        }
        return null;
    }

    private static object Champ(object o, string nom)
    {
        if (o == null) return null;
        Type t = o.GetType();
        PropertyInfo p = t.GetProperty(nom, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (p != null) { try { return p.GetValue(o, null); } catch { return null; } }
        FieldInfo f = t.GetField(nom, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (f != null) { try { return f.GetValue(o); } catch { return null; } }
        return null;
    }

    private static string Texte(object o)
    {
        if (o == null) return "null";
        System.Numerics.Vector3 v3;
        if (o is System.Numerics.Vector3) { v3 = (System.Numerics.Vector3)o; return V3(v3); }
        System.Numerics.Vector2 v2 = default(System.Numerics.Vector2);
        if (o is System.Numerics.Vector2) { v2 = (System.Numerics.Vector2)o; return string.Format(Inv, "({0:0.#####} {1:0.#####})", v2.X, v2.Y); }
        return Convert.ToString(o, Inv);
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage: FlverDump.exe <modele.flver>");
            return 2;
        }
        FLVER2 f = FLVER2.Read(args[0]);
        FLVER2.FLVERHeader h = f.Header;

        Console.WriteLine("### fichier : " + args[0]);
        Console.WriteLine("## en-tete");
        foreach (string nom in new string[] { "BigEndian", "Version", "Unicode", "Unk4A", "Unk4B", "Unk4C", "Unk5C", "Unk5D", "Unk68", "SpecialModifier", "Unk74" })
            Console.WriteLine("en-tete." + nom + " = " + Texte(Champ(h, nom)));
        Console.WriteLine("en-tete.bboxMin = " + V3(h.BoundingBoxMin));
        Console.WriteLine("en-tete.bboxMax = " + V3(h.BoundingBoxMax));
        Console.WriteLine("compte.materiaux = " + f.Materials.Count);
        Console.WriteLine("compte.dummies = " + f.Dummies.Count);
        Console.WriteLine("compte.gxlistes = " + f.GXLists.Count);
        Console.WriteLine("compte.noeuds = " + f.Nodes.Count);
        Console.WriteLine("compte.maillages = " + f.Meshes.Count);
        Console.WriteLine("compte.agencements = " + f.BufferLayouts.Count);
        Console.WriteLine("compte.osBase = " + f.Skeletons.BaseSkeleton.Count);
        Console.WriteLine("compte.osTous = " + f.Skeletons.AllSkeletons.Count);
        Console.WriteLine("compte.tamponsSommets = " + f.Meshes.Sum(delegate (FLVER2.Mesh m) { return m.VertexBuffers.Count; }));

        Console.WriteLine();
        Console.WriteLine("## agencements de sommets");
        for (int i = 0; i < f.BufferLayouts.Count; i++)
        {
            object bl = f.BufferLayouts[i];
            object taille = Champ(bl, "Size");
            IEnumerable ms = MembresLayout(bl);
            int n = 0;
            List<string> lignes = new List<string>();
            if (ms != null)
            {
                foreach (object m in ms)
                {
                    n++;
                    lignes.Add(string.Format(Inv, "agencement[{0}].membre[{1}] = flux {2}  type {3}  semantique {4}  index {5}  taille {6}  modificateur {7}",
                        i, n - 1, Texte(Champ(m, "Stream")), Texte(Champ(m, "Type")), Texte(Champ(m, "Semantic")),
                        Texte(Champ(m, "Index")), Texte(Champ(m, "Size")), Texte(Champ(m, "SpecialModifier"))));
                }
            }
            Console.WriteLine(string.Format(Inv, "agencement[{0}] taille = {1}   membres = {2}", i, Texte(taille), n));
            foreach (string l in lignes) Console.WriteLine(l);
        }

        Console.WriteLine();
        Console.WriteLine("## materiaux");
        for (int i = 0; i < f.Materials.Count; i++)
        {
            FLVER2.Material m = f.Materials[i];
            Console.WriteLine(string.Format(Inv, "materiau[{0}] nom = {1}   mtd = {2}   gx = {3}   index = {4}   textures = {5}",
                i, m.Name, m.MTD, m.GXIndex, m.Index, m.Textures.Count));
            for (int k = 0; k < m.Textures.Count; k++)
            {
                FLVER2.Texture t = m.Textures[k];
                Console.WriteLine(string.Format(Inv, "materiau[{0}].texture[{1}] = type {2}  chemin {3}  echelle {4}  unk10 {5}  unk11 {6}  unk14 {7}  unk18 {8}  unk1C {9}",
                    i, k, t.Type, t.Path, Texte(t.Scale), t.Unk10, t.Unk11, t.Unk14, t.Unk18, t.Unk1C));
            }
        }

        Console.WriteLine();
        Console.WriteLine("## listes de commandes graphiques");
        for (int i = 0; i < f.GXLists.Count; i++)
        {
            FLVER2.GXList g = f.GXLists[i];
            Console.WriteLine(string.Format(Inv, "gx[{0}] terminateurID = {1}   longueur = {2}", i, g.TerminatorID, g.TerminatorLength));
        }

        Console.WriteLine();
        Console.WriteLine("## dummies");
        for (int i = 0; i < f.Dummies.Count; i++)
        {
            FLVER.Dummy d = f.Dummies[i];
            Console.WriteLine(string.Format(Inv, "dummy[{0}] pos {1}  avant {2}  haut {3}  ref {4}  osParent {5}  osAttache {6}  couleur {7}  flag1 {8}  useUpward {9}  unk30 {10}  unk34 {11}",
                i, V3(d.Position), V3(d.Forward), V3(d.Upward), d.ReferenceID, d.ParentBoneIndex, d.AttachBoneIndex,
                d.Color, d.Flag1, d.UseUpwardVector, d.Unk30, d.Unk34));
        }

        Console.WriteLine();
        Console.WriteLine("## os (noms, parents, drapeaux)");
        for (int i = 0; i < f.Nodes.Count; i++)
        {
            FLVER.Node nd = f.Nodes[i];
            Console.WriteLine(string.Format(Inv, "os[{0}] {1}  parent {2}  premierEnfant {3}  frereSuivant {4}  frerePrecedent {5}  drapeaux {6}  translation {7}  rotation {8}  echelle {9}",
                i, nd.Name, nd.ParentIndex, nd.FirstChildIndex, nd.NextSiblingIndex, nd.PreviousSiblingIndex,
                nd.Flags, V3(nd.Translation), V3(nd.Rotation), V3(nd.Scale)));
        }

        Console.WriteLine();
        Console.WriteLine("## squelettes");
        long sommeBase = 0, sommeTous = 0;
        foreach (FLVER2.SkeletonSet.Bone b in f.Skeletons.BaseSkeleton)
            sommeBase += b.ParentIndex * 7 + b.FirstChildIndex * 13 + b.NextSiblingIndex * 17 + b.PreviousSiblingIndex * 19 + b.NodeIndex * 23;
        foreach (FLVER2.SkeletonSet.Bone b in f.Skeletons.AllSkeletons)
            sommeTous += b.ParentIndex * 7 + b.FirstChildIndex * 13 + b.NextSiblingIndex * 17 + b.PreviousSiblingIndex * 19 + b.NodeIndex * 23;
        Console.WriteLine("squelette.sommeBase = " + sommeBase);
        Console.WriteLine("squelette.sommeTous = " + sommeTous);

        Console.WriteLine();
        Console.WriteLine("## maillages");
        for (int i = 0; i < f.Meshes.Count; i++)
        {
            FLVER2.Mesh m = f.Meshes[i];
            Console.WriteLine(string.Format(Inv, "maillage[{0}] materiau {1}  noeud {2}  dynamique {3}  poidsOs {4}  palette {5}  sommets {6}  bbox min {7} max {8} unk {9}",
                i, m.MaterialIndex, m.NodeIndex, m.Dynamic, m.UseBoneWeights, m.BoneIndices.Count, m.Vertices.Count,
                V3(m.BoundingBox.Min), V3(m.BoundingBox.Max), V3(m.BoundingBox.Unk)));
            for (int k = 0; k < m.VertexBuffers.Count; k++)
            {
                FLVER2.VertexBuffer vb = m.VertexBuffers[k];
                Console.WriteLine(string.Format(Inv, "maillage[{0}].tampon[{1}] tampon {2}  agencement {3}  aretesCompressees {4}",
                    i, k, vb.BufferIndex, vb.LayoutIndex, vb.EdgeCompressed));
            }
            for (int k = 0; k < m.FaceSets.Count; k++)
            {
                FLVER2.FaceSet fs = m.FaceSets[k];
                long s = 0;
                foreach (int v in fs.Indices) s += v;
                Console.WriteLine(string.Format(Inv, "maillage[{0}].faceset[{1}] drapeaux {2}  bande {3}  cull {4}  unk06 {5}  indices {6}  somme {7}  min {8}  max {9}",
                    i, k, fs.Flags, fs.TriangleStrip, fs.CullBackfaces, fs.Unk06, fs.Indices.Count, s,
                    fs.Indices.Count > 0 ? fs.Indices.Min() : -1, fs.Indices.Count > 0 ? fs.Indices.Max() : -1));
            }
        }
        return 0;
    }
}
