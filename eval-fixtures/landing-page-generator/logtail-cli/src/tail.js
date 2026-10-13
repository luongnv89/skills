'use strict';

const fs = require('fs');
const readline = require('readline');

const LEVELS = ['debug', 'info', 'warn', 'error'];
const UNITS = { s: 1000, m: 60000, h: 3600000, d: 86400000 };

function cutoff(since) {
  const match = /^(\d+)([smhd])$/.exec(since || '');
  return match ? Date.now() - Number(match[1]) * UNITS[match[2]] : null;
}

// Reads the file (or stdin), parses each line as JSON, and prints the lines that pass the filters.
async function tail(file, options) {
  const input = file ? fs.createReadStream(file) : process.stdin;
  const minLevel = LEVELS.indexOf(options.level || 'info');
  const since = cutoff(options.since);
  const lines = readline.createInterface({ input });
  for await (const line of lines) {
    let entry;
    try {
      entry = JSON.parse(line);
    } catch {
      continue;
    }
    if (LEVELS.indexOf(entry.level) < minLevel) continue;
    if (since && Date.parse(entry.time) < since) continue;
    if (options.grep && !new RegExp(options.grep).test(entry.msg || '')) continue;
    console.log(options.json ? line : `${entry.level} ${entry.msg}`);
  }
}

module.exports = { tail };
