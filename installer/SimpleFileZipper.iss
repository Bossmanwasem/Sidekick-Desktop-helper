#define AppName "Smartbox Vocab Zipper"
#define AppVersion "1.1.0"
#define AppPublisher "Sidekick"
#define AppExeName "SmartboxVocabZipper.exe"
#define AppId "{{D476B0F0-28D6-4BE8-89E9-56D2DA3EA62D}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Smartbox Vocab Zipper
DefaultGroupName=Smartbox Vocab Zipper
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=SmartboxVocabZipper-Setup-{#AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}
PrivilegesRequired=admin
SetupIconFile=..\assets\install-icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\dist\SmartboxVocabZipper.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Smartbox Vocab Zipper"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\Smartbox Vocab Zipper"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch Smartbox Vocab Zipper"; Flags: nowait postinstall skipifsilent
