; Anime1 Desktop Windows Installer (NSIS)
; Simplified installer without MUI2

; Compressor settings (must be at top)
SetCompressor /SOLID lzma

!define APPNAME "Anime1"
!define COMPANYNAME "Anime1"
!define DESCRIPTION "Anime1 Desktop - Anime Browser"
!define VERSIONMAJOR 0
!define VERSIONMINOR 1
!define INSTALLSIZE 120000
!define INSTDIR "$PROGRAMFILES\${APPNAME}"

; Basic settings
Name "${APPNAME}"
Caption "${APPNAME} v${VERSIONMAJOR}.${VERSIONMINOR} - Installation Wizard"
OutFile "release\anime1-windows-x64-setup.exe"
InstallDir "${INSTDIR}"
InstallDirRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}" "InstallDir"
ShowInstDetails show
ShowUnInstDetails show

; Version info
VIProductVersion "${VERSIONMAJOR}.${VERSIONMINOR}.0.0"
VIAddVersionKey /LANG=2052 "ProductName" "${APPNAME}"
VIAddVersionKey /LANG=2052 "CompanyName" "${COMPANYNAME}"
VIAddVersionKey /LANG=2052 "FileDescription" "${DESCRIPTION}"
VIAddVersionKey /LANG=2052 "FileVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.0.0"
VIAddVersionKey /LANG=2052 "LegalCopyright" "Copyright (C) 2024 ${COMPANYNAME}. All rights reserved."

; Include LogicLib for ${If} statements
!include LogicLib.nsh

; ----------------------------------------------
; Pre-install check

Function .onInit
    ; Check if admin (simplified)
    InitPluginsDir
FunctionEnd

; ----------------------------------------------
; Installation pages

Page directory
Page instfiles

; ----------------------------------------------
; Uninstall pages

UninstPage uninstConfirm
UninstPage instfiles

; ----------------------------------------------
; Installation section

Section "Main Application" SecMain
    SectionIn RO

    ; Set output path
    SetOutPath "$INSTDIR"

    ; Copy entire app directory (use $EXEDIR for relative path from script location)
    SetOutPath "$INSTDIR"
    File /r "$EXEDIR\dist\Anime1"

    ; Check if app.ico exists
    IfFileExists "$INSTDIR\app.ico" 0 SkipIcon

    ; Create shortcuts with icon
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\Anime1.exe" "" "$INSTDIR\app.ico" 0
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\Anime1.exe" "" "$INSTDIR\app.ico" 0
    Goto AfterShortcuts

SkipIcon:
    ; Create shortcuts without icon
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\Anime1.exe"
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\Anime1.exe"

AfterShortcuts:

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Add uninstall info to control panel
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "DisplayIcon" "$INSTDIR\app.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "Publisher" "${COMPANYNAME}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "NoRepair" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
                     "EstimatedSize" ${INSTALLSIZE}

    ; Add install info
    WriteRegStr HKLM "Software\${COMPANYNAME}\${APPNAME}" \
                     "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\${COMPANYNAME}\${APPNAME}" \
                     "Version" "${VERSIONMAJOR}.${VERSIONMINOR}"

    ; Finish
    SetAutoClose true

SectionEnd

; ----------------------------------------------
; Uninstall section

Section "Uninstall"

    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    RMDir "$SMPROGRAMS\${APPNAME}"
    Delete "$DESKTOP\${APPNAME}.lnk"

    Delete "$INSTDIR\*.*"
    RMDir /r "$INSTDIR"

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    DeleteRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}"

    SetAutoClose true

SectionEnd
