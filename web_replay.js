#!/usr/bin/env node
'use strict';

const https = require('https');
const vm = require('vm');
const { URL } = require('url');

const MATCH_URL = 'https://match.yuanrenxue.cn/match/1';
const API_URL = 'https://match.yuanrenxue.cn/api/question/1';
const DEFAULT_UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36';

function fetchText(url, headers = {}) {
  return new Promise((resolve, reject) => {
    https
      .get(url, { headers }, (res) => {
        let data = '';
        res.setEncoding('utf8');
        res.on('data', (chunk) => {
          data += chunk;
        });
        res.on('end', () => {
          resolve({ status: res.statusCode, body: data, headers: res.headers });
        });
      })
      .on('error', reject);
  });
}

function extractWindowA(html) {
  const match = html.match(/<script>window\.a='([\s\S]*?)';?<\/script>/);
  if (!match) {
    throw new Error('Failed to locate window.a payload');
  }
  return match[1];
}

function decodeBase64String(windowA) {
  let base64 = '';
  for (let i = 0; i < windowA.length; i++) {
    base64 += String.fromCharCode(windowA.charCodeAt(i) - i - 5);
  }
  return base64;
}

function buildM(windowA) {
  const adjustedMs = Date.parse(new Date()) + 100000000;
  const base64 = decodeBase64String(windowA);
  const md5Source = Buffer.from(base64, 'base64')
    .toString('utf8')
    .replace('mwqqppz', JSON.stringify(String(adjustedMs)));

  const ctx = { window: {} };
  vm.createContext(ctx);
  vm.runInContext(md5Source, ctx, { timeout: 5000 });

  return `${ctx.window.f}丨${Math.floor(adjustedMs / 1000)}`;
}

async function fetchPage(windowA, page, cookieHeader) {
  const url = new URL(API_URL);
  url.searchParams.set('page', String(page));
  url.searchParams.set('pageSize', '10');
  url.searchParams.set('kw', '');
  url.searchParams.set('m', buildM(windowA));

  const headers = {
    Accept: 'application/json, text/javascript, */*; q=0.01',
    Referer: MATCH_URL,
    'User-Agent': page === 5 ? 'yuanrenxue' : DEFAULT_UA,
    'X-Requested-With': 'XMLHttpRequest',
  };

  if (cookieHeader) {
    headers.Cookie = cookieHeader;
  }

  const response = await fetchText(url.toString(), headers);
  if (response.status !== 200) {
    throw new Error(`Unexpected status ${response.status} for page ${page}: ${response.body}`);
  }

  const parsed = JSON.parse(response.body);
  return parsed.data || [];
}

async function main() {
  const cookieHeader = process.env.COOKIE || '';
  const matchPage = await fetchText(MATCH_URL);
  if (matchPage.status !== 200) {
    throw new Error(`Failed to fetch match page: ${matchPage.status}`);
  }

  const windowA = extractWindowA(matchPage.body);
  let total = 0;

  for (let page = 1; page <= 5; page++) {
    const data = await fetchPage(windowA, page, cookieHeader);
    const pageSum = data.reduce((sum, value) => sum + value, 0);
    total += pageSum;
    console.log(`page ${page}: ${pageSum} -> [${data.join(', ')}]`);
  }

  console.log(`total: ${total}`);
}

main().catch((error) => {
  console.error('[!] Replay failed:', error.message);
  process.exitCode = 1;
});
