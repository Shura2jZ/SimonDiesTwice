// MtdDump.exe -- imprime le contenu d'un MTD (shader, textures, params).
using System;
using SoulsFormats;

internal static class MtdDump
{
    private static int Main(string[] args)
    {
        MTD m = MTD.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("ShaderPath : " + m.ShaderPath);
        Console.WriteLine("Description : " + m.Description);
        Console.WriteLine("Textures (" + m.Textures.Count + ") :");
        foreach (MTD.Texture t in m.Textures)
            Console.WriteLine("  Type=" + t.Type + "  Path=" + t.Path + "  UV=" + t.UVNumber + "  Ext=" + t.Extended);
        Console.WriteLine("Params (" + m.Params.Count + ") :");
        foreach (MTD.Param p in m.Params)
            Console.WriteLine("  " + p.Name + " = " + p.Value + "  (" + p.Type + ")");
        return 0;
    }
}
