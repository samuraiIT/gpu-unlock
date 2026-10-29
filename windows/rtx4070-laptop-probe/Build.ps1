param(
    [string]$VcVars = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat',
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
if (!(Test-Path -LiteralPath $VcVars)) { throw 'MSVC setup unavailable' }
if ($VcVars -match '["&|<>%^!\r\n]' -or $PSScriptRoot -match '["&|<>%^!\r\n]') { throw 'Unsupported build path' }
& $Python (Join-Path $PSScriptRoot 'tests\verify_pe.py') --headers-only
if ($LASTEXITCODE -ne 0) { throw 'Pinned vendor header verification failed' }
New-Item -ItemType Directory -Force (Join-Path $PSScriptRoot 'build') | Out-Null
$hashes = Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'src') -File | Sort-Object Name | ForEach-Object { $_.Name + '=' + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
$hashes += 'headers=' + (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'vendor\edk2\headers.json') -Algorithm SHA256).Hash
$hashes += 'build=' + (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
$sha = [Security.Cryptography.SHA256]::Create()
try { $buildId = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes(($hashes -join "`n")))).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
Set-Content -LiteralPath (Join-Path $PSScriptRoot 'build\build_id.h') -Value ('#define PROBE_BUILD_ID "' + $buildId + '"') -Encoding ascii
$script = @"
@echo off
call "$VcVars" >nul
if errorlevel 1 exit /b 1
cd /d "$PSScriptRoot"
cl /nologo /W4 /WX /O2 /Oi /GS- /Gs65536 /Zl /c /TC /Ivendor\edk2\Include /Ivendor\edk2\Include\X64 /Fobuild\core.obj src\core.c
if errorlevel 1 exit /b 1
cl /nologo /W4 /WX /O2 /Oi /GS- /Gs65536 /Zl /c /TC /Ibuild /FIbuild_id.h /Ivendor\edk2\Include /Ivendor\edk2\Include\X64 /Fobuild\probe.obj src\probe.c
if errorlevel 1 exit /b 1
cl /nologo /W4 /WX /O2 /Oi /GS- /Gs65536 /Zl /c /TC /Ivendor\edk2\Include /Ivendor\edk2\Include\X64 /Fobuild\platform.obj src\platform.c
if errorlevel 1 exit /b 1
cl /nologo /W4 /WX /Od /Oi- /GS- /Zl /c /TC /Ivendor\edk2\Include /Ivendor\edk2\Include\X64 /Fobuild\runtime.obj src\runtime.c
if errorlevel 1 exit /b 1
link /nologo /Brepro /subsystem:efi_application /entry:UefiMain /machine:x64 /nodefaultlib /incremental:no /fixed:no /dynamicbase:no /nxcompat:no /out:build\RTX4070-PROBE.EFI build\core.obj build\probe.obj build\platform.obj build\runtime.obj
if errorlevel 1 exit /b 1
cl /nologo /W4 /WX /Od /D_CRT_SECURE_NO_WARNINGS /Ibuild /FIbuild_id.h /Ivendor\edk2\Include /Ivendor\edk2\Include\X64 tests\host_tests.c src\core.c src\platform.c /Febuild\host-tests.exe /Fobuild\
if errorlevel 1 exit /b 1
build\host-tests.exe
if errorlevel 1 exit /b 1
cl /nologo /W4 /WX /Od /D_CRT_SECURE_NO_WARNINGS /Ivendor\edk2\Include /Ivendor\edk2\Include\X64 tests\platform_tests.c src\core.c src\platform.c /Febuild\platform-tests.exe /Fobuild\
if errorlevel 1 exit /b 1
build\platform-tests.exe
if errorlevel 1 exit /b 1
"@
$cmd = Join-Path $PSScriptRoot 'build\compile.cmd'
Set-Content -LiteralPath $cmd -Value $script -Encoding ascii
& $env:ComSpec /d /c $cmd
if ($LASTEXITCODE -ne 0) { throw 'Build or test failure' }

& $Python (Join-Path $PSScriptRoot 'tests\verify_pe.py')
if ($LASTEXITCODE -ne 0) { throw 'PE verification failure' }
$manifest = [ordered]@{
    version = '0.2.0-research'
    build_id = $buildId
    binary = 'RTX4070-PROBE.EFI'
    sha256 = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'build\RTX4070-PROBE.EFI') -Algorithm SHA256).Hash.ToLowerInvariant()
    source_hashes = $hashes
    hardware_tested = $false
    unlock_implemented = $false
    gpu_writes = $false
    mmio_reads = $false
    validation = 'MSVC host mocks; pinned headers; PE and mock JSON checks'
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'build\manifest.json') -Encoding utf8
Write-Output ('EFI SHA256: ' + $manifest.sha256)
