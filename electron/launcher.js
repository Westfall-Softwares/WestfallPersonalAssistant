#!/usr/bin/env node

/**
 * Westfall Assistant - Zero-Dependency Launcher
 * 
 * This launcher automatically installs dependencies and starts the application
 * so users don't need to manually install anything.
 */

const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

console.log('🚀 Starting Westfall Assistant...');
console.log('');

// Check if this is the first run
const firstRunMarker = path.join(__dirname, '.first-run-complete');
const isFirstRun = !fs.existsSync(firstRunMarker);

if (isFirstRun) {
  console.log('📦 First-time setup: Installing dependencies automatically...');
  console.log('This will only happen once.');
  console.log('');
  
  // Install dependencies automatically
  installDependencies()
    .then(() => {
      // Mark first run as complete
      fs.writeFileSync(firstRunMarker, new Date().toISOString());
      console.log('✅ Setup complete! Starting application...');
      console.log('');
      startApplication();
    })
    .catch((error) => {
      console.error('❌ Setup failed:', error.message);
      console.log('');
      console.log('Please ensure you have Node.js 16+ and Python 3.8+ installed.');
      process.exit(1);
    });
} else {
  console.log('✅ Dependencies already installed. Starting application...');
  startApplication();
}

async function installDependencies() {
  return new Promise((resolve, reject) => {
    console.log('  Installing Node.js dependencies...');
    
    const npmInstall = spawn('npm', ['install'], {
      stdio: ['inherit', 'pipe', 'pipe'],
      cwd: __dirname
    });
    
    npmInstall.stdout.on('data', (data) => {
      // Show minimal output to avoid overwhelming user
      if (data.toString().includes('added') || data.toString().includes('audited')) {
        process.stdout.write('.');
      }
    });
    
    npmInstall.stderr.on('data', (data) => {
      // Only show actual errors, not warnings
      if (!data.toString().includes('warn')) {
        console.error(data.toString());
      }
    });
    
    npmInstall.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`npm install failed with code ${code}`));
        return;
      }
      
      console.log(' ✓');
      console.log('  Installing Python dependencies...');
      
      const pipInstall = spawn('pip', ['install', '-r', 'backend/requirements.txt'], {
        stdio: ['inherit', 'pipe', 'pipe'],
        cwd: __dirname
      });
      
      pipInstall.stdout.on('data', (data) => {
        // Show progress dots
        if (data.toString().includes('Installing') || data.toString().includes('Successfully')) {
          process.stdout.write('.');
        }
      });
      
      pipInstall.stderr.on('data', (data) => {
        // Only show actual errors
        if (!data.toString().includes('warn') && !data.toString().includes('deprecated')) {
          console.error(data.toString());
        }
      });
      
      pipInstall.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`pip install failed with code ${code}`));
          return;
        }
        
        console.log(' ✓');
        console.log('  Building React frontend...');
        
        const buildReact = spawn('npm', ['run', 'build-react'], {
          stdio: ['inherit', 'pipe', 'pipe'],
          cwd: __dirname
        });
        
        buildReact.stdout.on('data', (data) => {
          if (data.toString().includes('Compiled') || data.toString().includes('build folder')) {
            process.stdout.write('.');
          }
        });
        
        buildReact.on('close', (code) => {
          if (code !== 0) {
            reject(new Error(`React build failed with code ${code}`));
            return;
          }
          
          console.log(' ✓');
          resolve();
        });
      });
    });
  });
}

function startApplication() {
  console.log('🎯 Launching Westfall Assistant...');
  console.log('');
  
  // Start the application
  const app = spawn('npm', ['run', 'dev'], {
    stdio: 'inherit',
    cwd: __dirname
  });
  
  app.on('close', (code) => {
    console.log(`Application exited with code ${code}`);
  });
  
  // Handle Ctrl+C gracefully
  process.on('SIGINT', () => {
    console.log('\n👋 Shutting down Westfall Assistant - Entrepreneur Edition...');
    app.kill();
    process.exit(0);
  });
}