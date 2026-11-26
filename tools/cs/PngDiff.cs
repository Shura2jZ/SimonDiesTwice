// PngDiff.exe -- compare deux images PNG pixel par pixel.
//
// Sert a verifier qu'un rendu est identique a un autre (ou a mesurer l'ecart).
//
// Usage : PngDiff.exe <a.png> <b.png>

using System;
using System.Drawing;

internal static class PngDiff
{
    private static int Main(string[] args)
    {
        if (args.Length < 2) { Console.WriteLine("usage: PngDiff.exe <a.png> <b.png>"); return 2; }
        using (Bitmap A = new Bitmap(args[0]))
        using (Bitmap B = new Bitmap(args[1]))
        {
            if (A.Width != B.Width || A.Height != B.Height)
            {
                Console.WriteLine("tailles differentes : " + A.Width + "x" + A.Height
                                  + " vs " + B.Width + "x" + B.Height);
                return 1;
            }
            long differents = 0, somme = 0;
            int max = 0;
            int minx = A.Width, maxx = -1, miny = A.Height, maxy = -1;
            for (int y = 0; y < A.Height; y++)
            {
                for (int x = 0; x < A.Width; x++)
                {
                    Color p = A.GetPixel(x, y), q = B.GetPixel(x, y);
                    int d = Math.Abs(p.R - q.R) + Math.Abs(p.G - q.G) + Math.Abs(p.B - q.B);
                    if (d != 0)
                    {
                        differents++;
                        if (x < minx) minx = x;
                        if (x > maxx) maxx = x;
                        if (y < miny) miny = y;
                        if (y > maxy) maxy = y;
                    }
                    if (d > max) max = d;
                    somme += d;
                }
            }
            Console.WriteLine("pixels differents : " + differents + " / " + ((long)A.Width * A.Height)
                              + "  (" + (100.0 * differents / ((double)A.Width * A.Height)).ToString("0.####") + "%)");
            Console.WriteLine("ecart max (R+V+B) : " + max + "    ecart moyen : "
                              + (somme / ((double)A.Width * A.Height)).ToString("0.####"));
            if (differents > 0)
            {
                Console.WriteLine("zone concernee : x " + minx + ".." + maxx + "   y " + miny + ".." + maxy);
            }
        }
        return 0;
    }
}
