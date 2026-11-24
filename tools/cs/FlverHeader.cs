// FlverHeader.exe -- deux verifications sur un FLVER :
//
//  1) affiche TOUS les champs de l'en-tete (meme internes) avec leur valeur,
//     afin de reperer un champ qu'on aurait laisse dans un etat incoherent ;
//  2) cherche dans le fichier brut comment sont encodes les indices d'un maillage
//     (16 ou 32 bits par indice) et a quel offset.
//
// La taille d'un indice est capitale : si le moteur lit des indices 16 bits dans
// un tampon ecrit en 32 bits (ou l'inverse), il lit des indices absurdes qui
// pointent hors du maillage. Resultat a l'ecran : des triangles geants qui
// relient des sommets quelconques.
//
// Usage : FlverHeader.exe <fichier.flver> [index de maillage pour la sonde]

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using SoulsFormats;

internal static class FlverHeader
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverHeader.exe <fichier.flver> [maillage]"); return 2; }
        FLVER2 f = FLVER2.Read(args[0]);
        byte[] raw = File.ReadAllBytes(args[0]);
        int mi = args.Length > 1 ? int.Parse(args[1]) : 0;

        Console.WriteLine("fichier : " + args[0] + "   " + raw.Length.ToString("N0") + " octets");

        Console.WriteLine();
        Console.WriteLine("=== champs de l'en-tete (FLVERHeader) ===");
        object h = f.Header;
        Type th = h.GetType();
        foreach (FieldInfo fi in th.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
        {
            string nom = fi.Name;
            if (nom.StartsWith("<") && nom.EndsWith(">k__BackingField"))
                nom = nom.Substring(1, nom.IndexOf('>') - 1);
            object v;
            try { v = fi.GetValue(h); } catch (Exception) { continue; }
            Console.WriteLine("    " + nom.PadRight(24) + " = " + (v == null ? "null" : v.ToString()));
        }
        foreach (PropertyInfo pi in th.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
        {
            if (pi.GetIndexParameters().Length != 0) continue;
            object v;
            try { v = pi.GetValue(h, null); } catch (Exception) { continue; }
            Console.WriteLine("    " + pi.Name.PadRight(24) + " = " + (v == null ? "null" : v.ToString()));
        }

        Console.WriteLine();
        Console.WriteLine("=== octets bruts de l'en-tete 0x28..0xA0 ===");
        for (int o = 0x28; o < 0xA0; o += 16)
        {
            if (o + 16 > raw.Length) break;
            System.Text.StringBuilder sb = new System.Text.StringBuilder();
            for (int k = 0; k < 16; k++) sb.Append(raw[o + k].ToString("X2") + " ");
            Console.WriteLine("    " + o.ToString("X4") + "  " + sb.ToString());
        }

        Console.WriteLine();
        Console.WriteLine("=== sonde d'encodage des indices (maillage " + mi + ") ===");
        FLVER2.Mesh m = f.Meshes[mi];
        Console.WriteLine("    maillage " + mi + " : sommets " + m.Vertices.Count
                          + ", facesets " + m.FaceSets.Count);
        FLVER2.FaceSet fs = m.FaceSets[0];
        Console.WriteLine("    faceset 0 : " + fs.Indices.Count + " indices");

        // On prend une tranche au milieu de la liste : elle est bien plus
        // distinctive que les premiers indices.
        int debut = fs.Indices.Count / 3;
        int n = 24;
        if (debut + n > fs.Indices.Count) debut = Math.Max(0, fs.Indices.Count - n);
        List<int> tranche = fs.Indices.GetRange(debut, n);
        System.Text.StringBuilder sbResume = new System.Text.StringBuilder();
        foreach (int x in tranche) sbResume.Append(x + " ");
        Console.WriteLine("    tranche (indices " + debut + ".." + (debut + n - 1) + ") = " + sbResume.ToString());

        byte[] p16 = new byte[n * 2];
        byte[] p32 = new byte[n * 4];
        for (int k = 0; k < n; k++)
        {
            ushort v16 = (ushort)tranche[k];
            uint v32 = (uint)tranche[k];
            p16[k * 2] = (byte)(v16 & 0xFF); p16[k * 2 + 1] = (byte)(v16 >> 8);
            p32[k * 4] = (byte)(v32 & 0xFF); p32[k * 4 + 1] = (byte)((v32 >> 8) & 0xFF);
            p32[k * 4 + 2] = (byte)((v32 >> 16) & 0xFF); p32[k * 4 + 3] = (byte)((v32 >> 24) & 0xFF);
        }

        List<int> trouves16 = Chercher(raw, p16, 12);
        List<int> trouves32 = Chercher(raw, p32, 12);
        Console.WriteLine("    occurrences en 16 bits : " + trouves16.Count
                          + (trouves16.Count > 0 ? "   premier offset 0x" + trouves16[0].ToString("X") : ""));
        Console.WriteLine("    occurrences en 32 bits : " + trouves32.Count
                          + (trouves32.Count > 0 ? "   premier offset 0x" + trouves32[0].ToString("X") : ""));
        foreach (int o in trouves16) Console.WriteLine("        16 bits @ 0x" + o.ToString("X") + "  (le maillage demande y placerait l'indice " + debut + ")");
        foreach (int o in trouves32) Console.WriteLine("        32 bits @ 0x" + o.ToString("X"));

        Console.WriteLine();
        Console.WriteLine("=== recoupement par la taille ===");
        long sommeSommets = 0;
        foreach (FLVER2.Mesh mm in f.Meshes)
        {
            int taille = 40;
            if (mm.VertexBuffers.Count > 0)
            {
                FieldInfo fv = typeof(FLVER2.VertexBuffer).GetField("VertexSize",
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                if (fv != null && mm.VertexBuffers[0] != null) taille = (int)fv.GetValue(mm.VertexBuffers[0]);
            }
            sommeSommets += (long)mm.Vertices.Count * taille;
        }
        Console.WriteLine("    somme (sommets x taille de sommet) = " + sommeSommets.ToString("N0"));
        Console.WriteLine("    dataLength                        = " + ((long)raw.Length - 0x2E0).ToString("N0") + "  (approximatif)");
        return 0;
    }

    private static List<int> Chercher(byte[] gros, byte[] motif, int max)
    {
        List<int> res = new List<int>();
        int fin = gros.Length - motif.Length;
        for (int i = 0; i <= fin; i++)
        {
            bool ok = true;
            for (int k = 0; k < motif.Length; k++)
            {
                if (gros[i + k] != motif[k]) { ok = false; break; }
            }
            if (ok)
            {
                res.Add(i);
                if (res.Count >= max) break;
            }
        }
        return res;
    }
}
