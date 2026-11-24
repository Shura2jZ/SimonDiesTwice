using System;
using SoulsFormats;

internal static class MtdVals
{
    private static int Main(string[] args)
    {
        MTD m = MTD.Read(args[0]);
        foreach (MTD.Param p in m.Params)
        {
            if (p.Name == "g_DiffuseMapColor" || p.Name == "g_SSSStrength" || p.Name == "g_SSSWidth")
            {
                Console.Write(p.Name + " = ");
                if (p.Value is float[])
                {
                    float[] fa = (float[])p.Value;
                    foreach (float f in fa) Console.Write(f.ToString("0.###") + " ");
                }
                else if (p.Value is int[])
                {
                    int[] ia = (int[])p.Value;
                    foreach (int i in ia) Console.Write(i + " ");
                }
                else
                {
                    Console.Write(p.Value);
                }
                Console.WriteLine();
            }
        }
        return 0;
    }
}
