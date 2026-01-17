; Anime1 Desktop Windows Installer (NSIS)

!define APPNAME "Anime1"
!define COMPANYNAME "Anime1"
!define DESCRIPTION "Anime1 Desktop - 番剧浏览器"
!define VERSIONMAJOR 0
!define VERSIONMINOR 1
!define INSTALLSIZE 120000

; 安装目录
!define INSTDIR "$PROGRAMFILES\${APPNAME}"

; MUI settings
!include "MUI2.nsh"
!include "WinVer.nsh"

; 安装程序名称
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

    ; 设置压缩
    SetCompressor /SOLID lzma

FunctionEnd

; ----------------------------------------------
; 安装部分

Section "Main Application" SecMain
    SectionIn RO

    SetDetailsPrint textonly

    ; 创建安装目录
    CreateDirectory "$INSTDIR"

    DetailPrint "正在安装主程序文件..."

    ; 复制整个应用目录
    SetOutPath "$INSTDIR"
    File /r "dist\anime1\*.*"

    ; 检查 app.ico 是否存在，不存在则使用内置默认图标
    IfFileExists "$INSTDIR\app.ico" 0 SkipIcon

    ; 创建开始菜单快捷方式（带图标）
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\Anime1.exe" "" "$INSTDIR\app.ico" 0
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\Anime1.exe" "" "$INSTDIR\app.ico" 0

    Goto DoneShortcuts

SkipIcon:
    ; 没有图标时创建快捷方式
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\Anime1.exe"
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\Anime1.exe"

DoneShortcuts:

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

    SetDetailsPrint both
    DetailPrint ""
    DetailPrint "安装完成！"
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

    SetDetailsPrint both
    DetailPrint ""
    DetailPrint "卸载完成！感谢使用 ${APPNAME}。"

SectionEnd

; ----------------------------------------------
; 页面（必须在 MUI_LANGUAGE 之前）

!insertmacro MUI_PAGE_FINISH

UninstPage uninstConfirm
UninstPage uninstFinished

; ----------------------------------------------
; 界面语言（必须在页面之后）

!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

; ----------------------------------------------
; 安装脚本结束
