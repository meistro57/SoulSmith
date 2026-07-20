// frontend/scripts/run-tests.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const typesSource = readFileSync(new URL('../src/types.ts', import.meta.url), 'utf8');
const apiSource = readFileSync(new URL('../src/lib/api.ts', import.meta.url), 'utf8');

assert.match(apiSource, /VITE_API_BASE_URL/, 'API client must use VITE_API_BASE_URL');
assert.match(apiSource, /replace\(\/\\\/\$\//, 'API client should trim trailing slash');
assert.match(typesSource, /interface NumericDiceRoll/, 'NumericDiceRoll type should exist');
assert.match(typesSource, /interface CanonicalDiceRead/, 'CanonicalDiceRead type should exist');
assert.match(typesSource, /isNumericDiceRoll/, 'numeric roll guard should exist');
assert.match(typesSource, /d4: 4/, 'd4 validation must cap at four faces');
assert.match(typesSource, /interpretation: DiceInterpretation/, 'canonical read preserves symbolic interpretation');

console.log('Frontend roll contract tests passed.');
