// FlverTextures.exe -- liste les textures referencees par chaque materiau.
using System;
using System.Collections;
using System.Reflection;
using SoulsFormats;

internal static class FlverTextures
{
    private static object Get(object o, string name)
    {
        PropertyInfo p = o.GetType().GetProperty(name);
        if (p != null) return p.GetValue(o);
        FieldInfo f = o.GetType().GetField(name);
        return f != null ? f.GetValue(o) : null;
    }

    private static int Main(string[] args)
    {
        FLVER2 f = FLVER2.Read(args[0]);
        int mi = 0;
        foreach (object m in f.Materials)
        {
            object texs = Get(m, "Textures");
            Console.WriteLine("materiau " + mi + " (" + Get(m, "Name") + ") :");
            if (texs is IEnumerable)
                foreach (object t in (IEnumerable)texs)
                    Console.WriteLine("    " + Get(t, "Type") + "  ->  " + Get(t, "Path"));
            mi++;
        }
        return 0;
    }
}
