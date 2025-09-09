#!/usr/bin/env node
/**
 * Backend startup script for Electron
 * Locates Python backend binary, picks free port, starts process, polls /health
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

const BACKEND_PORT = 8756;
const HEALTH_CHECK_TIMEOUT = 15000; // 15 seconds
const HEALTH_CHECK_INTERVAL = 1000; // 1 second

/**
 * Find an available port starting from the given port
 */
async function findAvailablePort(startPort = BACKEND_PORT) {
  return new Promise((resolve) => {
    const server = require('net').createServer();
    server.listen(startPort, () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on('error', () => {
      resolve(findAvailablePort(startPort + 1));
    });
  });
}

/**
 * Check if backend is healthy
 */
async function checkHealth(port) {
  return new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${port}/health`, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          resolve(response.status === 'ok');
        } catch (e) {
          resolve(false);
        }
      });
    });
    req.on('error', () => resolve(false));
    req.setTimeout(2000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

/**
 * Start the backend process
 */
async function startBackend() {
  const port = await findAvailablePort(BACKEND_PORT);
  
  // Try to locate Python backend
  const backendPaths = [
    path.join(__dirname, '..', '..', 'backend', 'server.py'),
    path.join(__dirname, '..', '..', 'backend', 'westfall_backend', 'app.py'),
    path.join(__dirname, '..', '..', 'dist-backend', 'westfall-backend'),
    path.join(__dirname, '..', '..', 'dist-backend', 'westfall-backend.exe')
  ];
  
  let backendPath = null;
  for (const testPath of backendPaths) {
    if (fs.existsSync(testPath)) {
      backendPath = testPath;
      break;
    }
  }
  
  if (!backendPath) {
    throw new Error('Backend binary not found');
  }
  
  console.log(`Starting backend at ${backendPath} on port ${port}`);
  
  // Set environment variables
  const env = {
    ...process.env,
    WESTFALL_HOST: '127.0.0.1',
    WESTFALL_PORT: port.toString(),
    PYTHONPATH: path.join(__dirname, '..', '..')
  };
  
  // Start the process
  let backendProcess;
  if (backendPath.endsWith('.py')) {
    backendProcess = spawn('python', [backendPath], { env });
  } else {
    backendProcess = spawn(backendPath, [], { env });
  }
  
  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data.toString().trim()}`);
  });
  
  backendProcess.stderr.on('data', (data) => {
    console.error(`Backend Error: ${data.toString().trim()}`);
  });
  
  // Wait for health check
  const startTime = Date.now();
  while (Date.now() - startTime < HEALTH_CHECK_TIMEOUT) {
    if (await checkHealth(port)) {
      console.log(`Backend ready on port ${port}`);
      return { process: backendProcess, port, url: `http://127.0.0.1:${port}` };
    }
    await new Promise(resolve => setTimeout(resolve, HEALTH_CHECK_INTERVAL));
  }
  
  throw new Error('Backend failed to start within timeout');
}

module.exports = { startBackend, findAvailablePort, checkHealth };

// If run directly
if (require.main === module) {
  startBackend()
    .then(({ port, url }) => {
      console.log(`Backend started successfully at ${url}`);
      process.exit(0);
    })
    .catch((error) => {
      console.error('Failed to start backend:', error.message);
      process.exit(1);
    });
}