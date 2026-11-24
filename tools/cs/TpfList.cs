// TpfList.exe -- lecture (et extraction) d'un TPF, via SoulsFormats.
//
// Un TPF est une archive de textures : chaque entree porte un NOM (souvent le
// nom de fichier attendu par les materiaux), un format DDS et les octets d'un
// fichier DDS complet. On s'en sert pour decouvrir quels noms de textures un
// personnage utilise, et pour reconstruire un TPF de remplacement.
//
// Usage :
//   TpfList.exe <fichier.tpf|.tpf.dcx> [filtre]           -> liste
//   TpfList.exe <fichier.tpf|.tpf.dcx> [filtre] --extraire <dossier>
//                                                          -> ecrit les .dds
//
// Lecture seule sur l'entree.
using System;
using System.Globalization;
using System.IO;
using SoulsFormats;

internal static class TpfList
{
    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage: TpfList.exe <fichier.tpf|.tpf.dcx> [filtre] [--extraire <dossier>]");
            return 2;
        }
        string chemin = args[0];
        string filtre = null;
        string dossier = null;
        for (int i = 1; i < args.Length; i++)
        {
            if (args[i] == "--extraire" && i + 1 < args.Length) { dossier = args[i + 1]; i++; }
            else if (filtre == null) filtre = args[i];
        }

        TPF tpf = TPF.Read(chemin);
        Console.WriteLine("fichier   : " + chemin);
        Console.WriteLine("textures  : " + tpf.Textures.Count + (tpf.Compression != null ? "   compression : " + tpf.Compression : ""));
        if (dossier != null) Directory.CreateDirectory(dossier);

        int n = 0;
        long octets = 0;
        foreach (TPF.Texture t in tpf.Textures)
        {
            octets += t.Bytes.Length;
            if (filtre != null && t.Name.IndexOf(filtre, StringComparison.OrdinalIgnoreCase) < 0) continue;
            n++;
            Console.WriteLine(string.Format(CultureInfo.InvariantCulture,
                "  {0,-44} {1,-12} {2,9} o  flags1=0x{3:X}",
                t.Name, t.Format.ToString(), t.Bytes.Length, t.Flags1));
            if (dossier != null)
            {
                string nom = t.Name.Replace('/', '_').Replace('\\', '_');
                if (!nom.EndsWith(".dds", StringComparison.OrdinalIgnoreCase)) nom += ".dds";
                File.WriteAllBytes(Path.Combine(dossier, nom), t.Bytes);
            }
        }
        Console.WriteLine("affichees  : " + n + "   total octets textures : " + octets);
        return 0;
    }
}
