; Anime1 Desktop Windows Installer (NSIS)
; Simplified installer without MUI2

; 包含 Windows 版本检查宏
!include WinVer.nsh

; 压缩设置（必须放在最前面）
SetCompressor /SOLID lzma

!define APPNAME "Anime1"
!define COMPANYNAME "Anime1"
!define DESCRIPTION "Anime1 Desktop - 番剧浏览器"
!define VERSIONMAJOR 0
!define VERSIONMINOR 1
!define INSTALLSIZE 120000
!define INSTDIR "$PROGRAMFILES\${APPNAME}"

; 基础设置
Name "${APPNAME}"
Caption "${APPNAME} v${VERSIONMAJOR}.${VERSIONMINOR} - 安装向导"
OutFile "release\anime1-windows-x64-setup.exe"
InstallDir "${INSTDIR}"
InstallDirRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}" "InstallDir"
ShowInstDetails show
ShowUnInstDetails show

; 版本信息
VIProductVersion "${VERSIONMAJOR}.${VERSIONMINOR}.0.0"
VIAddVersionKey /LANG=2052 "ProductName" "${APPNAME}"
VIAddVersionKey /LANG=2052 "CompanyName" "${COMPANYNAME}"
VIAddVersionKey /LANG=2052 "FileDescription" "${DESCRIPTION}"
VIAddVersionKey /LANG=2052 "FileVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.0.0"
VIAddVersionKey /LANG=2052 "LegalCopyright" "Copyright (C) 2024 ${COMPANYNAME}. All rights reserved."

; ----------------------------------------------
; 安装前检查

Function .onInit
    ; 检查 Windows 版本
    ${If} ${AtLeastWinVista}
        UserInfo::GetAccountType
        Pop $0
        ${If} $0 != "Admin"
            MessageBox MB_OK|MB_ICONSTOP "安装程序需要管理员权限。请右键点击安装程序，选择'以管理员身份运行'。"
            Quit
        ${EndIf}
    ${Else}
        MessageBox MB_OK|MB_ICONSTOP "此程序需要 Windows Vista 或更高版本。"
        Quit
    ${EndIf}
FunctionEnd

; ----------------------------------------------
; 安装页面

Page directory
Page instfiles

; ----------------------------------------------
; 卸载页面

UninstPage uninstConfirm
UninstPage instfiles

; ----------------------------------------------
; 安装部分

Section "Main Application" SecMain
    SectionIn RO

    ; 使用 FilesTree 递归复制整个目录
    SetOutPath "$INSTDIR"
    File /nonfatal /r "dist\anime1"

    ; 检查 app.ico 是否存在
    IfFileExists "$INSTDIR\app.ico" 0 SkipIcon

    ; 有图标时创建快捷方式
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\Anime1.exe" "" "$INSTDIR\app.ico" 0
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\Anime1.exe" "" "$INSTDIR\app.ico" 0
    Goto AfterShortcuts

SkipIcon:
    ; 没有图标时创建快捷方式
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\Anime1.exe"
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\Anime1.exe"

AfterShortcuts:

    ; 创建卸载程序
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; 添加卸载信息到控制面板
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

    ; 添加安装信息
    WriteRegStr HKLM "Software\${COMPANYNAME}\${APPNAME}" \
                     "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\${COMPANYNAME}\${APPNAME}" \
                     "Version" "${VERSIONMAJOR}.${VERSIONMINOR}"

    ; 完成
    SetAutoClose true

SectionEnd

; ----------------------------------------------
; 卸载部分

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
