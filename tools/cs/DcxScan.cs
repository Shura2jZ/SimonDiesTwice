// DcxScan.exe -- que contiennent ces fichiers .dcx ? (TPF, BND4, FLVER, autre)
//
// But : retrouver les textures d'un personnage. Les index d'archives Data*.bhd
// sont chiffres, donc on ne peut pas lire la liste des chemins ; en revanche le
// dossier _unknown du jeu contient des fichiers .dcx extraits sans nom. On les
// ouvre un par un et on regarde ce qu'ils sont, en signalant ceux qui parlent
// du personnage cherche.
//
// Usage :
//   DcxScan.exe <dossier> [motif]        (motif par defaut : c5400)
//
// Lecture seule.
using System;
using System.Collections.Generic;
using System.IO;
using SoulsFormats;

internal static class DcxScan
{
    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("usage: DcxScan.exe <dossier> [motif]");
            return 2;
        }
        string dossier = args[0];
        string motif = args.Length > 1 ? args[1] : "c5400";

        string[] fichiers = Directory.GetFiles(dossier);
        Array.Sort(fichiers);
        Console.WriteLine("dossier : " + dossier + "   fichiers : " + fichiers.Length + "   motif : " + motif);

        var compte = new Dictionary<string, int>();
        var interessants = new List<string>();

        foreach (string chemin in fichiers)
        {
            string nom = Path.GetFileName(chemin);
            try
            {
                byte[] brut = File.ReadAllBytes(chemin);
                byte[] donnees = brut;
                if (brut.Length > 4 && brut[0] == 'D' && brut[1] == 'C' && brut[2] == 'X' && brut[3] == 0)
                {
                    donnees = DCX.Decompress(brut);
                }

                string genre = Classer(donnees, motif, interessants, nom);
                if (!compte.ContainsKey(genre)) compte[genre] = 0;
                compte[genre]++;
            }
            catch (Exception e)
            {
                string g = "ERREUR (" + e.GetType().Name + ")";
                if (!compte.ContainsKey(g)) compte[g] = 0;
                compte[g]++;
            }
        }

        Console.WriteLine();
        foreach (var paire in compte) Console.WriteLine("  " + paire.Key + " : " + paire.Value);

        if (interessants.Count > 0)
        {
            Console.WriteLine();
            Console.WriteLine("fichiers contenant le motif :");
            foreach (string ligne in interessants) Console.WriteLine("  " + ligne);
        }
        return 0;
    }

    private static string Classer(byte[] d, string motif, List<string> interessants, string nom)
    {
        if (d.Length < 4) return "trop court";

        if (d[0] == 'T' && d[1] == 'P' && d[2] == 'F' && d[3] == 0)
        {
            using (var ms = new MemoryStream(d))
            {
                TPF t = TPF.Read(ms);
                var noms = new List<string>();
                foreach (TPF.Texture tex in t.Textures) noms.Add(tex.Name ?? "");
                string trouve = "";
                foreach (string n in noms)
                {
                    if (motif.Length > 0 && n.IndexOf(motif, StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        trouve = "   <<< contient " + motif + " : " + n;
                        break;
                    }
                }
                if (trouve != "") interessants.Add(nom + "  TPF " + t.Textures.Count + " textures" + trouve);
                return "TPF (" + t.Textures.Count + " textures)" + trouve;
            }
        }

        if (d[0] == 'B' && d[1] == 'N' && d[2] == 'D' && d[3] == 4)
        {
            using (var ms = new MemoryStream(d))
            {
                BND4 b = BND4.Read(ms);
                string apercu = b.Files.Count > 0 ? b.Files[0].Name : "";
                bool touche = false;
                foreach (var f in b.Files)
                {
                    if (motif.Length > 0 && f.Name != null &&
                        f.Name.IndexOf(motif, StringComparison.OrdinalIgnoreCase) >= 0) { touche = true; break; }
                }
                if (touche) interessants.Add(nom + "  BND4 " + b.Files.Count + " entrees");
                return "BND4 (" + b.Files.Count + " entrees)" + (touche ? "  <<< contient " + motif : "");
            }
        }

        if (d[0] == 'F' && d[1] == 'L' && d[2] == 'V' && d[3] == 'E') return "FLVER";
        if (d[0] == 'T' && d[1] == 'A' && d[2] == 'E' && d[3] == 0) return "TAE";
        if (d.Length > 0x54 && d[0] == 'H' && d[1] == 'K' && d[2] == 'X') return "HKX";

        // Dernier recours : recherche du motif dans le contenu brut.
        string texte = System.Text.Encoding.ASCII.GetString(d, 0, Math.Min(d.Length, 4096));
        if (motif.Length > 0 && System.Text.Encoding.ASCII.GetString(d).IndexOf(motif, StringComparison.OrdinalIgnoreCase) >= 0)
        {
            interessants.Add(nom + "  contenu brut (pas un conteneur connu)");
            return "contenu brut contenant " + motif;
        }
        return "autre";
    }
}
