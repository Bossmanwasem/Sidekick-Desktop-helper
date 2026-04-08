#define AppName "Simple File Zipper"
#define AppVersion "1.0.0"
#define AppPublisher "Sidekick"
#define AppExeName "SimpleFileZipper.exe"
#define AppId "{{D476B0F0-28D6-4BE8-89E9-56D2DA3EA62D}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Simple File Zipper
DefaultGroupName=Simple File Zipper
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=SimpleFileZipper-Setup-{#AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\bin\Release\net8.0-windows\win-x64\publish\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Simple File Zipper"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\Simple File Zipper"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch Simple File Zipper"; Flags: nowait postinstall skipifsilent
