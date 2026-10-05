<#
    AutoSprint 1.7.10 - ForgeGradle-free manual build.

    Why: ForgeGradle 1.2 downloads the vanilla Minecraft jar from
    http://s3.amazonaws.com/Minecraft.Download/... which is dead today (404),
    so `gradle setupDecompWorkspace` cannot work out of the box anymore.
    This script does the same job with plain tools:

      vanilla client jar --(MCP joined.srg)--> MCP names  (compile classpath)
      Forge universal jar --(same mapping)----> srg names  (compile classpath)
      javac  ->  merge with MC classes  ->  SpecialSource (MCP -> srg)  ->  jar

    Requirements:
      * JDK 8  (pass -JavaHome 'C:\Program Files\Java\jdk-1.8' if JAVA_HOME is not set)
      * Python 3 on PATH (or pass -Python 'C:\path\to\python.exe')
      * internet access for the first run (about 12 MB of downloads)

    Usage:
      powershell -ExecutionPolicy Bypass -File tools\build-manual.ps1
#>
[CmdletBinding()]
param(
    [string]$WorkDir  = '',
    [string]$Python   = 'python',
    [string]$JavaHome = $env:JAVA_HOME
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# NOTE: $PSScriptRoot is not available inside the param() block on Windows PowerShell 5.1,
# so the default work dir is resolved here.
if (-not $WorkDir) { $WorkDir = Join-Path $PSScriptRoot '..\build-manual' }

$proj = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$WorkDir = [System.IO.Path]::GetFullPath($WorkDir)
$tools = Join-Path $WorkDir 'tools'
New-Item -ItemType Directory -Force -Path $tools | Out-Null

if ($JavaHome) {
    $java = Join-Path $JavaHome 'bin\java.exe'
    $javac = Join-Path $JavaHome 'bin\javac.exe'
} else {
    $java = 'java'
    $javac = 'javac'
}

Write-Host "project : $proj"
Write-Host "workdir : $WorkDir"
Write-Host "java    : $java"

$downloads = @(
    @{ url = 'https://bmclapi2.bangbang93.com/version/1.7.10/client'; file = 'client.jar' },
    @{ url = 'https://maven.minecraftforge.net/de/oceanlabs/mcp/mcp/1.7.10/mcp-1.7.10-srg.zip'; file = 'mcp_srg.zip' },
    @{ url = 'https://maven.minecraftforge.net/de/oceanlabs/mcp/mcp_stable/12-1.7.10/mcp_stable-12-1.7.10.zip'; file = 'mcp_stable.zip' },
    @{ url = 'https://maven.minecraftforge.net/net/minecraftforge/forge/1.7.10-10.13.4.1614-1.7.10/forge-1.7.10-10.13.4.1614-1.7.10-universal.jar'; file = 'forge-universal.jar' },
    @{ url = 'https://repo1.maven.org/maven2/net/md-5/SpecialSource/1.7.4/SpecialSource-1.7.4.jar'; file = 'SpecialSource.jar' },
    @{ url = 'https://repo1.maven.org/maven2/net/sf/jopt-simple/jopt-simple/5.0.1/jopt-simple-5.0.1.jar'; file = 'jopt-simple.jar' },
    @{ url = 'https://repo1.maven.org/maven2/org/ow2/asm/asm-debug-all/5.1/asm-debug-all-5.1.jar'; file = 'asm-debug-all.jar' },
    @{ url = 'https://repo1.maven.org/maven2/com/google/guava/guava/19.0/guava-19.0.jar'; file = 'guava.jar' },
    @{ url = 'https://libraries.minecraft.net/org/lwjgl/lwjgl/lwjgl/2.9.1/lwjgl-2.9.1.jar'; file = 'lwjgl.jar' }
)

foreach ($d in $downloads) {
    $dest = Join-Path $tools $d.file
    if (-not (Test-Path $dest)) {
        Write-Host ("download " + $d.file)
        Invoke-WebRequest -Uri $d.url -OutFile $dest -UseBasicParsing -TimeoutSec 300
    }
}

$ssCp = @(
    (Join-Path $tools 'SpecialSource.jar'),
    (Join-Path $tools 'jopt-simple.jar'),
    (Join-Path $tools 'asm-debug-all.jar'),
    (Join-Path $tools 'guava.jar')
) -join ';'

function Invoke-Remap([string]$inJar, [string]$outJar, [string]$srg) {
    Write-Host ("remap " + (Split-Path $inJar -Leaf) + " -> " + (Split-Path $outJar -Leaf))
    & $java -Xmx2G -cp $ssCp net.md_5.specialsource.SpecialSource --in-jar $inJar --out-jar $outJar --srg-in $srg --quiet
    if ($LASTEXITCODE -ne 0) { throw ("SpecialSource failed on " + $inJar) }
}

Write-Host '[1/5] generating mappings'
& $Python (Join-Path $PSScriptRoot 'gen_srg.py') `
    (Join-Path $tools 'mcp_srg.zip') (Join-Path $tools 'mcp_stable.zip') `
    (Join-Path $tools 'obf2mcp.srg') (Join-Path $tools 'mcp2srg.srg') (Join-Path $tools 'obf2srg.srg')
if ($LASTEXITCODE -ne 0) { throw 'gen_srg.py failed' }

Write-Host '[2/5] deobfuscating Minecraft and Forge'
Invoke-Remap (Join-Path $tools 'client.jar') (Join-Path $tools 'mc-mcp.jar') (Join-Path $tools 'obf2mcp.srg')
Invoke-Remap (Join-Path $tools 'forge-universal.jar') (Join-Path $tools 'forge-srg.jar') (Join-Path $tools 'obf2srg.srg')

Write-Host '[3/5] compiling'
$classes = Join-Path $WorkDir 'classes-mcp'
Remove-Item $classes -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $classes | Out-Null
$cp = @(
    (Join-Path $tools 'mc-mcp.jar'),
    (Join-Path $tools 'forge-srg.jar'),
    (Join-Path $tools 'lwjgl.jar')
) -join ';'
$sources = Get-ChildItem (Join-Path $proj 'src\main\java') -Recurse -Filter *.java | Select-Object -ExpandProperty FullName
& $javac -encoding UTF-8 -source 1.7 -target 1.7 -nowarn -d $classes -cp $cp $sources
if ($LASTEXITCODE -ne 0) { throw 'javac failed' }

Write-Host '[4/5] reobfuscating to srg names'
& $Python (Join-Path $PSScriptRoot 'pack.py') merge $WorkDir
if ($LASTEXITCODE -ne 0) { throw 'pack.py merge failed' }
Invoke-Remap (Join-Path $WorkDir 'merge.jar') (Join-Path $WorkDir 'merge-srg.jar') (Join-Path $tools 'mcp2srg.srg')

Write-Host '[5/5] packaging'
$outDir = Join-Path $proj 'build\libs'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outJar = Join-Path $outDir 'AutoSprint-1.7.10-1.0.0.jar'
& $Python (Join-Path $PSScriptRoot 'pack.py') pack $WorkDir $proj $outJar
if ($LASTEXITCODE -ne 0) { throw 'pack.py pack failed' }

Write-Host ''
Write-Host ('BUILD OK -> ' + $outJar)
