"""Porte TagTools.py (Python 2) vers Python 3 - transformations textuelles minimales."""
import re
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()

# 2 -> 3 basiques
s = s.replace("xrange(", "range(")
s = s.replace(".iteritems()", ".items()")
s = s.replace("long(text)", "int(text)")
s = s.replace(".has_key(", ".__contains__(")

# has_key -> in (formes explicites)
s = re.sub(r"if (self\.patches)\.__contains__\(([^)]+)\):", r"if \2 in \1:", s)
s = re.sub(r"if (obj\.value)\.__contains__\(([^)]+)\):", r"if \2 in \1:", s)
s = re.sub(r"if (elem\.attrib)\.__contains__\(([^)]+)\):", r"if \2 in \1:", s)
s = re.sub(r"if (TagXmlSerializerSpecialTypeNames)\.__contains__\(([^)]+)\):", r"if \2 in \1:", s)

# prints
s = re.sub(r'^(\s*)print "(.*)"$', r'\1print("\2")', s, flags=re.M)
s = s.replace('print "\\nUsage: {} [source] [compendium] [destination]".format(os.path.basename(sys.argv[0]))',
              'print("\\nUsage: {} [source] [compendium] [destination]".format(os.path.basename(sys.argv[0])))')
s = s.replace("raw_input()", "input()")

# octets <-> texte
s = s.replace("self.signature = r.f.read( 4 )", 'self.signature = r.f.read( 4 ).decode("latin-1")')
s = s.replace("signature = f.read( 4 )", 'signature = f.read( 4 ).decode("latin-1")')
s = s.replace('typeStrings = self.f.read(t3.size).split("\\0")',
              'typeStrings = self.f.read(t3.size).decode("latin-1").split("\\0")')
s = s.replace('fieldStrings = self.f.read(t5.size).split("\\0")',
              'fieldStrings = self.f.read(t5.size).decode("latin-1").split("\\0")')
s = s.replace('self.f.write("\\0".join(typeStrings) + "\\0")',
              'self.f.write(("\\0".join(typeStrings) + "\\0").encode("latin-1"))')
s = s.replace('self.f.write("\\0".join(fieldStrings) + "\\0")',
              'self.f.write(("\\0".join(fieldStrings) + "\\0").encode("latin-1"))')
s = s.replace('self.f.write("20160100")', 'self.f.write(b"20160100")')
s = s.replace('self.f.write("\\0" * amount)', 'self.f.write(b"\\0" * amount)')
s = s.replace("w.f.write(signature[:4])", 'w.f.write(signature[:4].encode("latin-1"))')

# division entiere
s = s.replace("t4.size / 8", "t4.size // 8")

open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
