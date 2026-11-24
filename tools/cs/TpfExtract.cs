// Extrait les DDS embarques dans un TPF avec SoulsFormats.
// Usage: TpfExtract.exe <entree.tpf> <dossier_sortie>
using System;
using System.IO;
using SoulsFormats;

internal static class TpfExtract
{
    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("usage: TpfExtract.exe <entree.tpf> <dossier_sortie>");
            return 2;
        }
        Directory.CreateDirectory(args[1]);
        TPF tpf = TPF.Read(args[0]);
        Console.WriteLine("textures : " + tpf.Textures.Count);
        foreach (TPF.Texture tex in tpf.Textures)
        {
            if (tex.Bytes == null || tex.Bytes.Length == 0) continue;
            string name = Path.GetFileNameWithoutExtension(tex.Name);
            if (String.IsNullOrWhiteSpace(name)) continue;
            string path = Path.Combine(args[1], name + ".dds");
            File.WriteAllBytes(path, tex.Bytes);
            Console.WriteLine("  " + tex.Name + " -> " + path + " (" + tex.Bytes.Length + " bytes)");
        }
        return 0;
    }
}
