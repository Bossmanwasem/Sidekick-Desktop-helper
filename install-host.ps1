param(
    [Parameter(Mandatory = $true)]
    [string]$ManifestPath
)

$resolvedManifest = (Resolve-Path $ManifestPath).Path
$keyPath = 'HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\com.sidekick.helper'

New-Item -Path $keyPath -Force | Out-Null
Set-ItemProperty -Path $keyPath -Name '(default)' -Value $resolvedManifest

Write-Host "Registered native messaging host manifest: $resolvedManifest"
