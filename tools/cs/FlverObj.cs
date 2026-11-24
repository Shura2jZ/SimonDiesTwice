// FlverObj.exe -- exporte des maillages FLVER en OBJ (positions, UV0, triangles).
//
// Sert a visualiser un maillage avec sa texture dans Blender : on peut alors
// verifier la convention d'UV (un V a l'envers se voit immediatement) et
// previsualiser le resultat final.
//
// Chaque maillage devient un groupe 'maillageN' avec son materiau 'matN', donc
// on peut n'afficher qu'une piece.
//
// Usage :
//   FlverObj.exe <entree.flver> <sortie.obj> <maillages|tous> [--vflip]
//
// --vflip : ecrit v' = 1 - v. OBJ et Blender comptent le V depuis le bas, alors
//           que les textures DirectX/FromSoft le comptent depuis le haut : c'est
//           cette conversion qui reproduit ce que fait le moteur.
//
// Lecture seule sur l'entree.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using SoulsFormats;

internal static class FlverObj
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static int Main(string[] args)
    {
        if (args.Length < 3)
        {
            Console.WriteLine("usage: FlverObj.exe <entree.flver> <sortie.obj> <maillages|tous> [--vflip]");
            return 2;
        }
        bool vflip = false;
        for (int i = 3; i < args.Length; i++) if (args[i] == "--vflip") vflip = true;

        bool tous = args[2] == "tous";
        var voulus = new HashSet<int>();
        if (!tous) foreach (string s in args[2].Split(',')) voulus.Add(int.Parse(s.Trim(), Inv));

        FLVER2 f = FLVER2.Read(args[0]);
        var sb = new StringBuilder();
        sb.AppendLine("# export FlverObj : " + Path.GetFileName(args[0]));
        if (vflip) sb.AppendLine("# V inverse (1 - v)");

        long baseSommet = 1;   // OBJ : les indices commencent a 1
        long baseUv = 1;
        int maillages = 0, triangles = 0;

        for (int mi = 0; mi < f.Meshes.Count; mi++)
        {
            if (!tous && !voulus.Contains(mi)) continue;
            FLVER2.Mesh m = f.Meshes[mi];
            if (m.Vertices.Count == 0) continue;
            maillages++;

            sb.AppendLine("o maillage" + mi);
            sb.AppendLine("usemtl mat" + mi);
            foreach (FLVER.Vertex v in m.Vertices)
            {
                sb.AppendLine(string.Format(Inv, "v {0:0.######} {1:0.######} {2:0.######}",
                    v.Position.X, v.Position.Y, v.Position.Z));
            }
            foreach (FLVER.Vertex v in m.Vertices)
            {
                float u = 0f, vv = 0f;
                if (v.UVs != null && v.UVs.Count > 0)
                {
                    u = v.UVs[0].X;
                    vv = v.UVs[0].Y;
                }
                if (vflip) vv = 1f - vv;
                sb.AppendLine(string.Format(Inv, "vt {0:0.######} {1:0.######}", u, vv));
            }

            foreach (FLVER2.FaceSet fs in m.FaceSets)
            {
                List<int> idx = fs.Indices;
                for (int t = 0; t + 2 < idx.Count; t += 3)
                {
                    int a = idx[t], b = idx[t + 1], c = idx[t + 2];
                    sb.AppendLine(string.Format(Inv, "f {0}/{0} {1}/{1} {2}/{2}",
                        baseSommet + a, baseSommet + b, baseSommet + c));
                    triangles++;
                }
            }
            baseSommet += m.Vertices.Count;
            baseUv += m.Vertices.Count;
        }

        File.WriteAllText(args[1], sb.ToString(), new UTF8Encoding(false));
        Console.WriteLine("maillages : " + maillages + "   triangles : " + triangles);
        Console.WriteLine("ecrit : " + args[1]);
        return 0;
    }

    private struct Vector3D
    {
        public float X, Y;
        public Vector3D(float x, float y) { X = x; Y = y; }
    }
}
