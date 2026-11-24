// FlverRenduTex.exe -- rendu local TEXTURE d'un FLVER, sans le jeu.
// Comme FlverRendu mais echantillonne la texture du materiau (DDS BC1) via les UV.
//
// Usage :
//   FlverRenduTex.exe <flver> <sortie.png> <vue> <carteTextures> [maillages] [zoom] [W] [H]
//
//   vue            : avant|arriere|droite|gauche|dessus|dessous
//   carteTextures  : fichier .txt, une ligne par maillage : "<indexMaillage> <chemin.dds>"
//   maillages      : "tous" ou liste (defaut tous)
//   zoom           : 1.15
//
// Les DDS BC1 (DXT1) sont lus directement. Les UV sont interpretees comme dans
// le moteur : V stocke en Short4 normalise (0..1), origine en bas a gauche.
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;
using System.Numerics;
using System.Runtime.InteropServices;
using SoulsFormats;

internal static class FlverRenduTex
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    // ---------- lecture DDS BC1 (DXT1) ----------
    private sealed class Texture
    {
        public int W, H;
        public byte[] Bc1;   // 8 octets par bloc 4x4
        public int BlockW, BlockH;
        public int DataOffset;

        public static Texture Load(string path)
        {
            byte[] d = File.ReadAllBytes(path);
            if (d.Length < 128 || d[0] != 'D' || d[1] != 'D' || d[2] != 'S' || d[3] != ' ')
                throw new Exception("pas un DDS : " + path);
            int h = BitConverter.ToInt32(d, 12);
            int w = BitConverter.ToInt32(d, 16);
            int flags = BitConverter.ToInt32(d, 80);
            int fourcc = BitConverter.ToInt32(d, 84);
            int pixelFlags = BitConverter.ToInt32(d, 80);
            bool dxt1 = (fourcc == 0x31545844); // 'DXT1'
            bool dx10 = (fourcc == 0x30315844); // 'DX10'
            int dataOffset = 128;
            if (dx10)
            {
                dataOffset = 128 + 20;
                int dxgi = BitConverter.ToInt32(d, 128);
                // 71 = BC1_UNORM, 72 = BC1_UNORM_SRGB
                if (dxgi != 71 && dxgi != 72)
                    throw new Exception("format DX10 non BC1 : " + dxgi);
            }
            else if (!dxt1)
            {
                throw new Exception("DDS non BC1 (fourcc=0x" + fourcc.ToString("X") + ") : " + path);
            }
            var t = new Texture { W = w, H = h, DataOffset = dataOffset };
            t.BlockW = (w + 3) / 4;
            t.BlockH = (h + 3) / 4;
            int taille = t.BlockW * t.BlockH * 8;
            if (d.Length - dataOffset < taille) taille = Math.Max(0, d.Length - dataOffset);
            t.Bc1 = new byte[taille];
            Array.Copy(d, dataOffset, t.Bc1, 0, taille);
            return t;
        }

        // BC1 avec adressage wrap et alpha-test (index 3 transparent si c0 <= c1).
        // V du FLVER a son origine en bas; la texture DDS a son origine en haut.
        public void Sample(float u, float v, out int r, out int g, out int b, out int a)
        {
            r = g = b = 255; a = 255;
            if (W <= 0 || H <= 0) return;
            u -= (float)Math.Floor(u); v -= (float)Math.Floor(v);
            int x = ((int)Math.Floor(u * W)) % W;
            int y = ((int)Math.Floor((1f - v) * H)) % H;
            if (x < 0) x += W; if (y < 0) y += H;
            int bx = x / 4, by = y / 4;
            int off = (by * BlockW + bx) * 8;
            if (off + 7 >= Bc1.Length) return;
            int c0 = Bc1[off] | (Bc1[off + 1] << 8);
            int c1 = Bc1[off + 2] | (Bc1[off + 3] << 8);
            int row = Bc1[off + 4 + (y & 3)];
            int index = (row >> (2 * (x & 3))) & 3;
            int[] p0 = {
                (int)Math.Round(((c0 >> 11) & 0x1F) * 255.0 / 31.0),
                (int)Math.Round(((c0 >> 5) & 0x3F) * 255.0 / 63.0),
                (int)Math.Round((c0 & 0x1F) * 255.0 / 31.0)
            };
            int[] p1 = {
                (int)Math.Round(((c1 >> 11) & 0x1F) * 255.0 / 31.0),
                (int)Math.Round(((c1 >> 5) & 0x3F) * 255.0 / 63.0),
                (int)Math.Round((c1 & 0x1F) * 255.0 / 31.0)
            };
            int[] color = new int[3];
            if (c0 > c1)
            {
                if (index == 0) Array.Copy(p0, color, 3);
                else if (index == 1) Array.Copy(p1, color, 3);
                else if (index == 2)
                    for (int k = 0; k < 3; k++) color[k] = (2 * p0[k] + p1[k]) / 3;
                else
                    for (int k = 0; k < 3; k++) color[k] = (p0[k] + 2 * p1[k]) / 3;
            }
            else
            {
                if (index == 3) { a = 0; r = g = b = 0; return; }
                if (index == 0) Array.Copy(p0, color, 3);
                else if (index == 1) Array.Copy(p1, color, 3);
                else
                    for (int k = 0; k < 3; k++) color[k] = (p0[k] + p1[k]) / 2;
            }
            r = color[0]; g = color[1]; b = color[2];
        }
    }

    private static bool SkinMaillage(int index, string[] args)
    {
        foreach (string arg in args)
        {
            if (arg == "--skin") return true;
            if (arg.StartsWith("--skin="))
                foreach (string s in arg.Substring(7).Split(','))
                {
                    int n;
                    if (int.TryParse(s, out n) && n == index) return true;
                }
        }
        return false;
    }

    private static Vector3 PoserSommet(FLVER2 f, FLVER2.Mesh mesh, FLVER.Vertex v)
    {
        Vector3 result = Vector3.Zero;
        float total = 0f;
        for (int k = 0; k < 4; k++)
        {
            float w = v.BoneWeights[k];
            if (w <= 0f) continue;
            int bi = v.BoneIndices[k];
            if (bi < 0 || bi >= f.Nodes.Count) continue;
            Matrix4x4 bone = Monde(f, bi);
            result += Vector3.Transform(v.Position, bone) * w;
            total += w;
        }
        return total > 0f ? result / total : v.Position;
    }

    private static Matrix4x4 Monde(FLVER2 f, int i)
    {
        Matrix4x4 m = f.Nodes[i].ComputeLocalTransform();
        int p = f.Nodes[i].ParentIndex;
        while (p >= 0 && p < f.Nodes.Count && p != i)
        {
            m = Matrix4x4.Multiply(m, f.Nodes[p].ComputeLocalTransform());
            i = p;
            p = f.Nodes[i].ParentIndex;
        }
        return m;
    }

    private static int Main(string[] args)
    {
        if (args.Length < 4)
        {
            Console.WriteLine("usage: FlverRenduTex.exe <flver> <sortie.png> <vue> <carte.txt> [maillages=tous] [zoom=1.15] [W=900] [H=1100] [cadre=maillages]");
            return 2;
        }
        string chemin = args[0], sortie = args[1], vue = args[2], carte = args[3];
        string liste = args.Length > 4 ? args[4] : "tous";
        float zoom = args.Length > 5 ? float.Parse(args[5], Inv) : 1.15f;
        int W = args.Length > 6 ? int.Parse(args[6], Inv) : 900;
        int H = args.Length > 7 ? int.Parse(args[7], Inv) : 1100;

        // carte : indexMaillage -> chemin DDS
        var textures = new Dictionary<int, Texture>();
        foreach (string ligne in File.ReadAllLines(carte))
        {
            string l = ligne.Trim();
            if (l.Length == 0 || l.StartsWith("#")) continue;
            string[] p = l.Split(new[] { '|', '\t' }, StringSplitOptions.RemoveEmptyEntries);
            if (p.Length < 2) continue;
            int idx = int.Parse(p[0], Inv);
            if (!File.Exists(p[1])) { Console.WriteLine("  texture absente : " + p[1]); continue; }
            try { textures[idx] = Texture.Load(p[1]); }
            catch (Exception e) { Console.WriteLine("  texture illisible : " + p[1] + " (" + e.Message + ")"); }
        }
        Console.WriteLine("textures chargees : " + textures.Count);

        FLVER2 f = FLVER2.Read(chemin);
        int nm = f.Meshes.Count;
        var choisis = new List<int>();
        if (liste == "tous") { for (int i = 0; i < nm; i++) choisis.Add(i); }
        else foreach (string s in liste.Split(',')) choisis.Add(int.Parse(s.Trim(), Inv));

        Vector3 dir;
        switch (vue)
        {
            case "avant": dir = new Vector3(0f, 0f, -1f); break;
            case "arriere": dir = new Vector3(0f, 0f, 1f); break;
            case "droite": dir = new Vector3(1f, 0f, 0f); break;
            case "gauche": dir = new Vector3(-1f, 0f, 0f); break;
            case "dessus": dir = new Vector3(0f, 1f, 0f); break;
            case "dessous": dir = new Vector3(0f, -1f, 0f); break;
            case "angle30": dir = Vector3.Normalize(new Vector3(0.5f, 0f, -0.8660254f)); break;
            case "angle45": dir = Vector3.Normalize(new Vector3(0.7071068f, 0f, -0.7071068f)); break;
            case "angle60": dir = Vector3.Normalize(new Vector3(0.8660254f, 0f, -0.5f)); break;
            default: Console.WriteLine("vue inconnue"); return 2;
        }
        Vector3 up = Math.Abs(dir.Y) > 0.9f ? new Vector3(0f, 0f, -1f) : new Vector3(0f, 1f, 0f);
        Vector3 dr = Vector3.Normalize(Vector3.Cross(up, dir));
        Vector3 ht = Vector3.Normalize(Vector3.Cross(dir, dr));

        var cadrage = new List<int>(choisis);
        if (args.Length > 8 && args[8] != "-")
        {
            cadrage.Clear();
            foreach (string s in args[8].Split(',')) cadrage.Add(int.Parse(s.Trim(), Inv));
        }
        float umin = float.MaxValue, umax = float.MinValue, vmin = float.MaxValue, vmax = float.MinValue;
        Vector3 frameMin = new Vector3(float.NegativeInfinity);
        Vector3 frameMax = new Vector3(float.PositiveInfinity);
        foreach (string arg in args)
        {
            if (!arg.StartsWith("--frame-box=")) continue;
            string[] q = arg.Substring(12).Split(',');
            if (q.Length != 6) throw new Exception("--frame-box=xmin,ymin,zmin,xmax,ymax,zmax attendu");
            frameMin = new Vector3(float.Parse(q[0], Inv), float.Parse(q[1], Inv), float.Parse(q[2], Inv));
            frameMax = new Vector3(float.Parse(q[3], Inv), float.Parse(q[4], Inv), float.Parse(q[5], Inv));
        }
        foreach (int i in cadrage)
            foreach (var v in f.Meshes[i].Vertices)
            {
                Vector3 p = v.Position;
                if (SkinMaillage(i, args)) p = PoserSommet(f, f.Meshes[i], v);
                if (p.X < frameMin.X || p.Y < frameMin.Y || p.Z < frameMin.Z ||
                    p.X > frameMax.X || p.Y > frameMax.Y || p.Z > frameMax.Z) continue;
                float u = Vector3.Dot(p, dr), w = Vector3.Dot(p, ht);
                if (u < umin) umin = u; if (u > umax) umax = u;
                if (w < vmin) vmin = w; if (w > vmax) vmax = w;
            }
        float uc = (umin + umax) * 0.5f, vc = (vmin + vmax) * 0.5f;
        float k = Math.Min(W / Math.Max(1e-4f, umax - umin), H / Math.Max(1e-4f, vmax - vmin)) / zoom;

        var zbuf = new float[W * H];
        var pix = new byte[W * H * 3];
        for (int i = 0; i < W * H; i++)
        {
            zbuf[i] = float.MinValue;
            pix[i * 3] = 24; pix[i * 3 + 1] = 24; pix[i * 3 + 2] = 28;
        }
        Vector3 lum = Vector3.Normalize(dr * 0.35f + ht * 0.65f + dir * 0.55f);

        foreach (int i in choisis)
        {
            var m = f.Meshes[i];
            if (m.FaceSets.Count == 0) continue;
            var idx = m.FaceSets[0].Indices;
            Texture tex = textures.ContainsKey(i) ? textures[i] : null;
            for (int t = 0; t + 2 < idx.Count; t += 3)
            {
                int ia = idx[t], ib = idx[t + 1], ic = idx[t + 2];
                var va = m.Vertices[ia]; var vb = m.Vertices[ib]; var vc2 = m.Vertices[ic];
                Vector3 a = va.Position, b = vb.Position, d = vc2.Position;
                if (SkinMaillage(i, args))
                {
                    a = PoserSommet(f, m, va);
                    b = PoserSommet(f, m, vb);
                    d = PoserSommet(f, m, vc2);
                }

                float au = Vector3.Dot(a, dr), av = Vector3.Dot(a, ht), ad = Vector3.Dot(a, dir);
                float bu = Vector3.Dot(b, dr), bv = Vector3.Dot(b, ht), bd = Vector3.Dot(b, dir);
                float du = Vector3.Dot(d, dr), dv = Vector3.Dot(d, ht), dd = Vector3.Dot(d, dir);

                float ax = W * 0.5f + (au - uc) * k, ay = H * 0.5f - (av - vc) * k;
                float bx = W * 0.5f + (bu - uc) * k, by = H * 0.5f - (bv - vc) * k;
                float dx = W * 0.5f + (du - uc) * k, dy = H * 0.5f - (dv - vc) * k;

                float det = (by - dy) * (ax - dx) + (dx - bx) * (ay - dy);
                if (Math.Abs(det) < 1e-6f) continue;
                Vector3 n = Vector3.Cross(b - a, d - a);
                float ln = n.Length(); if (ln < 1e-12f) continue;
                n = n / ln;
                if (i != 5 && i != 10 && i != 27 && Vector3.Dot(n, dir) >= 0f) continue; // cheveux et armes double-face
                float br = 0.42f + 0.58f * Math.Abs(Vector3.Dot(n, lum));

                float auv = va.UVs.Count > 0 ? va.UVs[0].X : 0f, avv = va.UVs.Count > 0 ? va.UVs[0].Y : 0f;
                float buv = vb.UVs.Count > 0 ? vb.UVs[0].X : 0f, bvv = vb.UVs.Count > 0 ? vb.UVs[0].Y : 0f;
                float duv = vc2.UVs.Count > 0 ? vc2.UVs[0].X : 0f, dvv = vc2.UVs.Count > 0 ? vc2.UVs[0].Y : 0f;

                int x0 = (int)Math.Floor(Math.Min(ax, Math.Min(bx, dx)));
                int x1 = (int)Math.Ceiling(Math.Max(ax, Math.Max(bx, dx)));
                int y0 = (int)Math.Floor(Math.Min(ay, Math.Min(by, dy)));
                int y1 = (int)Math.Ceiling(Math.Max(ay, Math.Max(by, dy)));
                if (x0 < 0) x0 = 0; if (y0 < 0) y0 = 0;
                if (x1 > W - 1) x1 = W - 1; if (y1 > H - 1) y1 = H - 1;

                for (int y = y0; y <= y1; y++)
                {
                    for (int x = x0; x <= x1; x++)
                    {
                        float px = x + 0.5f, py = y + 0.5f;
                        float w0 = ((by - dy) * (px - dx) + (dx - bx) * (py - dy)) / det;
                        if (w0 < 0f) continue;
                        float w1 = ((dy - ay) * (px - dx) + (ax - dx) * (py - dy)) / det;
                        if (w1 < 0f) continue;
                        float w2 = 1f - w0 - w1;
                        if (w2 < 0f) continue;
                        float prof = w0 * ad + w1 * bd + w2 * dd;
                        int o = y * W + x;
                        if (prof <= zbuf[o]) continue;
                        int rr = 200, gg = 200, bb2 = 200;
                        if (tex != null)
                        {
                            float tu = w0 * auv + w1 * buv + w2 * duv;
                            float tv = w0 * avv + w1 * bvv + w2 * dvv;
                            int aa;
                            tex.Sample(tu, tv, out rr, out gg, out bb2, out aa);
                            if (aa < 128) continue; // le transparent ne masque pas les cartes derriere
                        }
                        zbuf[o] = prof; // profondeur seulement apres le test alpha
                        int s = o * 3;
                        pix[s + 0] = (byte)Math.Min(255, bb2 * br);
                        pix[s + 1] = (byte)Math.Min(255, gg * br);
                        pix[s + 2] = (byte)Math.Min(255, rr * br);
                    }
                }
            }
            Console.WriteLine("  maillage " + i + " : mat " + m.MaterialIndex + " " + (m.MaterialIndex < f.Materials.Count ? f.Materials[m.MaterialIndex].Name : "?") + (tex != null ? "  (texture " + tex.W + "x" + tex.H + ")" : "  (PAS DE TEXTURE)"));
        }

        var bmp = new Bitmap(W, H, PixelFormat.Format24bppRgb);
        BitmapData data = bmp.LockBits(new Rectangle(0, 0, W, H), ImageLockMode.WriteOnly, PixelFormat.Format24bppRgb);
        byte[] dest = new byte[data.Stride * H];
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++)
            {
                int s = (y * W + x) * 3;
                dest[y * data.Stride + x * 3] = pix[s];
                dest[y * data.Stride + x * 3 + 1] = pix[s + 1];
                dest[y * data.Stride + x * 3 + 2] = pix[s + 2];
            }
        Marshal.Copy(dest, 0, data.Scan0, dest.Length);
        bmp.UnlockBits(data);
        bmp.Save(sortie, ImageFormat.Png);
        bmp.Dispose();
        Console.WriteLine("ecrit : " + sortie + " (" + W + "x" + H + ")");
        return 0;
    }
}
