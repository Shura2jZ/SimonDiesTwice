// TaeMask - extrait du .tae les evenements qui portent un masque de dessin
// (ChangeDrawMask, ModelMask, HideModelMask) et montre la taille des masques en
// octets et en bits. Sert a savoir si les animations attendent 33 maillages.
//
// Usage : TaeMask.exe <fichier.tae> [maxAnimations]
using System;
using System.Collections.Generic;
using System.Globalization;
using SoulsFormats;

internal static class TaeMask
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static string Bits(byte[] masque)
    {
        if (masque == null) return "(null)";
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        for (int i = masque.Length - 1; i >= 0; i--)
        {
            for (int b = 7; b >= 0; b--)
                sb.Append(((masque[i] >> b) & 1) != 0 ? '1' : '0');
        }
        return sb.ToString();
    }

    private static string Hex(byte[] masque)
    {
        if (masque == null) return "(null)";
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        for (int i = 0; i < masque.Length; i++) sb.Append(masque[i].ToString("X2", Inv));
        return sb.ToString();
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage: TaeMask.exe <fichier.tae> [maxAnimations]");
            return 2;
        }
        int maxAnim = args.Length > 1 ? int.Parse(args[1], Inv) : 400;

        TAE3 tae;
        try { tae = TAE3.Read(args[0]); }
        catch (Exception e) { Console.WriteLine("lecture impossible : " + e.Message); return 1; }

        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("animations : " + tae.Animations.Count);
        Console.WriteLine();

        // longueurs de masque rencontrees
        SortedDictionary<int, int> tailles = new SortedDictionary<int, int>();
        SortedDictionary<int, int> taillesModel = new SortedDictionary<int, int>();
        SortedDictionary<int, int> taillesHide = new SortedDictionary<int, int>();
        int nbCdm = 0, nbModel = 0, nbHide = 0;
        int montrees = 0;

        foreach (TAE3.Animation a in tae.Animations)
        {
            foreach (TAE3.Event e in a.Events)
            {
                TAE3.Event.ChangeDrawMask cdm = e as TAE3.Event.ChangeDrawMask;
                TAE3.Event.ModelMask mm = e as TAE3.Event.ModelMask;
                TAE3.Event.HideModelMask hm = e as TAE3.Event.HideModelMask;

                if (cdm != null)
                {
                    nbCdm++;
                    int n = cdm.DrawMask == null ? -1 : cdm.DrawMask.Length;
                    if (!tailles.ContainsKey(n)) tailles[n] = 0;
                    tailles[n]++;
                    if (montrees < maxAnim && nbCdm <= 25)
                    {
                        Console.WriteLine(string.Format(Inv,
                            "ChangeDrawMask  anim id {0,6}  t {1,7:F3}..{2,7:F3}  {3} octets ({4} bits)  {5}  bits={6}",
                            a.ID, cdm.StartTime, cdm.EndTime, n, n * 8, Hex(cdm.DrawMask), Bits(cdm.DrawMask)));
                        montrees++;
                    }
                }
                if (mm != null)
                {
                    nbModel++;
                    int n = mm.Mask == null ? -1 : mm.Mask.Length;
                    if (!taillesModel.ContainsKey(n)) taillesModel[n] = 0;
                    taillesModel[n]++;
                }
                if (hm != null)
                {
                    nbHide++;
                    int n = hm.Mask == null ? -1 : hm.Mask.Length;
                    if (!taillesHide.ContainsKey(n)) taillesHide[n] = 0;
                    taillesHide[n]++;
                }
            }
        }

        Console.WriteLine();
        Console.WriteLine("ChangeDrawMask : " + nbCdm + " evenements, tailles (octets) :");
        foreach (KeyValuePair<int, int> kv in tailles)
            Console.WriteLine("   " + kv.Key + " octets (" + (kv.Key * 8) + " bits) : " + kv.Value + " fois");
        Console.WriteLine("ModelMask      : " + nbModel + " evenements, tailles :");
        foreach (KeyValuePair<int, int> kv in taillesModel)
            Console.WriteLine("   " + kv.Key + " octets (" + (kv.Key * 8) + " bits) : " + kv.Value + " fois");
        Console.WriteLine("HideModelMask  : " + nbHide + " evenements, tailles :");
        foreach (KeyValuePair<int, int> kv in taillesHide)
            Console.WriteLine("   " + kv.Key + " octets (" + (kv.Key * 8) + " bits) : " + kv.Value + " fois");
        return 0;
    }
}
