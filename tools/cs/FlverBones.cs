// FlverBones - etat de la "collection d'os" (f.Bones), de la palette par maillage
// (Mesh.BoneIndices) et de la facon dont les index d'os des sommets se resolvent.
//
// Question tranchee : les index d'os des sommets visent-ils f.Bones, la palette du
// maillage, ou f.Nodes ? Si la vanille passe par f.Bones/palette et que nos index
// sont des index de Noeuds, le moteur lit des os faux -> triangles etires a l'infini.
//
// La DLL (fork FLVER_Editor X2.7) differe de la source amont : tout ce qui concerne
// le maillage passe donc par reflexion.
//
// Usage : FlverBones.exe <flver> [emplacements separes par des virgules]
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using SoulsFormats;

internal static class FlverBones
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static object Prop(object o, string nom)
    {
        if (o == null) return null;
        PropertyInfo p = o.GetType().GetProperty(nom);
        if (p == null || p.GetIndexParameters().Length > 0) return null;
        try { return p.GetValue(o, null); } catch { return null; }
    }

    private static object Fld(object o, string nom)
    {
        if (o == null) return null;
        FieldInfo f = o.GetType().GetField(nom);
        if (f == null) return null;
        try { return f.GetValue(o); } catch { return null; }
    }

    // propriete si elle existe, sinon champ (SoulsFormats melange les deux)
    private static object Get(object o, string nom)
    {
        if (o == null) return null;
        object v = Prop(o, nom);
        if (v != null) return v;
        return Fld(o, nom);
    }

    // element k d'un VertexBoneWeights / VertexBoneIndices (indexeur "Item")
    private static object Index(object o, int k)
    {
        if (o == null) return null;
        PropertyInfo p = o.GetType().GetProperty("Item");
        if (p != null && p.GetIndexParameters().Length == 1)
        {
            try { return p.GetValue(o, new object[] { k }); } catch { return null; }
        }
        Array a = o as Array;
        if (a != null && k < a.Length) return a.GetValue(k);
        return null;
    }

    private static void Api(Type t, string titre)
    {
        Console.WriteLine("   " + titre + " (" + t.Name + ") :");
        foreach (PropertyInfo p in t.GetProperties())
        {
            if (p.GetIndexParameters().Length > 0) continue;
            Console.WriteLine("      prop " + p.Name + " : " + p.PropertyType.Name);
        }
        foreach (FieldInfo f in t.GetFields())
            Console.WriteLine("      champ " + f.Name + " : " + f.FieldType.Name);
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage: FlverBones.exe <flver> [emplacements]");
            return 2;
        }

        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier   : " + args[0]);
        Console.WriteLine("noeuds    : " + f.Nodes.Count.ToString(Inv));
        Console.WriteLine("maillages : " + f.Meshes.Count.ToString(Inv));

        PropertyInfo piBones = typeof(FLVER2).GetProperty("Bones");
        IList bones = null;
        if (piBones == null)
        {
            Console.WriteLine("f.Bones   : ABSENT de cette DLL");
        }
        else
        {
            bones = piBones.GetValue(f, null) as IList;
            Console.WriteLine("f.Bones   : present, " + (bones == null ? "null" : bones.Count.ToString(Inv) + " elements"));
        }

        if (bones != null && bones.Count > 0)
        {
            object b0 = bones[0];
            Api(b0.GetType(), "membres d'un os (os 0)");
            Console.WriteLine("      valeurs os 0 :");
            foreach (PropertyInfo p in b0.GetType().GetProperties())
            {
                if (p.GetIndexParameters().Length > 0) continue;
                object v = Prop(b0, p.Name);
                Console.WriteLine("         " + p.Name + " = " + (v == null ? "null" : v.ToString()));
            }
        }

        List<int> slots = new List<int>();
        if (args.Length > 1)
        {
            foreach (string s in args[1].Split(',')) slots.Add(int.Parse(s, Inv));
        }
        else
        {
            for (int i = 0; i < f.Meshes.Count; i++) slots.Add(i);
        }

        // API d'un maillage : une seule fois
        Api(f.Meshes[0].GetType(), "membres d'un maillage");
        {
            object v0 = (Prop(f.Meshes[0], "Vertices") as IList) != null && (Prop(f.Meshes[0], "Vertices") as IList).Count > 0
                ? (Prop(f.Meshes[0], "Vertices") as IList)[0] : null;
            if (v0 != null) Api(v0.GetType(), "membres d'un sommet");
        }

        foreach (int i in slots)
        {
            object m = f.Meshes[i];
            IList verts = Prop(m, "Vertices") as IList;
            object matIdx = Prop(m, "MaterialIndex");
            object dyn = Prop(m, "Dynamic");
            IList pal = Prop(m, "BoneIndices") as IList;

            Console.WriteLine();
            Console.WriteLine("== emplacement " + i.ToString(Inv)
                + " : " + (verts == null ? "?" : verts.Count.ToString(Inv)) + " sommets"
                + ", materiau " + (matIdx == null ? "?" : matIdx.ToString())
                + ", Dynamic=" + (dyn == null ? "?" : dyn.ToString()));

            Console.WriteLine("   palette (Mesh.BoneIndices) : " + (pal == null ? "ABSENTE/null" : pal.Count.ToString(Inv) + " entrees"));
            if (pal != null && pal.Count > 0)
            {
                string debut = "";
                for (int k = 0; k < pal.Count && k < 40; k++) debut += Convert.ToString(pal[k], Inv) + " ";
                Console.WriteLine("      debut : " + debut);
            }
            if (verts == null) continue;

            SortedDictionary<int, int> hist = new SortedDictionary<int, int>();
            foreach (object vo in verts)
            {
                object bw = Get(vo, "BoneWeights");
                object bi = Get(vo, "BoneIndices");
                if (bw == null || bi == null)
                {
                    Console.WriteLine("   !! BoneWeights=" + (bw == null ? "introuvable" : "ok") + "  BoneIndices=" + (bi == null ? "introuvable" : "ok"));
                    break;
                }
                for (int k = 0; k < 4; k++)
                {
                    object wo = Index(bw, k);
                    if (wo == null) continue;
                    float w = Convert.ToSingle(wo, Inv);
                    if (w <= 0f) continue;
                    object io = Index(bi, k);
                    int idx = io == null ? -1 : Convert.ToInt32(io, Inv);
                    int c; hist.TryGetValue(idx, out c); hist[idx] = c + 1;
                }
            }

            Console.WriteLine("   index d'os distincts (poids>0) : " + hist.Count.ToString(Inv));
            if (hist.Count == 0) continue;

            int mn = int.MaxValue, mx = int.MinValue;
            foreach (int k in hist.Keys) { if (k < mn) mn = k; if (k > mx) mx = k; }
            Console.WriteLine("      min=" + mn.ToString(Inv) + "  max=" + mx.ToString(Inv));

            int horsBones = 0, horsNodes = 0, decale = 0;
            foreach (int k in hist.Keys)
            {
                if (bones != null && (k < 0 || k >= bones.Count)) horsBones++;
                if (k < 0 || k >= f.Nodes.Count) horsNodes++;
                if (bones != null && k >= 0 && k < bones.Count)
                {
                    object nv = Prop(bones[k], "NodeIndex");
                    if (nv is int && (int)nv != k) decale++;
                }
            }
            Console.WriteLine("      hors f.Bones=" + horsBones.ToString(Inv)
                + "  hors f.Nodes=" + horsNodes.ToString(Inv)
                + "  Bones[k].NodeIndex != k pour " + decale.ToString(Inv) + " index distincts");

            int n = 0;
            foreach (KeyValuePair<int, int> kv in hist)
            {
                if (n++ >= 25) break;
                string viaNode = (kv.Key >= 0 && kv.Key < f.Nodes.Count) ? f.Nodes[kv.Key].Name : "!! HORS BORNES !!";
                string viaBone = "-";
                if (bones != null && kv.Key >= 0 && kv.Key < bones.Count)
                {
                    object bn = bones[kv.Key];
                    object pn = Prop(bn, "NodeIndex");
                    object pm = Prop(bn, "Name");
                    string nm = pm == null ? "?" : pm.ToString();
                    int nd = pn is int ? (int)pn : -1;
                    string nn = (nd >= 0 && nd < f.Nodes.Count) ? f.Nodes[nd].Name : "!!";
                    viaBone = nm + " (noeud " + nd.ToString(Inv) + "=" + nn + ")";
                }
                Console.WriteLine("      os " + kv.Key.ToString(Inv).PadLeft(4) + " (" + kv.Value.ToString(Inv) + " sommets) : Nodes[]=" + viaNode + "   Bones[]=" + viaBone);
            }
        }

        return 0;
    }
}
