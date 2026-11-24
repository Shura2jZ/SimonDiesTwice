// FlverTampons - affiche les enregistrements de tampon de sommets de chaque
// maillage : BufferIndex, LayoutIndex, VertexSize, VertexCount, BufferOffset,
// BufferLength.
//
// Raison : l'injecteur cree ses tampons avec `new FLVER2.VertexBuffer(layout)`,
// donc tous les autres champs gardent leur valeur par defaut (0). Or SoulsFormats
// recalcule la taille de sommet a partir du layout a la relecture : une sonde
// verrait donc des donnees saines meme si le champ ecrit dans le fichier est
// faux. Le moteur, lui, lit ce champ. C'est un candidat direct au defaut
// "tout est sain hors jeu, le rendu explose en jeu".
//
// Usage : FlverTampons.exe <flver> [emplacements]
using System;
using System.Globalization;
using System.Reflection;
using SoulsFormats;

internal static class FlverTampons
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static object Champ(object o, Type t, string nom)
    {
        FieldInfo fi = t.GetField(nom, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (fi != null) return fi.GetValue(o);
        PropertyInfo pi = t.GetProperty(nom, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (pi != null) return pi.GetValue(o, null);
        return null;
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage: FlverTampons.exe <flver> [emplacements]");
            return 2;
        }
        FLVER2 f = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0] + "   (" + f.Meshes.Count + " maillages)");

        int[] voulus = null;
        if (args.Length > 1)
        {
            string[] p = args[1].Split(',');
            voulus = new int[p.Length];
            for (int i = 0; i < p.Length; i++) voulus[i] = int.Parse(p[i], Inv);
        }

        // d'abord : quels champs porte un VertexBuffer dans ce fork ?
        object premier = f.Meshes[0].VertexBuffers[0];
        Type tv = premier.GetType();
        Console.WriteLine("type tampon : " + tv.FullName);
        Console.WriteLine("champs      :");
        foreach (FieldInfo fi in tv.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
        {
            Console.WriteLine("   " + (fi.IsPublic ? "PUB  " : "priv ") + fi.Name + " : " + fi.FieldType.Name);
        }
        foreach (PropertyInfo pi in tv.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
        {
            Console.WriteLine("   PROP " + pi.Name + " : " + pi.PropertyType.Name);
        }
        Console.WriteLine();

        Console.WriteLine(" idx  buf  layout  (calc)   VertexSize  VertexCount   BufferOffset   BufferLength");

        foreach (FLVER2.Mesh m in f.Meshes)
        {
            int idx = f.Meshes.IndexOf(m);
            if (voulus != null && Array.IndexOf(voulus, idx) < 0) continue;
            foreach (object vb in m.VertexBuffers)
            {
                Type t = vb.GetType();
                object bi = Champ(vb, t, "BufferIndex");
                object li = Champ(vb, t, "LayoutIndex");
                object vs = Champ(vb, t, "VertexSize");
                object vc = Champ(vb, t, "VertexCount");
                object bo = Champ(vb, t, "BufferOffset");
                object bl = Champ(vb, t, "BufferLength");
                int layoutIdx = li == null ? -1 : Convert.ToInt32(li);
                int tailleLayout = 0;
                if (layoutIdx >= 0 && layoutIdx < f.BufferLayouts.Count)
                {
                    foreach (object membre in f.BufferLayouts[layoutIdx])
                    {
                        Type tmi = membre.GetType();
                        object tz = Champ(membre, tmi, "Type");
                        object sm = Champ(membre, tmi, "Semantic");
                        int mt = Convert.ToInt32(tz);
                        tailleLayout += tailleMembre(mt);
                    }
                }
                Console.WriteLine("{0,4} {1,4} {2,4} (calc {3,3}) {4,8} {5,8} {6,10} {7,10}   {8}"
                    , idx
                    , bi == null ? "?" : bi.ToString()
                    , layoutIdx
                    , tailleLayout
                    , vs == null ? "?" : vs.ToString()
                    , vc == null ? "?" : vc.ToString()
                    , bo == null ? "?" : bo.ToString()
                    , bl == null ? "?" : bl.ToString()
                    , "");
            }
        }
        return 0;
    }

    // taille en octets d'un membre de layout, selon son type
    private static int tailleMembre(int t)
    {
        // SoulsFormats.LayoutMemberType : 0 = Float1 ... 19 = EdgeCompressed
        switch (t)
        {
            case 0: return 4;    // Float1
            case 1: return 8;    // Float2
            case 2: return 12;   // Float3
            case 3: return 16;   // Float4
            case 4: return 4;    // Color (4 bytes)  [UByte4]
            case 5: return 4;    // UByte4
            case 6: return 4;    // Byte4 / UByte4Norm
            case 7: return 4;    // Short2
            case 8: return 8;    // Short4
            case 9: return 4;    // Byte4A
            case 10: return 4;   // Byte4B
            case 11: return 4;   // Short2toFloat2
            case 12: return 4;   // Byte4C
            case 13: return 4;   // UByte4Norm
            case 14: return 8;   // UByte8
            case 15: return 8;   // Short4Norm
            case 16: return 8;   // Byte8
            case 17: return 4;   // Short2Norm
            case 18: return 4;   // UByte2
            case 19: return 0;   // EdgeCompressed : variable
            default: return -1;
        }
    }
}
