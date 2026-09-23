/*! 极简静态文件服务器（无依赖）—— 仅用于手机访问/本地预览
 * 用法：node serve.js [端口] [目录]
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');

const port = Number(process.argv[2] || 8099);
const rootDir = path.resolve(process.argv[3] || __dirname);
const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.csv': 'text/csv; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8',
};

function lanIPs() {
  const out = [];
  const nets = os.networkInterfaces();
  Object.keys(nets).forEach((name) => {
    (nets[name] || []).forEach((n) => {
      if (n.family === 'IPv4' && !n.internal) out.push(n.address);
    });
  });
  return out;
}

http.createServer((req, res) => {
  const urlPath = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(rootDir, urlPath === '/' ? 'index.html' : urlPath);
  if (!file.startsWith(rootDir)) { res.writeHead(403).end('forbidden'); return; }
  fs.stat(file, (err, st) => {
    if (err || st.isDirectory()) {
      file = path.join(rootDir, 'index.html');
    }
    fs.readFile(file, (e2, buf) => {
      if (e2) { res.writeHead(404).end('not found'); return; }
      res.writeHead(200, {
        'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream',
        'Cache-Control': 'no-store',
      });
      res.end(buf);
    });
  });
}).listen(port, () => {
  console.log('魔方计时器（手机版）已启动');
  console.log('  本机:   http://localhost:' + port + '/');
  lanIPs().forEach((ip) => console.log('  手机:   http://' + ip + ':' + port + '/   （同一 Wi-Fi 下用 Safari 打开）'));
  console.log('  停止:   Ctrl+C');
});
