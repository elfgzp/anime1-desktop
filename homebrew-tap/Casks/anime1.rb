cask "anime1" do
  version "VERSION_PLACEHOLDER"
  sha256 :no_check

  url "https://github.com/elfgzp/anime1-desktop/releases/download/v#{version}/anime1-macos-#{version}.dmg"
  name "Anime1"
  desc "Anime1 Desktop - Anime Browser"
  homepage "https://github.com/elfgzp/anime1-desktop"

  app "Anime1.app"

  zap trash: [
    "~/Library/Application Support/com.anime1.app",
    "~/Library/Preferences/com.anime1.app.plist",
  ]
end
