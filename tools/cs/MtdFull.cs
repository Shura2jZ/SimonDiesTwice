// MtdFull.exe -- dumpe tous les parametres d'un MTD AVEC leurs valeurs.
using System;
using System.Collections;
using System.Collections.Generic;
using SoulsFormats;

internal static class MtdFull
{
    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: MtdFull.exe <mtd>"); return 2; }
        MTD mtd = MTD.Read(args[0]);
        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("shader  : " + mtd.ShaderPath);
        Console.WriteLine();
        foreach (MTD.Param p in mtd.Params)
        {
            object v = p.Value;
            string txt = null;
            if (v is IEnumerable && !(v is string))
            {
                List<string> parts = new List<string>();
                foreach (object item in (IEnumerable)v)
                    parts.Add(item == null ? "null" : item.ToString());
                txt = "[" + string.Join(", ", parts.ToArray()) + "]";
            }
            else if (v != null) txt = v.ToString();
            Console.WriteLine("  " + p.Name + " = " + txt + "   (" + p.Type + ")");
        }
        return 0;
    }
}
