// FlverLayouts - liste les membres de chaque agencement de sommets d'un FLVER
// (flux, type, semantique, index, taille, modificateur) par reflexion. C'est la
// source de verite pour savoir ce que contient chaque champ d'une disposition :
// c'est ce qui dit si "UV:Short4" est un ou deux jeux d'UV, et sous quel nom.
//
// Usage : FlverLayouts.exe modele.flver
using System;
using System.Collections;
using System.Linq;
using System.Reflection;
using System.Text;
using SoulsFormats;

internal static class FlverLayouts
{
    private static object Membres(object bl)
    {
        Type t = bl.GetType();
        PropertyInfo p = t.GetProperty("Members");
        if (p != null) return p.GetValue(bl, null);
        p = t.GetProperty("LayoutMembers");
        if (p != null) return p.GetValue(bl, null);
        FieldInfo fi = t.GetField("Members");
        if (fi != null) return fi.GetValue(bl);
        return null;
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverLayouts.exe modele.flver"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("type d'un agencement : " + typeof(FLVER2.BufferLayout).FullName);
        Console.WriteLine();
        for (int i = 0; i < f.BufferLayouts.Count; i++)
        {
            object bl = f.BufferLayouts[i];
            object taille = null;
            PropertyInfo pt = bl.GetType().GetProperty("Size");
            if (pt != null) taille = pt.GetValue(bl, null);
            Console.WriteLine("agencement[" + i + "]  taille = " + taille);
            object ms = Membres(bl);
            var liste = ms as IEnumerable;
            if (liste == null) liste = bl as IEnumerable;   // BufferLayout HERITE de List<LayoutMember>
            if (liste == null)
            {
                Console.WriteLine("   (membres introuvables)");
                continue;
            }
            int k = 0;
            foreach (object m in liste)
            {
                var sb = new StringBuilder("   [" + k + "] ");
                foreach (PropertyInfo q in m.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
                {
                    object v;
                    try { v = q.GetValue(m, null); } catch { v = "?"; }
                    sb.Append(q.Name).Append('=').Append(v).Append("   ");
                }
                Console.WriteLine(sb.ToString().TrimEnd());
                k++;
            }
            Console.WriteLine();
        }

        Console.WriteLine("maillages : [i] mat noeud | tampons (LayoutIndex, VertexSize, VertexCount, BufferIndex) | nSommets dyn poids");
        for (int i = 0; i < f.Meshes.Count; i++)
        {
            FLVER2.Mesh m = f.Meshes[i];
            var sb = new StringBuilder();
            foreach (FLVER2.VertexBuffer vb in m.VertexBuffers)
                sb.Append("(").Append(Dump(vb)).Append(")  ");
            Console.WriteLine(string.Format("  [{0,2}] {1,3} {2,5} | {3}| {4} {5} {6}",
                i, m.MaterialIndex, m.NodeIndex, sb.ToString().PadRight(30),
                m.Vertices.Count, m.Dynamic, m.UseBoneWeights));
        }
        return 0;
    }

    private static object Lire(object o, string nom)
    {
        Type t = o.GetType();
        PropertyInfo p = t.GetProperty(nom);
        if (p != null) return p.GetValue(o, null);
        FieldInfo fi = t.GetField(nom);
        if (fi != null) return fi.GetValue(o);
        return "?";
    }

    // affiche TOUS les champs/proprietes publiques d'un objet : c'est ce qui dit
    // ce que le moteur recoit vraiment (taille d'un sommet, nombre de sommets...).
    private static string Dump(object o)
    {
        var sb = new StringBuilder();
        Type t = o.GetType();
        foreach (PropertyInfo p in t.GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            if (p.GetIndexParameters().Length > 0) continue;
            object v; try { v = p.GetValue(o, null); } catch { v = "?"; }
            if (v is System.Collections.ICollection) continue;
            sb.Append(p.Name).Append('=').Append(v).Append(' ');
        }
        foreach (FieldInfo fi in t.GetFields(BindingFlags.Public | BindingFlags.Instance))
        {
            object v; try { v = fi.GetValue(o); } catch { v = "?"; }
            sb.Append(fi.Name).Append('=').Append(v).Append(' ');
        }
        return sb.ToString().TrimEnd();
    }
}
