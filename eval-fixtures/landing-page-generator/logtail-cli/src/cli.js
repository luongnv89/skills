#!/usr/bin/env node
'use strict';

const { program } = require('commander');
const { readConfig } = require('./config');
const { sendUsagePing } = require('./telemetry');
const { tail } = require('./tail');
const pkg = require('../package.json');

program
  .name('logtail')
  .description('Tail and filter JSON log output')
  .version(pkg.version)
  .argument('[file]', 'log file to read (reads stdin when omitted)')
  .option('-f, --follow', 'keep reading as the file grows')
  .option('-l, --level <level>', 'minimum level: debug, info, warn, error', 'info')
  .option('-g, --grep <pattern>', 'show only lines whose message matches the pattern')
  .option('--since <duration>', 'show only lines newer than the duration, for example 10m or 2h')
  .option('--json', 'print matching lines as raw JSON')
  .option('--no-color', 'disable colored output')
  .action(async (file, options) => {
    const config = readConfig();
    sendUsagePing({ command: 'tail', options: Object.keys(options), version: pkg.version });
    await tail(file, { ...config, ...options });
  });

program.parse();
