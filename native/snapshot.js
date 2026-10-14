/** Bounded, version-5 snapshots compatible with the original Python validator. */
export const copy = value => structuredClone(value);
export const assert = (condition, message = 'The saved progress could not be restored safely.') => { if (!condition) throw new Error(message); };
export const integer = (value, low, high) => Number.isInteger(value) && value >= low && value <= high;
export const exactKeys = (value, keys) => value !== null && !Array.isArray(value) && typeof value === 'object' && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
export function canonicalJSON(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJSON).join(',')}]`;
  if (value !== null && typeof value === 'object') return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonicalJSON(value[key])}`).join(',')}}`;
  return JSON.stringify(value);
}
export function parseJSON(text) {
  // Every numeric value in the original schema must be a JSON integer. Reject
  // duplicate fields before JS JSON parsing can silently discard one.
  let position = 0;
  const whitespace = () => { while (/[ \t\r\n]/.test(text[position] || '') && position < text.length) position++; };
  function string() {
    const start = position++;
    while (position < text.length) {
      const character = text[position++];
      if (character === '\\') position++;
      else if (character === '"') return JSON.parse(text.slice(start, position));
    }
    throw new Error('Invalid JSON string.');
  }
  function value(depth = 0) {
    assert(depth <= 32); whitespace();
    const character = text[position];
    if (character === '"') return string();
    if (character === '{') {
      position++; whitespace(); const object = {}, seen = new Set();
      if (text[position] === '}') { position++; return object; }
      while (true) {
        whitespace(); assert(text[position] === '"'); const key = string(); assert(!seen.has(key)); seen.add(key);
        whitespace(); assert(text[position++] === ':');
        Object.defineProperty(object, key, {value: value(depth + 1), enumerable: true, writable: true, configurable: true});
        whitespace(); const end = text[position++]; if (end === '}') return object; assert(end === ',');
      }
    }
    if (character === '[') {
      position++; whitespace(); const array = [];
      if (text[position] === ']') { position++; return array; }
      while (true) { array.push(value(depth + 1)); whitespace(); const end = text[position++]; if (end === ']') return array; assert(end === ','); }
    }
    for (const [word, result] of [['true',true],['false',false],['null',null]]) {
      if (text.slice(position, position + word.length) === word) { position += word.length; return result; }
    }
    const match = text.slice(position).match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/);
    assert(match && /^-?\d+$/.test(match[0])); position += match[0].length;
    const number = Number(match[0]); assert(Number.isSafeInteger(number)); return number;
  }
  const result = value(); whitespace(); assert(position === text.length); return result;
}
export function base64url(bytes) {
  return btoa(Array.from(bytes, byte => String.fromCharCode(byte)).join('')).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/g,'');
}
export function from64(token, max = 6000) {
  assert(typeof token === 'string' && token.length >= 1 && token.length <= max && /^[A-Za-z0-9_-]+$/.test(token));
  return Uint8Array.from(atob(token.replace(/-/g,'+').replace(/_/g,'/') + '='.repeat((4 - token.length % 4) % 4)), c => c.charCodeAt(0));
}
async function transform(bytes, stream, limit) {
  const reader = new Blob([bytes]).stream().pipeThrough(stream).getReader();
  let length = 0; const chunks = [];
  try {
    while (true) {
      const {done, value} = await reader.read(); if (done) break;
      length += value.length; assert(length <= limit); chunks.push(value);
    }
  } catch (error) { await reader.cancel().catch(() => {}); throw error; }
  const result = new Uint8Array(length); let offset = 0;
  for (const chunk of chunks) { result.set(chunk, offset); offset += chunk.length; }
  return result;
}
export async function compress(state) {
  const bytes = new TextEncoder().encode(canonicalJSON(state)); assert(bytes.length <= 16000);
  const token = base64url(await transform(bytes, new CompressionStream('deflate'), 6000)); assert(token.length <= 6000); return token;
}
export async function decompress(token) {
  const bytes = await transform(from64(token), new DecompressionStream('deflate'), 16000);
  return parseJSON(new TextDecoder('utf-8', {fatal:true}).decode(bytes));
}
export function readDraft(token) {
  if (!token) return null;
  try {
    const raw = new TextDecoder('utf-8', {fatal:true}).decode(from64(token,128));
    assert(raw.length <= 64 && /^[0-9eE+\-.\s]*$/.test(raw)); return raw;
  } catch { return null; }
}
export const draftToken = raw => base64url(new TextEncoder().encode(raw));
