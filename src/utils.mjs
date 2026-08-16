import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

const SENSITIVE_QUERY_KEY = /^(?:x-amz-.+|signature|sig|token|auth|authorization|expires?|policy|key(?:id)?|api[_-]?key|access[_-]?token|session(?:id|token)?|credential)$/i;

export function decodeHtmlEntities(value = '') {
  return String(value)
    .replace(/&#x([0-9a-f]+);/gi, (_, hex) => String.fromCodePoint(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec) => String.fromCodePoint(parseInt(dec, 10)))
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&quot;/gi, '"')
    .replace(/&apos;/gi, "'")
    .replace(/&#39;/gi, "'")
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>');
}

export function stripTags(value = '') {
  return decodeHtmlEntities(String(value)
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' '))
    .replace(/\s+/g, ' ')
    .trim();
}

export function sanitizeSegment(name, fallback = 'Sem nome', maxLength = 100) {
  let cleaned = String(name || fallback)
    .replace(/[<>:"/\\|?*\x00-\x1F]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/[. ]+$/g, '');
  if (!cleaned) cleaned = fallback;
  if (/^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)/i.test(cleaned)) cleaned = `_${cleaned}`;
  return cleaned.slice(0, maxLength);
}

function urlHasSensitiveQuery(value) {
  try {
    const u = new URL(value);
    return [...u.searchParams.keys()].some(key => SENSITIVE_QUERY_KEY.test(key));
  } catch {
    return /[?&](?:x-amz-[^=]+|signature|sig|token|auth|authorization|expires?|policy|key(?:id)?|api[_-]?key|access[_-]?token|session(?:id|token)?|credential)=/i.test(String(value));
  }
}

export function redactUrl(value) {
  if (!value) return null;
  try {
    const u = new URL(value);
    return `${u.origin}${u.pathname}${urlHasSensitiveQuery(value) ? '?<sensitive-query-redacted>' : (u.search || '')}`;
  } catch {
    return '<invalid-url>';
  }
}

export function isSensitiveSignedUrl(value) {
  return Boolean(value && urlHasSensitiveQuery(value));
}

export function redactSensitiveText(value = '') {
  return String(value)
    .replace(/https?:\/\/[^\s"'<>]+/gi, url => isSensitiveSignedUrl(url) ? redactUrl(url) : url)
    .replace(/([?&](?:x-amz-[^=]+|signature|sig|token|auth|authorization|expires?|policy|key(?:id)?|api[_-]?key|access[_-]?token|session(?:id|token)?|credential)=)[^&\s]+/gi, '$1<redacted>')
    .replace(/(Authorization\s*[:=]\s*(?:Bearer\s+)?)[^\s,;]+/gi,'$1<redacted>')
    .replace(/(Cookie\s*[:=]\s*)[^\r\n]+/gi,'$1<redacted>');
}

export function sanitizeForPersistence(value, seen = new WeakSet()) {
  if (typeof value === 'string') return redactSensitiveText(value);
  if (value == null || typeof value !== 'object') return value;
  if (seen.has(value)) return '<circular>';
  seen.add(value);
  if (Array.isArray(value)) return value.map(item => sanitizeForPersistence(item, seen));
  const out = {};
  for (const [key, item] of Object.entries(value)) {
    if (/^(?:authorization|proxy-authorization|cookie|set-cookie|x-api-key|api[_-]?key|token|auth|access[_-]?token|refresh[_-]?token|session(?:id|token)?|credential|password|secret)$/i.test(key)) {
      out[key] = '<redacted>';
    } else if (/^(?:videoUrl|mediaUrl)$/i.test(key)) {
      out[key] = typeof item === 'string' ? redactUrl(item) : null;
    } else {
      out[key] = sanitizeForPersistence(item, seen);
    }
  }
  return out;
}

export function truncateWithHash(value, maxLength) {
  const s=String(value||''); if(s.length<=maxLength)return s;
  const hash=crypto.createHash('sha1').update(s).digest('hex').slice(0,8);
  const keep=Math.max(1,maxLength-hash.length-1);
  return `${s.slice(0,keep).replace(/[. ]+$/g,'')}~${hash}`;
}

export function safePersistUrl(value) {
  if (!value) return null;
  try {
    const u=new URL(value);
    if (isSensitiveSignedUrl(value)) return `${u.origin}${u.pathname}`;
    return u.toString();
  } catch { return null; }
}

export function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

export async function atomicWriteJsonDurable(filePath, value) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const temp = `${filePath}.tmp-${process.pid}-${Date.now()}`;
  let handle = null;
  try {
    handle = await fs.open(temp, 'w');
    await handle.writeFile(`${JSON.stringify(value, null, 2)}\n`, 'utf8');
    await handle.sync();
  } finally {
    await handle?.close().catch(()=>{});
  }
  try {
    await fs.rename(temp, filePath);
  } catch (error) {
    if (!['EEXIST','EPERM','ENOTEMPTY'].includes(error?.code)) {
      await fs.rm(temp,{force:true}).catch(()=>{});
      throw error;
    }
    const backup=`${filePath}.replace-${process.pid}-${Date.now()}`;
    let movedOld=false;
    try {
      await fs.rename(filePath,backup); movedOld=true;
      await fs.rename(temp,filePath);
      await fs.rm(backup,{force:true});
    } catch (replaceError) {
      await fs.rm(temp,{force:true}).catch(()=>{});
      if(movedOld){try{await fs.rename(backup,filePath);}catch{}}
      throw replaceError;
    }
  }
  // Best-effort directory fsync on POSIX. Windows does not reliably permit opening directories.
  if (process.platform !== 'win32') {
    let dirHandle=null;
    try {dirHandle=await fs.open(path.dirname(filePath),'r');await dirHandle.sync();} catch {} finally {await dirHandle?.close().catch(()=>{});}
  }
}

export async function atomicWriteJson(filePath, value) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const temp = `${filePath}.tmp-${process.pid}-${Date.now()}`;
  await fs.writeFile(temp, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
  try {
    await fs.rename(temp, filePath);
  } catch (error) {
    // Some Windows filesystems reject replacing an existing destination via rename.
    if (!['EEXIST','EPERM','ENOTEMPTY'].includes(error?.code)) {
      await fs.rm(temp,{force:true}).catch(()=>{});
      throw error;
    }
    const backup=`${filePath}.replace-${process.pid}-${Date.now()}`;
    let movedOld=false;
    try {
      await fs.rename(filePath,backup); movedOld=true;
      await fs.rename(temp,filePath);
      await fs.rm(backup,{force:true});
    } catch (replaceError) {
      await fs.rm(temp,{force:true}).catch(()=>{});
      if(movedOld){
        try{await fs.rename(backup,filePath);}catch{}
      }
      throw replaceError;
    }
  }
}

export async function readJsonIfExists(filePath) {
  try { return JSON.parse(await fs.readFile(filePath, 'utf8')); }
  catch (error) { if (error?.code === 'ENOENT') return null; throw error; }
}

export function nowIso() { return new Date().toISOString(); }
export function unique(values) { return [...new Set(values)]; }
export function safeError(error) {
  return {
    name: error?.name || 'Error',
    code: error?.code || null,
    message: redactSensitiveText(String(error?.message || error)),
  };
}
