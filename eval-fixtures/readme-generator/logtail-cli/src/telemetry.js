'use strict';

const https = require('https');
const os = require('os');

const ENDPOINT = 'https://telemetry.logtail.example/v1/events';

// Anonymous usage ping: the option names used, the logtail version, and the OS platform.
// No log content, file paths, or hostnames are sent.
function sendUsagePing(event) {
  if (process.env.LOGTAIL_NO_TELEMETRY === '1') return;
  const body = JSON.stringify({ ...event, platform: os.platform() });
  const req = https.request(ENDPOINT, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
  });
  req.on('error', () => {});
  req.end(body);
}

module.exports = { sendUsagePing };
