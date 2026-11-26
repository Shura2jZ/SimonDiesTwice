// FlverHairInject.exe -- injecte un mesh de cheveux (extrait d'un jeu UE5)
// dans un emplacement du FLVER Sekiro.
//
// Le mesh de cheveux UE est en centimetres, Y vers le haut, personnage regardant
// +Z. Sekiro : metres, personnage regardant -Z. On applique donc une rotation
// de 180 degres autour de Y, une mise a l'echelle de 1/100, puis une
// translation de calibrage (dx, dy, dz).
//
// L'emplacement choisi (slot 5 du vanilla : materiau 5 = c5400_hair, shader
// Fur_NTC) recoit la geometrie. Le noeud porteur est mis sur l'os de la tete
// (199 = c5400_head_20180419_8) pour que les cheveux suivent la tete.
//
// Usage :
//   FlverHairInject.exe <flver> <sortie> <cheveux.bin> <slot> <dx> <dy> <dz> [noeud]
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Numerics;
using SoulsFormats;

internal static class FlverHairInject
{
    private static int Main(string[] args)
    {
        if (args.Length < 7)
        {
            Console.WriteLine("usage: FlverHairInject.exe <flver> <sortie> <bin> <slot> <dx> <dy> <dz> [noeud]");
            return 2;
        }
        string src = args[0], dst = args[1], bin = args[2];
        int slot = int.Parse(args[3], CultureInfo.InvariantCulture);
        float dx = float.Parse(args[4], CultureInfo.InvariantCulture);
        float dy = float.Parse(args[5], CultureInfo.InvariantCulture);
        float dz = float.Parse(args[6], CultureInfo.InvariantCulture);
        int node = args.Length > 7 ? int.Parse(args[7], CultureInfo.InvariantCulture) : 199;
        // materiau : -1 = garder celui de l'emplacement, sinon forcer
        // (les cheveux de Simon utilisent le materiau du casque d'Isshin, dont
        // on remplace la texture par l'atlas de mèches de Simon).
        int materiau = args.Length > 8 ? int.Parse(args[8], CultureInfo.InvariantCulture) : -1;
        // echelle : factor applique autour de l'origine du mesh de cheveux
        float echelle = args.Length > 9 ? float.Parse(args[9], CultureInfo.InvariantCulture) : 1.0f;
        // normales : 0 = normales UE, 1 = normales mixtes (verticales + radiales).
        // Les cartes de cheveux de Simon ont des normales tangentielles : eclairees
        // ainsi, elles ressortent NOIRES. On les remplace par des normales qui
        // pointent vers le haut/le dehors de la tete.
        int modeNormales = args.Length > 10 ? int.Parse(args[10], CultureInfo.InvariantCulture) : 0;

        // --- lecture du binaire de cheveux --------------------------------
        byte[] data = File.ReadAllBytes(bin);
        if (data.Length < 16 || System.Text.Encoding.ASCII.GetString(data, 0, 6) != "HAIRB1")
        {
            Console.WriteLine("format invalide : " + bin);
            return 3;
        }
        int n = BitConverter.ToInt32(data, 8);
        int ni = BitConverter.ToInt32(data, 12);
        Console.WriteLine("cheveux : " + n + " sommets, " + (ni / 3) + " triangles");

        int off = 16;
        var P = new Vector3[n];
        var N = new Vector3[n];
        var uv0 = new Vector2[n];
        var uv1 = new Vector2[n];
        var uv2 = new Vector2[n];
        for (int i = 0; i < n; i++)
        {
            P[i] = new Vector3(BitConverter.ToSingle(data, off), BitConverter.ToSingle(data, off + 4), BitConverter.ToSingle(data, off + 8));
            off += 12;
        }
        for (int i = 0; i < n; i++)
        {
            N[i] = new Vector3(BitConverter.ToSingle(data, off), BitConverter.ToSingle(data, off + 4), BitConverter.ToSingle(data, off + 8));
            off += 12;
        }
        for (int i = 0; i < n; i++)
        {
            uv0[i] = new Vector2(BitConverter.ToSingle(data, off), BitConverter.ToSingle(data, off + 4));
            off += 8;
        }
        for (int i = 0; i < n; i++)
        {
            uv1[i] = new Vector2(BitConverter.ToSingle(data, off), BitConverter.ToSingle(data, off + 4));
            off += 8;
        }
        for (int i = 0; i < n; i++)
        {
            uv2[i] = new Vector2(BitConverter.ToSingle(data, off), BitConverter.ToSingle(data, off + 4));
            off += 8;
        }
        var idx = new int[ni];
        for (int i = 0; i < ni; i++)
        {
            idx[i] = (int)BitConverter.ToUInt32(data, off);
            off += 4;
        }

        // --- conversion UE -> Sekiro --------------------------------------
        Vector3 lo = new Vector3(float.MaxValue), hi = new Vector3(float.MinValue);
        var verts = new List<FLVER.Vertex>(n);
        // centre de la calotte (pour les normales radiales) : point le plus haut
        Vector3 sommetHaut = new Vector3(0, float.MinValue, 0);
        for (int i = 0; i < n; i++)
        {
            Vector3 pBrut = new Vector3(-P[i].X / 100f * echelle, P[i].Y / 100f * echelle, -P[i].Z / 100f * echelle);
            if (pBrut.Y > sommetHaut.Y) sommetHaut = pBrut;
        }
        for (int i = 0; i < n; i++)
        {
            // UE cm -> m, rotation 180 Y (personnage vers +Z -> vers -Z)
            Vector3 p = new Vector3(-P[i].X / 100f * echelle, P[i].Y / 100f * echelle, -P[i].Z / 100f * echelle) + new Vector3(dx, dy, dz);
            Vector3 nn = new Vector3(-N[i].X, N[i].Y, -N[i].Z);
            if (nn.LengthSquared() > 1e-12f) nn = Vector3.Normalize(nn);
            if (modeNormales == 1)
            {
                // normale mixte : majoritairement vers le haut, legerement radiale
                Vector3 radial = p - new Vector3(p.X, sommetHaut.Y, p.Z);
                if (radial.LengthSquared() > 1e-12f) radial = Vector3.Normalize(radial);
                nn = Vector3.Normalize(new Vector3(radial.X * 0.45f, 1.0f, radial.Z * 0.45f));
            }
            lo = Vector3.Min(lo, p);
            hi = Vector3.Max(hi, p);

            var v = new FLVER.Vertex(0, 0, 0);
            v.Position = p;
            v.Normal = nn;
            v.NormalW = 0;
            v.Tangents = new List<Vector4> { new Vector4(1, 0, 0, 1) };
            v.BoneIndices = new FLVER.VertexBoneIndices();
            v.BoneIndices[0] = 0; v.BoneIndices[1] = 0; v.BoneIndices[2] = 0; v.BoneIndices[3] = 0;
            v.BoneWeights = new FLVER.VertexBoneWeights();
            v.BoneWeights[0] = 100; v.BoneWeights[1] = 0; v.BoneWeights[2] = 0; v.BoneWeights[3] = 0;
            v.UVs = new List<Vector3>
            {
                new Vector3(uv0[i].X, uv0[i].Y, 0),
                new Vector3(uv1[i].X, uv1[i].Y, 0),
                new Vector3(uv2[i].X, uv2[i].Y, 0)
            };
            v.Colors = new List<FLVER.VertexColor> { new FLVER.VertexColor(255, 255, 255, 255) };
            verts.Add(v);
        }
        Console.WriteLine("bbox Sekiro : " + lo + " .. " + hi);

        // --- injection ----------------------------------------------------
        FLVER2 f = FLVER2.Read(src);
        if (slot < 0 || slot >= f.Meshes.Count)
        {
            Console.WriteLine("emplacement hors limites : " + slot);
            return 4;
        }
        var gabarit = f.Meshes[slot];
        int layout = gabarit.VertexBuffers.Count > 0 ? gabarit.VertexBuffers[0].LayoutIndex : 6;
        Console.WriteLine("emplacement " + slot + " : materiau " + gabarit.MaterialIndex + ", noeud " + gabarit.NodeIndex + ", disposition " + layout
                          + (materiau >= 0 ? "  -> materiau force a " + materiau : ""));

        var mesh = new FLVER2.Mesh
        {
            MaterialIndex = materiau >= 0 ? materiau : gabarit.MaterialIndex,
            NodeIndex = node,
            Dynamic = 1,
            UseBoneWeights = true,
            BoneIndices = new List<int> { 147 },
        };
        mesh.VertexBuffers = new List<FLVER2.VertexBuffer>();
        mesh.VertexBuffers.Add(new FLVER2.VertexBuffer(layout));
        foreach (var v in verts)
            mesh.Vertices.Add(v);

        // 6 facesets comme sur la vanille (LOD0, LOD1, LOD2, motion blur...)
        var flags = new FLVER2.FaceSet.FSFlags[]
        {
            FLVER2.FaceSet.FSFlags.None,
            FLVER2.FaceSet.FSFlags.LodLevel1,
            FLVER2.FaceSet.FSFlags.LodLevel2,
            FLVER2.FaceSet.FSFlags.MotionBlur,
            FLVER2.FaceSet.FSFlags.LodLevel1 | FLVER2.FaceSet.FSFlags.MotionBlur,
            FLVER2.FaceSet.FSFlags.LodLevel2 | FLVER2.FaceSet.FSFlags.MotionBlur,
        };
        mesh.FaceSets = new List<FLVER2.FaceSet>();
        foreach (var fl in flags)
        {
            mesh.FaceSets.Add(new FLVER2.FaceSet
            {
                Flags = fl,
                TriangleStrip = false,
                CullBackfaces = false,
                Unk06 = 1,
                Indices = new List<int>(idx)
            });
        }
        mesh.BoundingBox = new FLVER2.Mesh.BoundingBoxes();
        mesh.BoundingBox.Min = lo;
        mesh.BoundingBox.Max = hi;
        mesh.BoundingBox.Unk = Vector3.Zero;

        f.Meshes[slot] = mesh;
        Console.WriteLine("remplace : " + n + " sommets, " + (ni / 3) + " triangles, noeud " + node);

        f.Write(dst);
        Console.WriteLine("ecrit : " + dst);
        return 0;
    }
}
