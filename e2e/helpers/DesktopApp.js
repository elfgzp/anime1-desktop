/**
 * Desktop Application Manager for E2E Testing
 * Handles starting/stopping the desktop application (pywebview-based)
 */
import { spawn, exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs';

const execAsync = promisify(exec);

export class DesktopApp {
  constructor(options = {}) {
    this.options = {
      // Path to the executable or script
      executable: options.executable || this._detectExecutable(),
      // Arguments to pass
      args: options.args || [],
      // Environment variables
      env: { ...process.env, ...options.env },
      // Working directory
      cwd: options.cwd || process.cwd(),
      // Timeout for startup
      startupTimeout: options.startupTimeout || 30000,
      // Timeout for shutdown
      shutdownTimeout: options.shutdownTimeout || 10000,
      // Debug port for CDP connection
      debugPort: options.debugPort || 9222,
      // Flask port
      flaskPort: options.flaskPort || 5172,
      // Whether to use development mode
      devMode: options.devMode ?? true,
    };
    
    this.process = null;
    this.isRunning = false;
    this.cdpWsUrl = null;
  }

  /**
   * Auto-detect executable based on platform
   */
  _detectExecutable() {
    const platform = process.platform;
    const rootDir = path.resolve(process.cwd(), '..');
    
    // Check for built executable first
    if (platform === 'darwin') {
      const macApp = path.join(rootDir, 'dist', 'Anime1.app', 'Contents', 'MacOS', 'Anime1');
      if (fs.existsSync(macApp)) return macApp;
    } else if (platform === 'win32') {
      const winExe = path.join(rootDir, 'dist', 'Anime1.exe');
      if (fs.existsSync(winExe)) return winExe;
    } else {
      const linuxExe = path.join(rootDir, 'dist', 'Anime1');
      if (fs.existsSync(linuxExe)) return linuxExe;
    }
    
    // Fall back to development script
    const devScript = path.join(rootDir, 'Anime1');
    if (fs.existsSync(devScript)) return devScript;
    
    // Fall back to Python module
    return 'python';
  }

  /**
   * Start the desktop application
   */
  async start() {
    if (this.isRunning) {
      console.log('[DesktopApp] Already running');
      return this;
    }

    console.log('[DesktopApp] Starting application...');
    
    const args = [...this.options.args];
    
    // Add development flags
    if (this.options.devMode) {
      args.push('--debug-webview');
    }
    
    // Set environment for CDP debugging
    const env = {
      ...this.options.env,
      WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: `--remote-debugging-port=${this.options.debugPort}`,
      PYWEBVIEW_LOG: 'debug',
    };

    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      
      if (this.options.executable === 'python') {
        args.unshift('-m', 'src.desktop');
      }

      console.log(`[DesktopApp] Spawning: ${this.options.executable} ${args.join(' ')}`);
      
      this.process = spawn(this.options.executable, args, {
        cwd: this.options.cwd,
        env,
        stdio: ['ignore', 'pipe', 'pipe'],
      });

      let stdout = '';
      let stderr = '';

      this.process.stdout.on('data', (data) => {
        const str = data.toString();
        stdout += str;
        console.log(`[App] ${str.trim()}`);
        
        // Check for ready signal
        if (str.includes('Starting webview') || str.includes('t6=')) {
          this.isRunning = true;
          console.log('[DesktopApp] Application started successfully');
          resolve(this);
        }
      });

      this.process.stderr.on('data', (data) => {
        const str = data.toString();
        stderr += str;
        console.error(`[App Error] ${str.trim()}`);
      });

      this.process.on('error', (err) => {
        console.error('[DesktopApp] Failed to start:', err);
        reject(err);
      });

      this.process.on('exit', (code) => {
        this.isRunning = false;
        if (code !== 0 && code !== null) {
          console.error(`[DesktopApp] Process exited with code ${code}`);
        }
      });

      // Timeout handler
      const timeout = setTimeout(() => {
        if (!this.isRunning) {
          this.kill();
          reject(new Error(`Startup timeout after ${this.options.startupTimeout}ms`));
        }
      }, this.options.startupTimeout);

      // Clean up timeout on success
      this.process.stdout.once('data', () => {
        clearTimeout(timeout);
      });
    });
  }

  /**
   * Wait for CDP (Chrome DevTools Protocol) to be available
   */
  async waitForCDP() {
    const maxAttempts = 30;
    const delay = 1000;
    
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const response = await fetch(`http://localhost:${this.options.debugPort}/json/version`);
        if (response.ok) {
          const data = await response.json();
          this.cdpWsUrl = data.webSocketDebuggerUrl;
          console.log('[DesktopApp] CDP ready:', this.cdpWsUrl);
          return this.cdpWsUrl;
        }
      } catch (err) {
        // Not ready yet
      }
      await new Promise(r => setTimeout(r, delay));
    }
    
    throw new Error('CDP not available after timeout');
  }

  /**
   * Get CDP WebSocket URL for Playwright connection
   */
  getCdpWsUrl() {
    return this.cdpWsUrl || `ws://localhost:${this.options.debugPort}/devtools/browser`;
  }

  /**
   * Check if the application is running
   */
  healthCheck() {
    return this.isRunning && this.process && !this.process.killed;
  }

  /**
   * Stop the desktop application
   */
  async stop() {
    if (!this.isRunning || !this.process) {
      console.log('[DesktopApp] Not running');
      return;
    }

    console.log('[DesktopApp] Stopping application...');
    
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        console.log('[DesktopApp] Force killing...');
        this.kill();
        resolve();
      }, this.options.shutdownTimeout);

      this.process.once('exit', () => {
        clearTimeout(timeout);
        this.isRunning = false;
        console.log('[DesktopApp] Stopped');
        resolve();
      });

      // Try graceful shutdown first
      if (process.platform === 'win32') {
        this.process.kill('SIGTERM');
      } else {
        this.process.kill('SIGTERM');
      }
    });
  }

  /**
   * Force kill the process
   */
  kill() {
    if (this.process) {
      this.process.kill('SIGKILL');
      this.isRunning = false;
    }
  }

  /**
   * Take a screenshot using Playwright page
   */
  async screenshot(page, name) {
    const screenshotDir = path.join(process.cwd(), 'screenshots');
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }
    
    const filepath = path.join(screenshotDir, `${name}-${Date.now()}.png`);
    await page.screenshot({ path: filepath, fullPage: true });
    console.log(`[DesktopApp] Screenshot saved: ${filepath}`);
    return filepath;
  }

  /**
   * Get application logs
   */
  getLogs() {
    return {
      stdout: this.process?.stdout?.read?.() || '',
      stderr: this.process?.stderr?.read?.() || '',
    };
  }
}

/**
 * Global app instance for test reuse
 */
let globalApp = null;

export async function getOrStartApp(options = {}) {
  if (!globalApp || !globalApp.healthCheck()) {
    globalApp = new DesktopApp(options);
    await globalApp.start();
    // Wait a bit for the app to be fully ready
    await new Promise(r => setTimeout(r, 3000));
  }
  return globalApp;
}

export async function stopGlobalApp() {
  if (globalApp) {
    await globalApp.stop();
    globalApp = null;
  }
}
