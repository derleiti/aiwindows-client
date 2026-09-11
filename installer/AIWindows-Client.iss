#ifndef MyAppVersion
  #define MyAppVersion "1.0.1"
#endif
#ifndef MyAppExe
  #define MyAppExe "AIWindows-Client.exe"
#endif

#define MyAppName "AIWindows Client"
#define MyAppPublisher "AILinux"
#define MyAppURL "https://ailinux.me"

[Setup]
AppId={{7E449616-5F95-4F79-98B5-52FC454CB388}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\AILinux\AIWindows Client
DefaultGroupName=AILinux
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=AIWindows-Client-Setup-{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\AIWindows-Client.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "..\dist\{#MyAppExe}"; DestDir: "{app}"; DestName: "AIWindows-Client.exe"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\AILinux\AIWindows Client"; Filename: "{app}\AIWindows-Client.exe"
Name: "{autodesktop}\AIWindows Client"; Filename: "{app}\AIWindows-Client.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung erstellen"; GroupDescription: "Zusätzliche Verknüpfungen:"; Flags: unchecked

[Run]
Filename: "{app}\AIWindows-Client.exe"; Description: "AIWindows Client starten"; Flags: nowait postinstall skipifsilent
