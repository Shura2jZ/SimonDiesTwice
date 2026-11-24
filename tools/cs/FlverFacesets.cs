// FlverFacesets.exe <fichier.flver>
//
// But : comprendre d'ou viennent les DEUX comptes de faces de l'en-tete FLVER
// (0x40 = "faces hors maillages de motion blur et faces degenerees",
//  0x44 = "total des faces").
//
// On liste chaque faceset avec ses drapeaux et son nombre de faces, puis on
// compare plusieurs sommes possibles aux deux valeurs de l'en-tete.
//
// Drapeaux connus (source SoulsFormats) :
//   0x01000000 LodLevel1
//   0x02000000 LodLevel2
//   0x40000000 EdgeCompressed
//   0x80000000 MotionBlur
//
// Usage : FlverFacesets.exe <fichier.flver>

using System;
using System.IO;
using SoulsFormats;

internal static class FlverFacesets
{
    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.WriteLine("usage: FlverFacesets.exe <fichier.flver>"); return 2; }

        FLVER2 f = FLVER2.Read(args[0]);
        byte[] raw = File.ReadAllBytes(args[0]);
        int h40 = BitConverter.ToInt32(raw, 0x40);
        int h44 = BitConverter.ToInt32(raw, 0x44);
        int h50 = BitConverter.ToInt32(raw, 0x50);

        Console.WriteLine("fichier : " + args[0]);
        Console.WriteLine("en-tete 0x40 (faces hors motion blur) = " + h40.ToString("N0"));
        Console.WriteLine("en-tete 0x44 (total faces)            = " + h44.ToString("N0"));
        Console.WriteLine("en-tete 0x50 (facesets)               = " + h50.ToString("N0"));
        Console.WriteLine();

        long total = 0;
        long sansMB = 0;
        long avecMB = 0;
        long lod0 = 0;
        long lod1 = 0;
        long lod2 = 0;
        long sansMB_lod0 = 0;
        int nStrips = 0;

        for (int i = 0; i < f.Meshes.Count; i++)
        {
            FLVER2.Mesh m = f.Meshes[i];
            Console.WriteLine("maillage " + i.ToString().PadLeft(2) + " : sommets " + m.Vertices.Count.ToString("N0")
                              + "  facesets " + m.FaceSets.Count);
            for (int j = 0; j < m.FaceSets.Count; j++)
            {
                FLVER2.FaceSet fs = m.FaceSets[j];
                uint fl = (uint)fs.Flags;
                int faces = fs.Indices.Count / 3;
                bool mb = (fl & 0x80000000u) != 0;
                bool l1 = (fl & 0x01000000u) != 0;
                bool l2 = (fl & 0x02000000u) != 0;
                bool eg = (fl & 0x40000000u) != 0;

                total += faces;
                if (mb) avecMB += faces; else sansMB += faces;
                if (l1) lod1 += faces;
                else if (l2) lod2 += faces;
                else lod0 += faces;
                if (!mb && !l1 && !l2) sansMB_lod0 += faces;
                if (fs.TriangleStrip) nStrips++;

                Console.WriteLine("   faceset " + j + " : drapeaux 0x" + fl.ToString("X8")
                                  + "  indices " + fs.Indices.Count.ToString("N0")
                                  + "  faces " + faces.ToString("N0")
                                  + (mb ? "  [MotionBlur]" : "")
                                  + (l1 ? "  [LOD1]" : "") + (l2 ? "  [LOD2]" : "")
                                  + (eg ? "  [EdgeComp]" : "")
                                  + (fs.TriangleStrip ? "  [strip]" : ""));
            }
        }

        Console.WriteLine();
        Console.WriteLine("=== sommes ===");
        Console.WriteLine("total faces (toutes)        = " + total.ToString("N0"));
        Console.WriteLine("faces hors MotionBlur       = " + sansMB.ToString("N0"));
        Console.WriteLine("faces MotionBlur            = " + avecMB.ToString("N0"));
        Console.WriteLine("faces LOD0 / LOD1 / LOD2    = " + lod0.ToString("N0") + " / " + lod1.ToString("N0")
                          + " / " + lod2.ToString("N0"));
        Console.WriteLine("faces LOD0 hors MotionBlur  = " + sansMB_lod0.ToString("N0"));
        Console.WriteLine("facesets en bande (strip)   = " + nStrips);
        Console.WriteLine();
        Console.WriteLine("=== confrontation a l'en-tete ===");
        Console.WriteLine("0x44 == total des faces ?                       " + (h44 == total));
        Console.WriteLine("0x40 == faces hors MotionBlur ?                 " + (h40 == sansMB));
        Console.WriteLine("0x40 == faces LOD0 hors MotionBlur ?            " + (h40 == sansMB_lod0));
        Console.WriteLine("0x40 == faces LOD0 (toutes) ?                   " + (h40 == lod0));
        Console.WriteLine("0x40 == faces LOD1 ?                            " + (h40 == lod1));
        return 0;
    }
}
