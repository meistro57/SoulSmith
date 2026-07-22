import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const typesSource = readFileSync(new URL('../src/types.ts', import.meta.url), 'utf8');
const apiSource = readFileSync(new URL('../src/lib/api.ts', import.meta.url), 'utf8');
const qualitySource = readFileSync(new URL('../src/three/diceQualityProfiles.ts', import.meta.url), 'utf8');
const resonanceSource = readFileSync(new URL('../src/three/resonanceEffects.ts', import.meta.url), 'utf8');
const motionSource = readFileSync(new URL('../src/three/diceMotion.ts', import.meta.url), 'utf8');
const geometrySource = readFileSync(new URL('../src/three/prepareDiceGeometry.ts', import.meta.url), 'utf8');

assert.match(apiSource, /VITE_API_BASE_URL/, 'API client must use VITE_API_BASE_URL');
assert.ok(apiSource.includes(".replace(/\\/$/, '')"), 'API client should trim trailing slash');
assert.match(typesSource, /interface NumericDiceRoll/, 'NumericDiceRoll type should exist');
assert.match(typesSource, /interface CanonicalDiceRead/, 'CanonicalDiceRead type should exist');
assert.match(typesSource, /isNumericDiceRoll/, 'numeric roll guard should exist');
assert.match(typesSource, /d4: 4/, 'd4 validation must cap at four faces');
assert.match(typesSource, /interpretation: DiceInterpretation/, 'canonical read preserves symbolic interpretation');

assert.match(qualitySource, /type DiceQualityMode = 'low' \| 'medium' \| 'high' \| 'auto'/, 'quality profile modes should include auto');
assert.match(qualitySource, /pickAutoQualityMode/, 'auto quality resolver should exist');
assert.match(qualitySource, /maxPixelRatio: 2/, 'high quality should cap pixel ratio at 2');

assert.match(resonanceSource, /interface ResonanceEffect/, 'resonance effect model should exist');
assert.match(resonanceSource, /mapReadToResonance/, 'resonance mapper should exist');
assert.match(resonanceSource, /legendary_pulse/, 'legendary pulse audio hook should exist');

assert.match(motionSource, /beginDieRollMotion/, 'deterministic roll motion starter should exist');
assert.match(motionSource, /updateDieMotion/, 'roll motion update should exist');
assert.match(motionSource, /hashSeed/, 'seeded reproducibility hash should exist in motion pipeline');

assert.match(geometrySource, /toCreasedNormals/, 'geometry prep should use crease-aware normals');
assert.match(geometrySource, /creaseAngleDeg/, 'geometry prep should expose crease angle config');

console.log('Frontend roll contract and renderer logic tests passed.');
