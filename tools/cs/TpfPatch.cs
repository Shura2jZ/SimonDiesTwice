// TpfPatch.exe -- remplace ou ajoute des textures dans un TPF Sekiro.
//
// Le TPF garde ses textures existantes ; on ne touche qu'aux entrees citees
// dans le manifeste. Une entree absente est ajoutee (clone de la premiere :
// plateforme, type, drapeaux). Les octets fournis sont un DDS complet (en-tete
// DX10 inclus) ; l'en-tete du TPF est mis a jour a partir de ce DDS.
//
// Usage :
//   TpfPatch.exe <entree.tpf> <sortie.tpf> <manifeste.tsv>
//
// manifeste.tsv : une ligne par texture, colonnes separees par des tabulations
//   nom<TAB>chemin.dds<TAB>format_octet
//
// Lecture seule sur l'entree.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using SoulsFormats;

internal static class TpfPatch
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private struct EnteteDds
    {
        public int Largeur;
        public int Hauteur;
        public int Mips;
        public int Dxgi;
    }

    private static EnteteDds LireDds(byte[] d)
    {
        if (d.Length < 148 || d[0] != 'D' || d[1] != 'D' || d[2] != 'S' || d[3] != ' ')
            throw new InvalidDataException("pas un DDS");
        EnteteDds e;
        e.Hauteur = BitConverter.ToInt32(d, 12);
        e.Largeur = BitConverter.ToInt32(d, 16);
        e.Mips = BitConverter.ToInt32(d, 28);
        if (e.Mips <= 0) e.Mips = 1;
        string fourcc = Encoding.ASCII.GetString(d, 84, 4);
        e.Dxgi = fourcc == "DX10" ? BitConverter.ToInt32(d, 128) : -1;
        return e;
    }

    private static int Main(string[] args)
    {
        if (args.Length < 3)
        {
            Console.WriteLine("usage: TpfPatch.exe <entree.tpf> <sortie.tpf> <manifeste.tsv>");
            return 2;
        }

        TPF tpf = TPF.Read(args[0]);
        Console.WriteLine("entree   : " + args[0]);
        Console.WriteLine("textures : " + tpf.Textures.Count);

        string[] lignes = File.ReadAllLines(args[2], Encoding.UTF8);
        int remplacees = 0, ajoutees = 0;
        foreach (string brute in lignes)
        {
            string ligne = brute.Trim();
            if (ligne.Length == 0 || ligne.StartsWith("#")) continue;
            string[] p = ligne.Split('\t');
            if (p.Length < 3) throw new InvalidDataException("ligne invalide : " + ligne);
            string nom = p[0].Trim();
            string dds = p[1].Trim();
            byte format = byte.Parse(p[2].Trim(), Inv);

            byte[] octets = File.ReadAllBytes(dds);
            EnteteDds e = LireDds(octets);

            TPF.Texture t = tpf.Textures.Find(x =>
                string.Equals(x.Name, nom, StringComparison.OrdinalIgnoreCase));
            bool etaitNul = (t != null && t.Header == null);
            if (t == null)
            {
                TPF.Texture modele = tpf.Textures[0];
                t = new TPF.Texture(modele.Platform);
                t.Name = nom;
                t.Type = modele.Type;
                t.Flags1 = modele.Flags1;
                t.FloatStruct = modele.FloatStruct;
                // conserver le format d'en-tete de la texture modele (nul ou non)
                if (modele.Header != null)
                {
                    t.Header = new TPF.TexHeader();
                    t.Header.TextureCount = 1;
                    t.Header.Unk1 = modele.Header.Unk1;
                    t.Header.Unk2 = modele.Header.Unk2;
                    t.Header.Width = (short)e.Largeur;
                    t.Header.Height = (short)e.Hauteur;
                    t.Header.DXGIFormat = e.Dxgi;
                }
                else
                {
                    t.Header = null;
                }
                tpf.Textures.Add(t);
                ajoutees++;
            }
            else
            {
                remplacees++;
            }

            t.Format = format;
            t.Mipmaps = (byte)e.Mips;
            // ne toucher au TPF-header que si la texture en avait un a l'origine
            if (t.Header != null)
            {
                t.Header.Width = (short)e.Largeur;
                t.Header.Height = (short)e.Hauteur;
                t.Header.DXGIFormat = e.Dxgi;
            }
            t.Bytes = octets;

            Console.WriteLine(string.Format(Inv,
                "  {0,-20} {1,5}x{2,-5} mips={3,-2} dxgi={4,-3} format={5,-3} {6}",
                nom, e.Largeur, e.Hauteur, e.Mips, e.Dxgi, format,
                (t.Header != null && t.Header.DXGIFormat == e.Dxgi) ? "ok" : "header-nul"));
        }

        File.WriteAllBytes(args[1], tpf.Write());
        Console.WriteLine("sortie   : " + args[1]);
        Console.WriteLine("remplacees : " + remplacees + "   ajoutees : " + ajoutees
                          + "   total : " + tpf.Textures.Count);
        return 0;
    }
}
