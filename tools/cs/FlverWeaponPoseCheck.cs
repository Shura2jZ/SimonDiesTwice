using System;
using System.Globalization;
using System.IO;
using System.Numerics;
using SoulsFormats;
internal static class FlverWeaponPoseCheck
{
 static void Main(string[] a){var f=FLVER2.Read(a[0]);var pose=File.ReadAllLines(a[1]);Vector3 hand=Vector3.Zero,kat=Vector3.Zero;foreach(var l in pose){var c=l.Split('\t');if(c.Length<17)continue;var p=new Vector3(float.Parse(c[13],CultureInfo.InvariantCulture),float.Parse(c[14],CultureInfo.InvariantCulture),float.Parse(c[15],CultureInfo.InvariantCulture));if(c[0]=="R_Hand")hand=p;if(c[0]=="R_Katana")kat=p;}Console.WriteLine("hand ({0:F4},{1:F4},{2:F4}) katana ({3:F4},{4:F4},{5:F4})",hand.X,hand.Y,hand.Z,kat.X,kat.Y,kat.Z);foreach(int si in new[]{10,12,27,30}){if(si>=f.Meshes.Count)continue;var m=f.Meshes[si];float dHand=float.MaxValue,dKat=float.MaxValue;Vector3 vHand=Vector3.Zero,vKat=Vector3.Zero,lo=new Vector3(float.MaxValue),hi=new Vector3(float.MinValue);var used=new System.Collections.Generic.HashSet<int>();foreach(var fs in m.FaceSets)foreach(int ix in fs.Indices)if(ix>=0&&ix<m.Vertices.Count)used.Add(ix);foreach(int ix in used){var v=m.Vertices[ix];lo=Vector3.Min(lo,v.Position);hi=Vector3.Max(hi,v.Position);float dh=Vector3.Distance(hand,v.Position),dk=Vector3.Distance(kat,v.Position);if(dh<dHand){dHand=dh;vHand=v.Position;}if(dk<dKat){dKat=dk;vKat=v.Position;}}Console.WriteLine("slot {0} mat {1} used {2} bbox ({3:F3},{4:F3},{5:F3})..({6:F3},{7:F3},{8:F3}) nearestHand {9:F3} @({10:F3},{11:F3},{12:F3}) nearestKatana {13:F3} @({14:F3},{15:F3},{16:F3})",si,m.MaterialIndex,used.Count,lo.X,lo.Y,lo.Z,hi.X,hi.Y,hi.Z,dHand,vHand.X,vHand.Y,vHand.Z,dKat,vKat.X,vKat.Y,vKat.Z);}}
}
