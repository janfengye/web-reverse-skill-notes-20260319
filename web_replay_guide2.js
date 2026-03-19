#!/usr/bin/env node
'use strict';

const https = require('https');

const TARGET_URL = 'https://match.yuanrenxue.cn/match/guide2';

function fetchText(url) {
  return new Promise((resolve, reject) => {
    https
      .get(url, (res) => {
        let data = '';
        res.setEncoding('utf8');
        res.on('data', (chunk) => {
          data += chunk;
        });
        res.on('end', () => {
          if (res.statusCode !== 200) {
            reject(new Error(`Unexpected status code: ${res.statusCode}`));
            return;
          }
          resolve(data);
        });
      })
      .on('error', reject);
  });
}

function extractSign(html) {
  const postMatch = html.match(
    /\$\.ajax\(\{\s*url:\s*['"]\/api\/user['"],\s*method:\s*['"]POST['"],\s*data:\s*\{sign:\s*"([^"]+)"\}/s
  );

  if (!postMatch) {
    throw new Error('Failed to locate POST /api/user sign value');
  }

  return postMatch[1];
}

async function main() {
  console.log(`[*] Fetching ${TARGET_URL}`);
  const html = await fetchText(TARGET_URL);
  const sign = extractSign(html);
  console.log(`[*] POST /api/user sign: ${sign}`);
}

main().catch((error) => {
  console.error('[!] Replay failed:', error.message);
  process.exitCode = 1;
});
