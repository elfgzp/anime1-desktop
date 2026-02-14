import { FusesPlugin } from '@electron-forge/plugin-fuses';
import { FuseV1Options, FuseVersion } from '@electron/fuses';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get __dirname in ES module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Get app version from package.json
const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8'));

// Environment detection
const isCI = process.env.CI === 'true';
const isTag = process.env.GITHUB_REF?.startsWith('refs/tags/');

// Platform-specific configuration
const platform = process.platform;
const isMac = platform === 'darwin';
const isWin = platform === 'win32';
const isLinux = platform === 'linux';

// Helper to check if icon exists
function iconExists(iconPath) {
  return fs.existsSync(path.resolve(__dirname, iconPath));
}

// Code signing configuration
const macOsSigningConfig = (() => {
  if (!isMac || !process.env.APPLE_ID) {
    return {};
  }
  return {
    osxSign: {
      identity: process.env.MACOS_CERTIFICATE_NAME || 'Developer ID Application',
      'hardened-runtime': true,
      'gatekeeper-assess': false,
      entitlements: 'entitlements.plist',
      'entitlements-inherit': 'entitlements.plist',
      'signature-flags': 'library',
    },
    osxNotarize: {
      tool: 'notarytool',
      appleId: process.env.APPLE_ID,
      appleIdPassword: process.env.APPLE_ID_PASSWORD,
      teamId: process.env.APPLE_TEAM_ID,
    },
  };
})();

const windowsSigningConfig = (() => {
  if (!isWin || !process.env.WINDOWS_PFX_FILE) {
    return {};
  }
  return {
    windowsSign: {
      certificateFile: process.env.WINDOWS_PFX_FILE,
      certificatePassword: process.env.WINDOWS_PFX_PASSWORD,
    },
  };
})();

export default {
  packagerConfig: {
    asar: true,
    name: 'Anime1Desktop',
    executableName: 'anime1-desktop-electron-forge',
    appBundleId: 'com.gzp.anime1-desktop',
    appCategoryType: 'public.app-category.entertainment',
    icon: iconExists('./assets/icon.png') ? './assets/icon' : undefined,
    // macOS specific
    ...(isMac && {
      appBundleId: 'com.gzp.anime1-desktop',
      appCategoryType: 'public.app-category.entertainment',
      extendInfo: {
        CFBundleDisplayName: 'Anime1 Desktop',
        CFBundleExecutableName: 'Anime1 Desktop',
        CFBundleDocumentTypes: [],
      },
      ...(iconExists('./assets/icon.icns') && { icon: './assets/icon.icns' }),
    }),
    // Windows specific
    ...(isWin && {
      ...(iconExists('./assets/icon.ico') && { icon: './assets/icon.ico' }),
      win32metadata: {
        CompanyName: 'gzp',
        FileDescription: 'Anime1 Desktop - Watch anime from anime1.me',
        OriginalFilename: 'Anime1Desktop.exe',
        ProductName: 'Anime1 Desktop',
        InternalName: 'anime1-desktop',
      },
    }),
    // Linux specific
    ...(isLinux && {
      ...(iconExists('./assets/icon.png') && { icon: './assets/icon.png' }),
    }),
    // Code signing
    ...macOsSigningConfig,
    ...windowsSigningConfig,
    // Ignore patterns
    ignore: [
      /^\/(?!package\.json|\.webpack|assets|node_modules)/,
      /^\/\.github/,
      /^\/\.vscode/,
      /^\/test/,
      /^\/tests?/,
      /^\/spec/,
      /^\/docs/,
      /^\/scripts\/.*\.test\./,
      /\.test\.(js|ts)$/,
      /\.spec\.(js|ts)$/,
      /__tests__/,
      /\.git/,
      /\.github/,
      /playwright\.config\./,
      /vitest\.config\./,
      /forge\.config\./,
    ],
  },
  rebuildConfig: {},
  makers: [
    // Windows - Squirrel
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'Anime1Desktop',
        exe: 'Anime1Desktop.exe',
        setupExe: `Anime1Desktop-${packageJson.version}-Setup.exe`,
        ...(iconExists('./assets/icon.ico') && { 
          setupIcon: './assets/icon.ico',
          iconUrl: 'https://raw.githubusercontent.com/gzp/anime1-desktop/main/assets/icon.ico',
        }),
        ...(iconExists('./assets/installer.gif') && { loadingGif: './assets/installer.gif' }),
        // Only create MSI if on Windows
        ...(isWin && {
          noMsi: false,
          msi: `Anime1Desktop-${packageJson.version}.msi`,
        }),
      },
    },
    // macOS - ZIP
    {
      name: '@electron-forge/maker-zip',
      platforms: ['darwin'],
      config: {
        macUpdateManifestBaseUrl: 'https://github.com/gzp/anime1-desktop/releases/download/latest',
      },
    },
    // macOS - DMG (optional, requires additional setup)
    // Uncomment if you want DMG builds
    /*
    {
      name: '@electron-forge/maker-dmg',
      config: {
        icon: './assets/icon.icns',
        background: './assets/dmg-background.png',
        format: 'ULFO',
      },
    },
    */
    // Linux - DEB
    {
      name: '@electron-forge/maker-deb',
      config: {
        options: {
          maintainer: 'gzp',
          homepage: 'https://github.com/gzp/anime1-desktop',
          icon: iconExists('./assets/icon.png') ? './assets/icon.png' : undefined,
          categories: ['AudioVideo', 'Video', 'Network'],
          description: 'Anime1 Desktop - Watch anime from anime1.me',
          productName: 'Anime1 Desktop',
          genericName: 'Anime Player',
          section: 'video',
          priority: 'optional',
          depends: [
            'gconf2',
            'gconf-service',
            'libnotify4',
            'libappindicator1',
            'libxtst6',
            'libnss3',
          ],
        },
      },
    },
    // Linux - RPM
    {
      name: '@electron-forge/maker-rpm',
      config: {
        options: {
          homepage: 'https://github.com/gzp/anime1-desktop',
          icon: iconExists('./assets/icon.png') ? './assets/icon.png' : undefined,
          categories: ['AudioVideo', 'Video', 'Network'],
          description: 'Anime1 Desktop - Watch anime from anime1.me',
          productName: 'Anime1 Desktop',
          genericName: 'Anime Player',
          license: 'MIT',
        },
      },
    },
  ],
  publishers: [
    // GitHub Releases
    {
      name: '@electron-forge/publisher-github',
      config: {
        repository: {
          owner: 'gzp',
          name: 'anime1-desktop',
        },
        prerelease: false,
        draft: false,
        // Generate release notes from commits
        generateReleaseNotes: true,
        // Force publish even if tag exists
        force: false,
      },
    },
  ],
  plugins: [
    {
      name: '@electron-forge/plugin-webpack',
      config: {
        mainConfig: './webpack.main.config.js',
        renderer: {
          config: './webpack.renderer.config.js',
          entryPoints: [
            {
              html: './index.html',
              js: './src/renderer.js',
              name: 'main_window',
              preload: {
                js: './src/preload.js',
              },
            },
          ],
        },
      },
    },
    // Fuses for security hardening
    new FusesPlugin({
      version: FuseVersion.V1,
      [FuseV1Options.RunAsNode]: false,
      [FuseV1Options.EnableCookieEncryption]: true,
      [FuseV1Options.EnableNodeOptionsEnvironmentVariable]: false,
      [FuseV1Options.EnableNodeCliInspectArguments]: false,
      [FuseV1Options.EnableEmbeddedAsarIntegrityValidation]: true,
      [FuseV1Options.OnlyLoadAppFromAsar]: true,
    }),
  ],
  hooks: {
    packageAfterPrune: async (forgeConfig, buildPath, electronVersion, platform, arch) => {
      // Additional cleanup after pruning
      // fs and path are already imported at the top of the file
      
      // Files/directories to remove from node_modules
      const toRemove = [
        '**/*.d.ts',
        '**/*.map',
        '**/docs',
        '**/test',
        '**/tests',
        '**/spec',
        '**/.github',
        '**/.gitignore',
        '**/README.md',
        '**/CHANGELOG.md',
        '**/LICENSE',
        '**/license',
      ];
      
      console.log(`[Hook] Package built for ${platform}-${arch} at ${buildPath}`);
    },
    postMake: async (forgeConfig, makeResults) => {
      // Log created artifacts
      for (const result of makeResults) {
        console.log(`[Hook] Created ${result.artifacts.length} artifacts:`);
        for (const artifact of result.artifacts) {
          console.log(`  - ${artifact}`);
        }
      }
    },
  },
};
