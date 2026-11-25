# Compile un (ou tous les) fichier(s) .cs de _work\tools\cs vers un .exe,
# avec reference a SoulsFormats.dll de FLVER_Editor.
#
# Usage :
#   powershell -File tools\cs_build.ps1 NomDuFichier        # compile NomDuFichier.cs
#   powershell -File tools\cs_build.ps1                     # compile tous les .cs (une exe chacun)
param([string]$Only)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$srcDir = Join-Path $root "_work\tools\cs"
$dbg = Join-Path $root "_work\tools\FLVER_Editor_X2.7\Debug"
$csc = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

if (-not (Test-Path $csc)) { throw "csc.exe introuvable : $csc" }
if (-not (Test-Path (Join-Path $dbg "SoulsFormats.dll"))) { throw "SoulsFormats.dll introuvable dans $dbg" }

# references : SoulsFormats + System.Numerics (BCL) + les assemblies dont il depend
$numerics = @(
    "C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8\System.Numerics.dll",
    "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\System.Numerics.dll",
    "C:\Windows\Microsoft.NET\Framework\v4.0.30319\System.Numerics.dll"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $numerics) { $numerics = (Get-ChildItem "C:\Windows\Microsoft.NET\assembly\GAC_MSIL\System.Numerics" -Recurse -Filter "System.Numerics.dll" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName) }
if (-not $numerics) { throw "System.Numerics.dll introuvable" }

$refs = @("SoulsFormats.dll", "System.Memory.dll", "System.Buffers.dll",
          "System.Runtime.CompilerServices.Unsafe.dll", "System.Text.Encoding.CodePages.dll") |
        ForEach-Object { Join-Path $dbg $_ } | Where-Object { Test-Path $_ } | ForEach-Object { "/r:" + $_ }
$refs += "/r:" + $numerics

# System.Web.Extensions (JavaScriptSerializer) : necessaire pour fabriquer les
# fichiers de pose lus par le CLI de rendu.
$web = @(
    "C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8\System.Web.Extensions.dll",
    "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\System.Web.Extensions.dll"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($web) { $refs += "/r:" + $web }

# System.Drawing : comparaison d'images (PngDiff).
$drawing = @(
    "C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8\System.Drawing.dll",
    "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\System.Drawing.dll"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($drawing) { $refs += "/r:" + $drawing }

$files = if ($Only) { Get-ChildItem (Join-Path $srcDir "$Only.cs") } else { Get-ChildItem (Join-Path $srcDir "*.cs") }
foreach ($f in $files) {
    $exe = [IO.Path]::ChangeExtension($f.FullName, ".exe")
    & $csc /nologo /target:exe /platform:anycpu /optimize+ /out:$exe @refs $f.FullName
    if ($LASTEXITCODE -ne 0) { throw "echec de compilation : $($f.Name)" }

    # redirection d'assembly : SoulsFormats (net48) attend Unsafe 4.0.4.1 mais la release fournit 6.0.0.0
    $cfg = @'
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <startup>
    <supportedRuntime version="v4.0" sku=".NETFramework,Version=v4.8" />
  </startup>
  <runtime>
    <assemblyBinding xmlns="urn:schemas-microsoft-com:asm.v1">
      <dependentAssembly>
        <assemblyIdentity name="System.Runtime.CompilerServices.Unsafe" publicKeyToken="b03f5f7f11d50a3a" culture="neutral" />
        <bindingRedirect oldVersion="0.0.0.0-6.0.0.0" newVersion="6.0.0.0" />
      </dependentAssembly>
    </assemblyBinding>
  </runtime>
</configuration>
'@
    Set-Content -Path ($exe + ".config") -Value $cfg -Encoding UTF8
    Write-Output ("compile : " + $f.Name + " -> " + (Split-Path -Leaf $exe) + "  (+ .exe.config)")
}

# les assemblies dependantes doivent se trouver a cote de l'exe a l'execution
foreach ($d in @("SoulsFormats.dll", "System.Numerics.Vectors.dll", "System.Memory.dll", "System.Buffers.dll",
                 "System.Runtime.CompilerServices.Unsafe.dll", "System.Text.Encoding.CodePages.dll")) {
    $src = Join-Path $dbg $d
    $dst = Join-Path $srcDir $d
    if ((Test-Path $src) -and -not (Test-Path $dst)) { Copy-Item $src $dst }
}
