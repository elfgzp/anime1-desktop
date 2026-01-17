# typed: true
# frozen_string_literal: true

# Homebrew Cask for Anime1 Desktop
# https://github.com/anime1-desktop/anime1-desktop
#
# 安装方法:
#   brew install --cask ./homebrew/anime1.rb
#
# 或从本地 DMG 安装:
#   brew install --cask /path/to/anime1-macos-*.dmg
#

cask "anime1" do
  version "VERSION"
  sha256 "CHECKSUM"

  url "https://github.com/anime1-desktop/anime1-desktop/releases/download/v#{version}/anime1-macos-ARCH.dmg"
  name "Anime1"
  desc "Anime1 desktop application"
  homepage "https://github.com/anime1-desktop/anime1-desktop"

  auto_updates true
  license :mit

  if Hardware::CPU.arm?
    url "https://github.com/anime1-desktop/anime1-desktop/releases/download/v#{version}/anime1-macos-arm64.dmg"
    sha256 "ARM64_CHECKSUM"
    architecture :arm
  elsif Hardware::CPU.intel?
    url "https://github.com/anime1-desktop/anime1-desktop/releases/download/v#{version}/anime1-macos-x64.dmg"
    sha256 "X64_CHECKSUM"
    architecture :intel
  end

  app "Anime1.app"

  # 安装后自动修复签名问题
  postflight do
    system_command "xattr",
                   args: ["-r", "-d", "com.apple.quarantine", "/Applications/Anime1.app"],
                   sudo: true

    # 重新签名应用（解决跨机器签名不兼容问题）
    system_command "codesign",
                   args: ["--force", "--sign", "-", "--deep", "--options", "runtime", "--timestamp", "/Applications/Anime1.app"],
                   sudo: true
  end

  uninstall quit: "com.anime1.app"

  caveats do
    <<~EOS
      首次运行如遇安全警告:
        1. 右键点击 Anime1.app 选择 "打开"
        2. 或前往 "系统设置" → "隐私与安全性" 点击 "仍要打开"

      DMG 文件中包含 "修复签名" 脚本，可直接双击运行。
    EOS
  end
end
