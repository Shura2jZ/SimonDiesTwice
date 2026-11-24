// FlverRendu.exe -- rendu local d'un FLVER, sans le jeu.
//
// Rasteriseur orthographique avec tampon de profondeur. Chaque maillage recoit
// une couleur distincte (les maillages de Simon sont en couleurs vives, ceux
// d'Isshin en gris), avec un ombrage plat base sur la normale geometrique, pour
// que les formes se lisent. Sert a verifier hors jeu : position, orientation,
// occlusion, forme d'une piece.
//
// On ne prend que le PREMIER faceset de chaque maillage (le niveau de detail 0) :
// dans ce modele les facesets suivants reprennent les memes triangles.
//
// Usage :
//   FlverRendu.exe <entree.flver> <sortie.png> <vue> [maillages] [zoom] [largeur] [hauteur]
//
//   vue       : avant | arriere | droite | gauche | dessus | dessous
//   maillages : "tous" ou une liste, ex. "3,4,5,6,7"
//   zoom      : 1 = la vue tient juste la selection, 2 = deux fois plus pres
//
// Lecture seule sur l'entree.
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.Globalization;
using System.Numerics;
using System.Runtime.InteropServices;
using SoulsFormats;

internal static class FlverRendu
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    // couleurs : maillages 3..7 = nos pieces de Simon, le reste en gris
    private static Color Couleur(int i)
    {
        switch (i)
        {
            case 3: return Color.FromArgb(235, 130, 10);   // orange
            case 4: return Color.FromArgb(225, 30, 30);    // rouge
            case 5: return Color.FromArgb(255, 245, 60);   // jaune
            case 6: return Color.FromArgb(40, 205, 70);    // vert
            case 7: return Color.FromArgb(0, 195, 215);    // cyan
            default:
                {
                    int g = 95 + (i * 37) % 120;
                    return Color.FromArgb(g, g, g);
                }
        }
    }

    private static int Main(string[] args)
    {
        if (args.Length < 3)
        {
            Console.WriteLine("usage: FlverRendu.exe <entree.flver> <sortie.png> <vue: avant|arriere|droite|gauche|dessus|dessous> [dessines=tous] [cadre=auto] [zoom=1.15] [largeur=900] [hauteur=1100]");
            Console.WriteLine("  dessines : maillages rasterises (liste separee par des virgules, ou tous)");
            Console.WriteLine("  cadre    : maillages dont la boite definit le cadre (auto = les maillages dessines)");
            return 2;
        }
        string chemin = args[0];
        string sortie = args[1];
        string vue = args[2];
        string liste = args.Length > 3 ? args[3] : "tous";
        string cadreTexte = args.Length > 4 ? args[4] : "auto";
        float zoom = args.Length > 5 ? float.Parse(args[5], Inv) : 1.15f;
        int W = args.Length > 6 ? int.Parse(args[6], Inv) : 900;
        int H = args.Length > 7 ? int.Parse(args[7], Inv) : 1100;
        // cull : 1 = ne dessine que les faces tournees vers la camera, comme le moteur.
        // Convention Sekiro mesuree sur la vanille : la normale geometrique cross(b-a,c-a)
        // pointe vers l'INTERIEUR (dot avec la normale de sommet = -0,98). Une face est donc
        // visible depuis la camera (situee du cote +dir) si dot(n, dir) < 0.
        bool cull = args.Length > 8 && args[8] == "1";

        FLVER2 f = FLVER2.Read(chemin);
        int nm = f.Meshes.Count;
        Console.WriteLine("fichier : " + chemin + "   maillages : " + nm);

        var choisis = new List<int>();
        if (liste == "tous") { for (int i = 0; i < nm; i++) choisis.Add(i); }
        else { foreach (string s in liste.Split(',')) choisis.Add(int.Parse(s.Trim(), Inv)); }

        var cadre = new List<int>();
        if (cadreTexte == "auto") cadre.AddRange(choisis);
        else { foreach (string s in cadreTexte.Split(',')) cadre.Add(int.Parse(s.Trim(), Inv)); }

        Vector3 dir;
        switch (vue)
        {
            case "avant": dir = new Vector3(0f, 0f, -1f); break;
            case "arriere": dir = new Vector3(0f, 0f, 1f); break;
            case "droite": dir = new Vector3(1f, 0f, 0f); break;
            case "gauche": dir = new Vector3(-1f, 0f, 0f); break;
            case "dessus": dir = new Vector3(0f, 1f, 0f); break;
            case "dessous": dir = new Vector3(0f, -1f, 0f); break;
            default: Console.WriteLine("vue inconnue : " + vue); return 2;
        }

        Vector3 up = Math.Abs(dir.Y) > 0.9f ? new Vector3(0f, 0f, -1f) : new Vector3(0f, 1f, 0f);
        Vector3 dr = Vector3.Normalize(Vector3.Cross(up, dir));
        Vector3 ht = Vector3.Normalize(Vector3.Cross(dir, dr));

        // cadre de la projection, calcule sur les sommets des maillages choisis
        float umin = float.MaxValue, umax = float.MinValue, vmin = float.MaxValue, vmax = float.MinValue;
        foreach (int i in cadre)
        {
            foreach (var v in f.Meshes[i].Vertices)
            {
                Vector3 p = v.Position;
                float u = Vector3.Dot(p, dr);
                float w = Vector3.Dot(p, ht);
                if (u < umin) umin = u;
                if (u > umax) umax = u;
                if (w < vmin) vmin = w;
                if (w > vmax) vmax = w;
            }
        }
        float uc = (umin + umax) * 0.5f;
        float vc = (vmin + vmax) * 0.5f;
        float eu = Math.Max(1e-4f, umax - umin);
        float ev = Math.Max(1e-4f, vmax - vmin);
        float k = Math.Min(W / eu, H / ev) / zoom;
        Console.WriteLine(string.Format(Inv, "cadre : {0:0.###} x {1:0.###} m   zoom {2}   {3} x {4} pixels   echelle {5:0.#} px/m",
            eu, ev, zoom, W, H, k));

        var zbuf = new float[W * H];
        var pix = new byte[W * H * 3];
        for (int i = 0; i < W * H; i++)
        {
            zbuf[i] = float.MinValue;
            pix[i * 3 + 0] = 26;
            pix[i * 3 + 1] = 26;
            pix[i * 3 + 2] = 30;
        }
        Vector3 lum = Vector3.Normalize(dr * 0.35f + ht * 0.65f + dir * 0.55f);

        long triangles = 0;
        foreach (int i in choisis)
        {
            var m = f.Meshes[i];
            if (m.FaceSets.Count == 0) continue;
            var idx = m.FaceSets[0].Indices;
            Color c = Couleur(i);
            int parMaillage = 0;
            for (int t = 0; t + 2 < idx.Count; t += 3)
            {
                Vector3 a = m.Vertices[idx[t]].Position;
                Vector3 b = m.Vertices[idx[t + 1]].Position;
                Vector3 d = m.Vertices[idx[t + 2]].Position;

                float au = Vector3.Dot(a, dr), av = Vector3.Dot(a, ht), ad = Vector3.Dot(a, dir);
                float bu = Vector3.Dot(b, dr), bv = Vector3.Dot(b, ht), bd = Vector3.Dot(b, dir);
                float du = Vector3.Dot(d, dr), dv = Vector3.Dot(d, ht), dd = Vector3.Dot(d, dir);

                float ax = W * 0.5f + (au - uc) * k, ay = H * 0.5f - (av - vc) * k;
                float bx = W * 0.5f + (bu - uc) * k, by = H * 0.5f - (bv - vc) * k;
                float dx = W * 0.5f + (du - uc) * k, dy = H * 0.5f - (dv - vc) * k;

                float det = (by - dy) * (ax - dx) + (dx - bx) * (ay - dy);
                if (Math.Abs(det) < 1e-6f) continue;

                Vector3 n = Vector3.Cross(b - a, d - a);
                float ln = n.Length();
                if (ln < 1e-12f) continue;
                n = n / ln;
                if (cull && Vector3.Dot(n, dir) >= 0f) continue;   // face arriere
                float br = 0.32f + 0.68f * Math.Abs(Vector3.Dot(n, lum));
                int rr = (int)(c.R * br), gg = (int)(c.G * br), bb = (int)(c.B * br);
                if (rr > 255) rr = 255; if (gg > 255) gg = 255; if (bb > 255) bb = 255;

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
                        zbuf[o] = prof;
                        int s = o * 3;
                        pix[s + 0] = (byte)bb;
                        pix[s + 1] = (byte)gg;
                        pix[s + 2] = (byte)rr;
                        parMaillage++;
                    }
                }
                triangles++;
            }
            Console.WriteLine(string.Format(Inv, "  maillage {0,2} : couleur ({1,3},{2,3},{3,3})  {4,7} triangles dessines  mat {5} {6}  noeud {7}",
                i, c.R, c.G, c.B, parMaillage,
                m.MaterialIndex,
                m.MaterialIndex < f.Materials.Count ? f.Materials[m.MaterialIndex].Name : "?",
                (m.NodeIndex >= 0 && m.NodeIndex < f.Nodes.Count) ? f.Nodes[m.NodeIndex].Name : "?"));
        }
        Console.WriteLine("triangles parcourus : " + triangles);

        var bmp = new Bitmap(W, H, PixelFormat.Format24bppRgb);
        BitmapData donnees = bmp.LockBits(new Rectangle(0, 0, W, H), ImageLockMode.WriteOnly, PixelFormat.Format24bppRgb);
        byte[] dest = new byte[donnees.Stride * H];
        for (int y = 0; y < H; y++)
        {
            for (int x = 0; x < W; x++)
            {
                int s = (y * W + x) * 3;
                dest[y * donnees.Stride + x * 3 + 0] = pix[s + 0];
                dest[y * donnees.Stride + x * 3 + 1] = pix[s + 1];
                dest[y * donnees.Stride + x * 3 + 2] = pix[s + 2];
            }
        }
        Marshal.Copy(dest, 0, donnees.Scan0, dest.Length);
        bmp.UnlockBits(donnees);
        bmp.Save(sortie, ImageFormat.Png);
        bmp.Dispose();
        Console.WriteLine("ecrit : " + sortie + "   (" + W + " x " + H + ")");
        return 0;
    }
}
