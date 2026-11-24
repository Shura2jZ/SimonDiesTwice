// MtdCreate.exe -- cree un MTD non-SSS pour la tete (shader kimono, textures head).
using System;
using SoulsFormats;

internal static class MtdCreate
{
    private static int Main(string[] args)
    {
        // args: <modele.mtd> <sortie.mtd>
        MTD src = MTD.Read(args[0]);
        MTD m = new MTD();
        m.ShaderPath = "N:\\NTC\\data\\Material\\sat\\OutputData\\SPX\\character_AMSN.spx";
        m.Description = src.Description;
        // copier les params (sauf ceux specifiques SSS)
        foreach (MTD.Param p in src.Params)
        {
            if (p.Name == "g_SSSWidth" || p.Name == "g_SSSStrength" || p.Name == "g_SSSStrength_UseCAParam" || p.Name.StartsWith("g_SSS")) continue;
            m.Params.Add(new MTD.Param { Name = p.Name, Type = p.Type, Value = p.Value });
        }
        // textures : albedo + normal (pas de mask SSS)
        foreach (MTD.Texture t in src.Textures)
        {
            MTD.Texture nt = new MTD.Texture();
            nt.Type = t.Type;
            nt.Extended = t.Extended;
            nt.UVNumber = t.UVNumber;
            nt.ShaderDataIndex = t.ShaderDataIndex;
            nt.UnkFloats = new System.Collections.Generic.List<float>(t.UnkFloats);
            string path = t.Path;
            path = path.Replace("c5409_kimono_a", "c5409_head_a");
            path = path.Replace("c5409_kimono_n", "c5409_head_n");
            nt.Path = path;
            // ne garder que albedo et normal (pas de mask)
            if (nt.Type.Contains("Mask1Map")) continue;
            m.Textures.Add(nt);
        }
        m.Write(args[1]);
        Console.WriteLine("ecrit : " + args[1]);
        // dump
        MTD m2 = MTD.Read(args[1]);
        Console.WriteLine("ShaderPath : " + m2.ShaderPath);
        foreach (MTD.Texture t in m2.Textures)
            Console.WriteLine("  Type=" + t.Type + " Path=" + t.Path);
        return 0;
    }
}
