; Anime1 Desktop Windows Installer (NSIS)
; 使用方法: makensis scripts/create_installer.nsi

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

; 界面设置
!define MUI_ICON "static\app.ico"
!define MUI_UNICON "static\app.ico"
!define MUI_ABORTWARNING

; 安装程序名称
Name "${APPNAME}"
Caption "${APPNAME} v${VERSIONMAJOR}.${VERSIONMINOR} - 安装向导"
OutFile "release\anime1-windows-x64-setup.exe"
InstallDir "${INSTDIR}"
InstallDirRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}" "InstallDir" "${INSTDIR}"
ShowInstDetails show
ShowUnInstDetails show

; 静默安装选项
!include "Quiet.nsh"

; 版本信息
VIProductVersion "${VERSIONMAJOR}.${VERSIONMINOR}.0.0"
VIAddVersionKey /LANG=2052 "ProductName" "${APPNAME}"
VIAddVersionKey /LANG=2052 "CompanyName" "${COMPANYNAME}"
VIAddVersionKey /LANG=2052 "FileDescription" "${DESCRIPTION}"
VIAddVersionKey /LANG=2052 "FileVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.0.0"
VIAddVersionKey /LANG=2052 "LegalCopyright" "Copyright (C) 2024 ${COMPANYNAME}. All rights reserved."

; ----------------------------------------------
; 界面语言
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

; ----------------------------------------------
; 安装前检查

Function .onInit
    ; 检查 Windows 版本
    ${If} ${AtLeastWinVista}
        ; Windows Vista 或更高版本，检查管理员权限
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

    ; 设置安装详细信息
    SetDetailsPrint textonly

    ; 创建安装目录
    CreateDirectory "$INSTDIR"

    DetailPrint "正在安装主程序文件..."

    ; 复制整个应用目录
    SetOutPath "$INSTDIR"
    File /r "dist\anime1\*.*"

    ; 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\Anime1.exe" "" "$INSTDIR\app.ico" 0

    ; 创建桌面快捷方式（可选）
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\Anime1.exe" "" "$INSTDIR\app.ico" 0

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

    ; 完成信息
    SetDetailsPrint both
    DetailPrint ""
    DetailPrint "安装完成！"
    DetailPrint ""
    SetAutoClose true

SectionEnd

; ----------------------------------------------
; 卸载部分

Section "Uninstall"

    ; 移除快捷方式
    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    RMDir "$SMPROGRAMS\${APPNAME}"
    Delete "$DESKTOP\${APPNAME}.lnk"

    ; 移除安装目录下的所有文件
    Delete "$INSTDIR\*.*"
    RMDir /r "$INSTDIR"

    ; 移除注册表项
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    DeleteRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}"

    ; 完成信息
    SetDetailsPrint both
    DetailPrint ""
    DetailPrint "卸载完成！"
    DetailPrint "感谢使用 ${APPNAME}。"

SectionEnd

; ----------------------------------------------
; 安装完成页面

!insertmacro MUI_PAGE_FINISH

; ----------------------------------------------
; 卸载开始页面

UninstPage uninstConfirm
UninstPage uninstFinished

; ----------------------------------------------
; 语言文件

LangString DESC_SecMain ${2052} "Anime1 桌面应用程序"
LangString DESC_SecMain ${1033} "Anime1 Desktop Application"

; ----------------------------------------------
; 安装脚本结束
