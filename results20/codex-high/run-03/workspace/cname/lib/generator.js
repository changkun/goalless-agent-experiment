'use strict';

const ADJECTIVES = [
  'amber', 'brave', 'calm', 'daring', 'eager', 'fierce', 'golden', 'happy',
  'icy', 'jolly', 'kind', 'lively', 'mighty', 'noble', 'orange', 'proud',
  'quick', 'rosy', 'silent', 'bright', 'timid', 'upbeat', 'vivid', 'witty',
  'wild', 'zesty', 'rapid', 'steady',
];

const ANIMALS = [
  'alpaca', 'badger', 'camel', 'dolphin', 'eagle', 'falcon', 'gecko', 'heron',
  'ibis', 'jaguar', 'koala', 'lemur', 'marmot', 'narwhal', 'ocelot', 'panda',
  'quokka', 'raccoon', 'salamander', 'tiger', 'urchin', 'viper', 'walrus',
  'yak', 'zebra', 'otter', 'lynx', 'bison',
];

function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

function pickFrom(seed) {
  const n = seed.length;
  const seen = new Set();
  const out = [];
  for (let i = 0; i < n; i++) {
    const idx = hashCode(seed) % n;
    if (seen.has(idx)) {
      for (let j = 0; j < n; j++) {
        if (!seen.has(j)) {
          out.push(j);
          seen.add(j);
          break;
        }
      }
    } else {
      out.push(idx);
      seen.add(idx);
    }
    seed = seed + i;
  }
  return out;
}

function formatName(parts, separator) {
  return parts.join(separator);
}

function camelCase(parts) {
  return parts
    .map((p, i) => (i === 0 ? p : p.charAt(0).toUpperCase() + p.slice(1)))
    .join('');
}

function snakeCase(parts) {
  return parts.join('_');
}

function kebabCase(parts) {
  return parts.join('-');
}

function titleCase(parts) {
  return parts.map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(' ');
}

const FORMATTERS = {
  short: (p) => formatName(p, '-'),
  camel: camelCase,
  snake: snakeCase,
  kebab: kebabCase,
  title: titleCase,
  plain: (p) => formatName(p, ' '),
};

/**
 * Generate a memorable codename.
 * @param {object} [opts]
 * @param {string} [opts.format='short'] one of 'short'|'camel'|'snake'|'kebab'|'title'|'plain'
 * @param {number} [opts.count=1] number of names to generate
 * @param {boolean} [opts.number=true] append a numeric suffix
 * @param {string} [opts.seed] optional deterministic seed
 */
function generate(opts = {}) {
  const format = opts.format || 'short';
  const count = opts.count == null ? 1 : Math.max(1, Math.floor(opts.count));
  const withNumber = opts.number !== false;
  const seed = opts.seed || Date.now().toString(36) + Math.random().toString(36).slice(2);

  const formatter = FORMATTERS[format];
  if (!formatter) {
    throw new Error(
      `Unknown format "${format}". Expected one of: ${Object.keys(FORMATTERS).join(', ')}`
    );
  }

  const adjOrder = pickFrom(seed);
  const animalOrder = pickFrom(seed + ':animal');

  const names = [];
  for (let i = 0; i < count; i++) {
    const adj = ADJECTIVES[adjOrder[(i + i) % adjOrder.length]];
    const animal = ANIMALS[animalOrder[(i + adjOrder[i % adjOrder.length]) % animalOrder.length]];
    const parts = [adj, animal];
    if (withNumber) {
      parts.push(String((seed.length + i * 7 + adjOrder[i % adjOrder.length]) % 100));
    }
    names.push(formatter(parts));
  }
  return count === 1 ? names[0] : names;
}

module.exports = { generate, FORMATTERS, ADJECTIVES, ANIMALS };
