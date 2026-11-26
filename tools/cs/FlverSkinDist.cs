// FlverSkinDist.exe -- controle de coherence du skinning.
//
// Pour chaque sommet, on mesure la distance entre sa position stockee et la
// position de chaque os qui le pondere (dans la pose de reference du FLVER,
// celle que le jeu utilise comme pose de liaison).
//
// C'est cette distance qui determine l'amplitude du mouvement quand l'os
// tourne : si un sommet est a plusieurs metres de son os, il part en vrille
// des que le personnage s'anime (triangles geants a l'ecran).
//
// Le fichier d'origine sert de temoin : ses sommets sont forcement coherents
// avec ses os. Si le temoin donne de bonnes distances et le fichier modde des
// distances enormes, le probleme est dans la geometrie moddee.
//
// Usage :
//     FlverSkinDist.exe <fichier.flver> [seuil]

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Numerics;
using SoulsFormats;

internal static class FlverSkinDist
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverSkinDist.exe <fichier.flver> [seuil]"); return 2; }
        float seuil = args.Length > 1 ? float.Parse(args[1], Inv) : 0.5f;

        FLVER2 f = FLVER2.Read(args[0]);
        int n = f.Nodes.Count;
        Matrix4x4[] local = new Matrix4x4[n];
        Matrix4x4[] global = new Matrix4x4[n];
        for (int i = 0; i < n; i++) local[i] = f.Nodes[i].ComputeLocalTransform();
        for (int i = 0; i < n; i++) global[i] = Compose(f, local, global, i, new bool[n]);

        Vector3[] posOs = new Vector3[n];
        for (int i = 0; i < n; i++) posOs[i] = new Vector3(global[i].M41, global[i].M42, global[i].M43);

        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("os      : " + n + "   maillages : " + f.Meshes.Count);

        double sommeMax = 0;
        int total = 0, horsSeuil = 0, poidsNuls = 0, osHorsPlage = 0;
        int[] tranches = new int[12];
        var pires = new List<string>();

        for (int mi = 0; mi < f.Meshes.Count; mi++)
        {
            FLVER2.Mesh m = f.Meshes[mi];
            double maxM = 0;
            int horsM = 0;
            foreach (FLVER.Vertex v in m.Vertices)
            {
                total++;
                float somme = 0;
                double dmax = 0;
                string quel = "";
                for (int k = 0; k < 4; k++)
                {
                    int b = v.BoneIndices[k];
                    float w = v.BoneWeights[k];
                    if (b < 0 || b >= n)
                    {
                        if (w != 0) osHorsPlage++;
                        continue;
                    }
                    if (w <= 0.001f) continue;
                    somme += w;
                    float d = (v.Position - posOs[b]).Length();
                    if (d > dmax) { dmax = d; quel = b + ":" + f.Nodes[b].Name + " (poids " + w.ToString("0.###", Inv) + ")"; }
                }
                if (somme <= 0.001f) { poidsNuls++; continue; }
                if (dmax > maxM) maxM = dmax;
                if (dmax > seuil)
                {
                    horsM++;
                    if (pires.Count < 15)
                    {
                        pires.Add("      maillage " + mi + "  dist " + dmax.ToString("0.###", Inv)
                                  + " m  sommet (" + v.Position.X.ToString("0.###", Inv) + ", "
                                  + v.Position.Y.ToString("0.###", Inv) + ", "
                                  + v.Position.Z.ToString("0.###", Inv) + ")  os " + quel);
                    }
                }
                int t = (int)(dmax / 0.5);
                if (t > 11) t = 11;
                tranches[t]++;
            }
            if (horsM > 0 || mi < 6)
            {
                Console.WriteLine("  maillage " + mi + " : " + m.Vertices.Count + " sommets, "
                                  + "distance max " + maxM.ToString("0.###", Inv) + " m, "
                                  + horsM + " sommets au-dela de " + seuil.ToString("0.##", Inv) + " m");
            }
            if (maxM > sommeMax) sommeMax = maxM;
            horsSeuil += horsM;
        }

        Console.WriteLine();
        Console.WriteLine("sommets                   : " + total);
        Console.WriteLine("distance max              : " + sommeMax.ToString("0.###", Inv) + " m");
        Console.WriteLine("sans poids utilisable     : " + poidsNuls);
        Console.WriteLine("poids sur os hors plage   : " + osHorsPlage);
        Console.WriteLine("sommets au-dela du seuil  : " + horsSeuil + "  (seuil "
                          + seuil.ToString("0.##", Inv) + " m)");
        Console.WriteLine("repartition des distances (tranches de 0,5 m) :");
        for (int t = 0; t < 12; t++)
        {
            if (tranches[t] == 0) continue;
            Console.WriteLine("   " + (t < 11 ? (t * 0.5f).ToString("0.0", Inv) + "-" + ((t + 1) * 0.5f).ToString("0.0", Inv) + " m"
                                             : ">= 5,5 m") + " : " + tranches[t]);
        }
        if (pires.Count > 0)
        {
            Console.WriteLine("pires sommets :");
            foreach (string s in pires) Console.WriteLine(s);
        }
        else
        {
            Console.WriteLine("aucun sommet au-dela du seuil.");
        }
        return 0;
    }

    private static Matrix4x4 Compose(FLVER2 f, Matrix4x4[] local, Matrix4x4[] global, int i, bool[] vus)
    {
        if (vus[i]) return global[i];
        vus[i] = true;
        Matrix4x4 m = local[i];
        int p = f.Nodes[i].ParentIndex;
        if (p >= 0 && p < f.Nodes.Count && p != i) m = Matrix4x4.Multiply(m, Compose(f, local, global, p, vus));
        global[i] = m;
        return m;
    }
}
