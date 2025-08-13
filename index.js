const http = require('http');
const url = require('url');

const START_CAPITAL = 10000;
let transactions = [];
let portfolio = [];

function sendJSON(res, status, data) {
  res.writeHead(status, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*'
  });
  res.end(JSON.stringify(data));
}

const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    });
    res.end();
    return;
  }

  if (req.method === 'GET' && parsedUrl.pathname === '/transactions') {
    return sendJSON(res, 200, transactions);
  }

  if (req.method === 'POST' && parsedUrl.pathname === '/transactions') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const data = JSON.parse(body || '{}');
        data.date = new Date().toISOString();
        transactions.push(data);
        sendJSON(res, 201, {status: 'ok'});
      } catch (e) {
        sendJSON(res, 400, {error: 'invalid json'});
      }
    });
    return;
  }

  if (req.method === 'POST' && parsedUrl.pathname === '/portfolio/buy') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const data = JSON.parse(body || '{}');
        portfolio.push(data);
        sendJSON(res, 201, {status: 'ok'});
      } catch (e) {
        sendJSON(res, 400, {error: 'invalid json'});
      }
    });
    return;
  }

  if (req.method === 'GET' && parsedUrl.pathname === '/portfolio/value') {
    let cost = 0;
    let currentValue = 0;
    portfolio.forEach(p => {
      cost += p.shares * p.price;
      const currentPrice = p.price * 1.1; // mock 10% gain
      currentValue += p.shares * currentPrice;
    });
    const totalValue = START_CAPITAL - cost + currentValue;
    const profit = totalValue - START_CAPITAL;
    return sendJSON(res, 200, { totalValue, profit });
  }

  sendJSON(res, 404, {error: 'not found'});
});

const PORT = 3001;
server.listen(PORT, () => {
  console.log(`Mock server running on port ${PORT}`);
});
