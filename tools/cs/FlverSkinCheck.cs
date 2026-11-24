// FlverSkinCheck - verifie comment un FLVER indexe ses os et a quoi servent les
// noeuds "porteurs" des maillages.
//
// Questions tranchees :
//   1. les indices d'os stockes par sommet sont-ils des indices GLOBAUX dans la
//      liste des noeuds ? (comparaison avec le nombre d'os)
//   2. les noeuds porteurs de maillage (Mesh.NodeIndex, ex. 200 c5400_body5)
//      sont-ils des os deformants, ou de simples noeuds de regroupement ?
//   3. la transformation globale de ces noeuds est-elle identite ?
//
// Usage : FlverSkinCheck.exe modele.flver
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Numerics;
using SoulsFormats;

internal static class FlverSkinCheck
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    private static FLVER2 g;
    private static Matrix4x4[] g_local, g_global;
    private static bool[] g_done;

    private static Matrix4x4 Global(int i)
    {
        if (g_done[i]) return g_global[i];
        Matrix4x4 m = g_local[i];
        int p = g.Nodes[i].ParentIndex;
        if (p >= 0 && p < g.Nodes.Count && p != i) m = Matrix4x4.Multiply(m, Global(p));
        g_global[i] = m; g_done[i] = true; return m;
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverSkinCheck.exe modele.flver"); return 2; }
        g = FLVER2.Read(args[0]);
        int n = g.Nodes.Count;
        g_local = new Matrix4x4[n]; g_global = new Matrix4x4[n]; g_done = new bool[n];
        for (int i = 0; i < n; i++) g_local[i] = g.Nodes[i].ComputeLocalTransform();
        for (int i = 0; i < n; i++) Global(i);

        Console.WriteLine("os : " + n);
        Console.WriteLine();

        // --- 1. nature des noeuds porteurs ---
        var porteurs = g.Meshes.Select(m => m.NodeIndex).Distinct().OrderBy(x => x).ToList();
        Console.WriteLine("=== noeuds porteurs de maillage (Mesh.NodeIndex) ===");
        foreach (int i in porteurs)
        {
            var m = g_global[i];
            bool identite = Math.Abs(m.M11 - 1) < 1e-5 && Math.Abs(m.M22 - 1) < 1e-5 && Math.Abs(m.M33 - 1) < 1e-5
                && Math.Abs(m.M12) < 1e-5 && Math.Abs(m.M13) < 1e-5 && Math.Abs(m.M21) < 1e-5
                && Math.Abs(m.M23) < 1e-5 && Math.Abs(m.M31) < 1e-5 && Math.Abs(m.M32) < 1e-5
                && Math.Abs(m.M41) < 1e-5 && Math.Abs(m.M42) < 1e-5 && Math.Abs(m.M43) < 1e-5;
            Console.WriteLine(string.Format(Inv, "  {0,4} {1,-26} flags={2,-14} translation=({3:0.####}, {4:0.####}, {5:0.####})  globale_identite={6}",
                i, g.Nodes[i].Name, g.Nodes[i].Flags.ToString(),
                m.M41, m.M42, m.M43, identite ? "OUI" : "non"));
        }
        Console.WriteLine();

        // --- 2. indices d'os stockes par sommet ---
        Console.WriteLine("=== indices d'os des sommets ===");
        int globalMax = n - 1;
        for (int mi = 0; mi < g.Meshes.Count; mi++)
        {
            var mesh = g.Meshes[mi];
            int min = int.MaxValue, max = -1;
            var compte = new Dictionary<int, int>();
            foreach (var v in mesh.Vertices)
                for (int b = 0; b < 4; b++)
                {
                    float w = v.BoneWeights[b];
                    int bi = v.BoneIndices[b];
                    if (w <= 0f) continue;
                    min = Math.Min(min, bi); max = Math.Max(max, bi);
                    if (!compte.ContainsKey(bi)) compte[bi] = 0;
                    compte[bi]++;
                }
            string top = string.Join(", ", compte.OrderByDescending(kv => kv.Value).Take(8)
                .Select(kv => kv.Key + "(" + (kv.Key < n ? g.Nodes[kv.Key].Name : "?") + ")").ToArray());
            Console.WriteLine(string.Format(Inv, "[{0,2}] {1,-26} os utilises : {2} distincts   min={3} max={4}   (limite globale {5})",
                mi, g.Nodes[mesh.NodeIndex].Name, compte.Count, min, max, globalMax));
            Console.WriteLine("       principaux : " + top);
        }

        // --- 3. les noeuds porteurs apparaissent-ils comme os deformants ? ---
        Console.WriteLine();
        Console.WriteLine("=== les noeuds porteurs sont-ils utilises comme os deformants ? ===");
        foreach (int i in porteurs)
        {
            int total = 0;
            foreach (var mesh in g.Meshes)
                foreach (var v in mesh.Vertices)
                    for (int b = 0; b < 4; b++)
                        if (v.BoneWeights[b] > 0f && v.BoneIndices[b] == i) total++;
            Console.WriteLine(string.Format(Inv, "  {0,4} {1,-26} sommets ponderes : {2}", i, g.Nodes[i].Name, total));
        }
        return 0;
    }
}
