// FlverSquelettes - vide l'ENSEMBLE DES SQUELETTES d'un FLVER (SkeletonSet).
//
// C'est la seule structure du fichier que nos sondes n'avaient jamais lue.
// D'apres SoulsFormats, elle contient deux listes plates d'os : BaseSkeleton et
// AllSkeletons. On veut savoir si ces listes sont de simples copies de la liste
// des noeuds, ou une palette restreinte (auquel cas les indices d'os des sommets
// pourraient etre interpretes comme des indices DANS la liste).
//
// Usage : FlverSquelettes.exe modele.flver
using System;
using System.Collections.Generic;
using System.Globalization;
using SoulsFormats;

internal static class FlverSquelettes
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverSquelettes.exe modele.flver"); return 2; }
        FLVER2 g = FLVER2.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("noeuds  : " + g.Nodes.Count);
        Console.WriteLine();

        var ss = g.Skeletons;
        if (ss == null) { Console.WriteLine("Skeletons == null"); return 0; }

        Console.WriteLine("BaseSkeleton : " + (ss.BaseSkeleton == null ? "null" : ss.BaseSkeleton.Count.ToString()));
        Console.WriteLine("AllSkeletons : " + (ss.AllSkeletons == null ? "null" : ss.AllSkeletons.Count.ToString()));
        Console.WriteLine();

        if (ss.BaseSkeleton != null)
        {
            Console.WriteLine("--- BaseSkeleton (20 premiers) ---");
            for (int i = 0; i < Math.Min(20, ss.BaseSkeleton.Count); i++)
                Console.WriteLine("  [" + i.ToString("D3", Inv) + "] " + Decrire(ss.BaseSkeleton[i], g));
            Console.WriteLine();
            Console.WriteLine("  est-ce exactement la liste des noeuds 0..N-1 ?");
            bool oui = ss.BaseSkeleton.Count == g.Nodes.Count;
            for (int i = 0; i < ss.BaseSkeleton.Count && oui; i++)
                if (ss.BaseSkeleton[i].NodeIndex != i) oui = false;
            Console.WriteLine("    -> " + (oui ? "OUI (copie de la liste des noeuds)" : "NON (liste differente)"));
            Console.WriteLine();
        }

        if (ss.AllSkeletons != null)
        {
            Console.WriteLine("--- AllSkeletons (20 premiers) ---");
            for (int i = 0; i < Math.Min(20, ss.AllSkeletons.Count); i++)
                Console.WriteLine("  [" + i.ToString("D3", Inv) + "] " + Decrire(ss.AllSkeletons[i], g));
            Console.WriteLine();
            Console.WriteLine("  est-ce exactement la liste des noeuds 0..N-1 ?");
            bool oui = ss.AllSkeletons.Count == g.Nodes.Count;
            for (int i = 0; i < ss.AllSkeletons.Count && oui; i++)
                if (ss.AllSkeletons[i].NodeIndex != i) oui = false;
            Console.WriteLine("    -> " + (oui ? "OUI (copie de la liste des noeuds)" : "NON (liste differente)"));
            // doublons ?
            var vus = new Dictionary<int, int>();
            foreach (var b in ss.AllSkeletons)
            {
                if (!vus.ContainsKey(b.NodeIndex)) vus[b.NodeIndex] = 0;
                vus[b.NodeIndex]++;
            }
            int doub = 0;
            foreach (var kv in vus) if (kv.Value > 1) doub++;
            Console.WriteLine("  index distincts : " + vus.Count + " ; indexes apparaissant plusieurs fois : " + doub);
            // les index de noeud sont-ils tous < Nodes.Count ?
            int hors = 0;
            foreach (var b in ss.AllSkeletons) if (b.NodeIndex < 0 || b.NodeIndex >= g.Nodes.Count) hors++;
            Console.WriteLine("  NodeIndex hors de la liste des noeuds : " + hors);
            Console.WriteLine();
        }

        // Recoupement avec les maillages : la question est de savoir si la liste
        // d'os d'un maillage correspond a ses sommets.
        Console.WriteLine("=== recoupement maillages / squelette ===");
        for (int mi = 0; mi < g.Meshes.Count; mi++)
        {
            var mesh = g.Meshes[mi];
            var utilises = new SortedSet<int>();
            foreach (var v in mesh.Vertices)
                for (int b = 0; b < 4; b++)
                    if (v.BoneWeights[b] > 0f && v.BoneIndices[b] != 0) utilises.Add(v.BoneIndices[b]);
            int hors = 0;
            foreach (int u in utilises) if (u >= ss.AllSkeletons.Count) hors++;
            Console.WriteLine(string.Format(Inv, "[{0,2}] {1,-26} sommets : {2,2} os distincts, max {3,3}  | AllSkeletons.Count {4}",
                mi, g.Nodes[mesh.NodeIndex].Name, utilises.Count, Max(utilises), ss.AllSkeletons.Count));
        }
        return 0;
    }

    private static int Max(SortedSet<int> s)
    {
        int m = -1;
        foreach (int x in s) m = Math.Max(m, x);
        return m;
    }

    private static string Decrire(FLVER2.SkeletonSet.Bone b, FLVER2 g)
    {
        if (b == null) return "<null>";
        string nom = (b.NodeIndex >= 0 && b.NodeIndex < g.Nodes.Count) ? g.Nodes[b.NodeIndex].Name : "?";
        return string.Format(Inv, "NodeIndex={0,-4} ({1,-24}) Parent={2,-4} 1erEnfant={3,-4} frereSuiv={4,-4} frerePrec={5}",
            b.NodeIndex, nom, b.ParentIndex, b.FirstChildIndex, b.NextSiblingIndex, b.PreviousSiblingIndex);
    }
}
