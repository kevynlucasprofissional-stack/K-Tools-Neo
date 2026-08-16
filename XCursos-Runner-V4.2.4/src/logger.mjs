import fs from 'node:fs/promises';
import path from 'node:path';
import { redactSensitiveText, sanitizeForPersistence } from './utils.mjs';

function safePart(value) {
  if (typeof value !== 'string') return value;
  return redactSensitiveText(value);
}

export class RunnerLogger {
  constructor({ logFile = null, sink = null } = {}) { this.logFile = logFile; this.sink = sink; }
  async log(scope, message, data = null) {
    const safeData=data==null?null:sanitizeForPersistence(data);
    const suffix = safeData ? ` ${JSON.stringify(safeData)}` : '';
    const line = `[${new Date().toISOString()}][${scope}] ${safePart(message)}${suffix}`;
    if (this.sink) this.sink(line);
    if (this.logFile) {
      await fs.mkdir(path.dirname(this.logFile), { recursive: true });
      await fs.appendFile(this.logFile, `${line}\n`, 'utf8');
    }
    return line;
  }
}
