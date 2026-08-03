'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { generate, ADJECTIVES, ANIMALS } = require('../lib/generator');

test('produces a string by default', () => {
  assert.strictEqual(typeof generate(), 'string');
});

test('short format is adjective-animal-number', () => {
  const name = generate({ format: 'short' });
  assert.match(name, /^[a-z]+-[a-z]+-\d{1,2}$/);
});

test('omits number with no-number', () => {
  const name = generate({ number: false });
  assert.match(name, /^[a-z]+-[a-z]+$/);
});

test('returns array when count > 1', () => {
  const names = generate({ count: 3 });
  assert.ok(Array.isArray(names));
  assert.strictEqual(names.length, 3);
});

test('deterministic with a seed', () => {
  const a = generate({ seed: 'abc', count: 5 });
  const b = generate({ seed: 'abc', count: 5 });
  assert.deepStrictEqual(a, b);
});

test('different seeds generally differ', () => {
  const a = generate({ seed: 'release-1' });
  const b = generate({ seed: 'release-2' });
  assert.notStrictEqual(a, b);
});

test('format variants', () => {
  assert.match(generate({ format: 'snake' }), /^[a-z]+_[a-z]+_\d+$/);
  assert.match(generate({ format: 'kebab' }), /^[a-z]+-[a-z]+-\d+$/);
  assert.match(generate({ format: 'camel' }), /^[a-z]+[A-Z][a-z]+\d+$/);
  assert.match(generate({ format: 'plain' }), /^[a-z]+ [a-z]+ \d+$/);
  assert.match(generate({ format: 'title' }), /^[A-Z][a-z]+ [A-Z][a-z]+ \d+$/);
});

test('unknown format throws', () => {
  assert.throws(() => generate({ format: 'nope' }), /Unknown format/);
});

test('validates words come from dictionaries', () => {
  const parts = generate({ number: false, format: 'plain' }).split(' ');
  assert.ok(ADJECTIVES.includes(parts[0]));
  assert.ok(ANIMALS.includes(parts[1]));
});
