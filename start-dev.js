#!/usr/bin/env node

const { spawn } = require('child_process')
const fs = require('fs')
const path = require('path')

const rootDir = __dirname
const serviceDir = path.join(rootDir, 'service')
const appDir = path.join(rootDir, 'app')

if (!fs.existsSync(serviceDir) || !fs.existsSync(appDir)) {
  console.error('项目目录不完整：需要同时存在 service 和 app 目录。')
  process.exit(1)
}

const isWin = process.platform === 'win32'
const npmCmd = isWin ? 'npm.cmd' : 'npm'

const winPython = path.join(serviceDir, '.venv', 'Scripts', 'python.exe')
const unixPython = path.join(serviceDir, '.venv', 'bin', 'python')

let backendCmd
if (fs.existsSync(winPython)) {
  backendCmd = `"${winPython}" -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload`
} else if (fs.existsSync(unixPython)) {
  backendCmd = `"${unixPython}" -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload`
} else {
  backendCmd = 'python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload'
}

const frontendCmd = `${npmCmd} run dev -- --port 5173 --strictPort`

console.log('启动中...')
console.log(`后端目录: ${serviceDir}`)
console.log(`前端目录: ${appDir}`)
console.log('后端地址: http://localhost:8002')
console.log('前端地址: http://localhost:5173')

const backend = spawn(backendCmd, {
  cwd: serviceDir,
  stdio: 'inherit',
  shell: true
})

const frontend = spawn(frontendCmd, {
  cwd: appDir,
  stdio: 'inherit',
  shell: true
})

let shuttingDown = false

function killProcessTree(child) {
  if (!child || child.killed || child.exitCode !== null) return
  if (isWin) {
    spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { stdio: 'ignore' })
  } else {
    child.kill('SIGTERM')
  }
}

function shutdown(reason) {
  if (shuttingDown) return
  shuttingDown = true
  console.log(`\n正在停止服务 (${reason})...`)
  killProcessTree(backend)
  killProcessTree(frontend)
  setTimeout(() => process.exit(0), 300)
}

process.on('SIGINT', () => shutdown('SIGINT'))
process.on('SIGTERM', () => shutdown('SIGTERM'))

backend.on('exit', (code) => {
  if (!shuttingDown) {
    console.log(`后端已退出 (code=${code ?? 'null'})，即将停止前端...`)
    shutdown('backend-exit')
  }
})

frontend.on('exit', (code) => {
  if (!shuttingDown) {
    console.log(`前端已退出 (code=${code ?? 'null'})，即将停止后端...`)
    shutdown('frontend-exit')
  }
})
