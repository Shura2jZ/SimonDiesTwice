// TpfDxgi.exe -- imprime pour les textures nommees : format octet, DXGI, dimensions, mips.
using System;
using System.Linq;
using SoulsFormats;

internal static class TpfDxgi
{
    private static int Main(string[] args)
    {
        if (args.Length < 2) { Console.WriteLine("usage: TpfDxgi.exe <tpf> <nom1> [nom2...]"); return 2; }
        TPF tpf = TPF.Read(args[0]);
        var noms = new System.Collections.Generic.List<string>(args);
        noms.RemoveAt(0);
        foreach (TPF.Texture t in tpf.Textures)
        {
            bool trouve = false;
            foreach (string n in noms) if (string.Equals(n, t.Name, StringComparison.OrdinalIgnoreCase)) { trouve = true; break; }
            if (!trouve) continue;
            var h = t.Header;
            Console.WriteLine("{0,-20} fmt={1,-4} dxgi={2,-4} {3}x{4} mips={5} unk1={6} unk2={7}",
                t.Name, t.Format, h == null ? -1 : h.DXGIFormat, h == null ? 0 : h.Width, h == null ? 0 : h.Height,
                t.Mipmaps, h == null ? 0 : h.Unk1, h == null ? 0 : h.Unk2);
        }
        return 0;
    }
}
