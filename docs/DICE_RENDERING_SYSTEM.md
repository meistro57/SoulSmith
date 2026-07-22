# Dice Rendering System

## Design philosophy

SoulSmith dice are narrative instruments, not decorative RNG tokens. The renderer now treats each die as a tactile mythic object whose visual resonance supports interpretation without replacing it. Effects are brief and secondary, outcome text remains authoritative, and readability is prioritized over spectacle.

## Architecture

Primary implementation lives in `frontend/src/components/DiceRoller3D.tsx`, with rendering modules in `frontend/src/three/`:

- `prepareDiceGeometry.ts`
- `diceMaterials.ts`
- `createDiceEnvironment.ts`
- `createDiceLighting.ts`
- `createDiceShadows.ts`
- `diceQualityProfiles.ts`
- `diceMotion.ts`
- `resonanceEffects.ts`
- `particlePool.ts`
- `disposeSceneResources.ts`

The scene is rebuilt when material or quality settings change, and all WebGL resources are disposed on teardown.

## Geometry and normals

`prepareDiceGeometry` applies a crease-aware normal strategy:

1. center geometry and compute bounds;
2. merge close vertices;
3. scale to a shared target radius;
4. apply `toCreasedNormals` using configurable crease angle;
5. validate normals and recompute if invalid.

Default crease angle is **35°**, configurable in UI from **25° to 45°**. This keeps large faces smooth while preserving major die edges.

## Material modes

`diceMaterials.ts` provides four modes:

- **Polished Resin**: partial transmission, low roughness, clearcoat, tuned attenuation.
- **Crystal / Glass**: high transmission, low roughness, clearcoat, controlled depth behavior.
- **Opaque Gemstone**: no transmission, richer diffuse body, subtle emissive floor.
- **Performance**: simplified `MeshStandardMaterial`, no transmission.

Color picker and opacity controls remain active. Transparent handling avoids aggressive depth artifacts and keeps opaque paths depth-writing.

## Color management and tone mapping

Renderer configuration:

- `renderer.outputColorSpace = THREE.SRGBColorSpace`
- `renderer.toneMapping = THREE.ACESFilmicToneMapping`
- controlled `toneMappingExposure`
- DPR cap from quality profile

## Environment setup

`createDiceEnvironment.ts` builds PMREM from `RoomEnvironment`, so reflections work offline with no remote HDR dependency. Environment texture is bound to `scene.environment` and disposed correctly.

## Lighting rig

`createDiceLighting.ts` creates a restrained studio setup:

- hemisphere fill,
- shadow-casting key directional light,
- lower-intensity fill directional light,
- rim directional light,
- warm bounce point light.

This keeps dark and light dice readable while preserving silhouette definition.

## Shadows and contact

`createDiceShadows.ts` adds:

- a receiving table plane,
- a subtle `ShadowMaterial` contact plane.

Dice cast shadows, the table receives shadows, and directional shadow camera bounds are tuned for usable resolution.

## Numeral readability

Numerals are rendered as die-attached enamel-style sprite badges and remain legible across transparent and opaque modes. Under-die narrative labels are high-contrast canvas sprites and remain camera-facing.

## Motion and settling

`diceMotion.ts` uses deterministic, seeded motion phases:

1. anticipation lift,
2. tumble spin,
3. damped settle,
4. quaternion lock.

Reduced-motion mode shortens phases and damping while preserving outcome mapping.

## Resonance system

`resonanceEffects.ts` defines typed resonance metadata and per-role mapping. Trigger logic in `DiceRoller3D.tsx` applies short-lived emissive pulses and optional particles, then fully fades. Rarity on percentile values controls global pulses. Audio hook events are emitted as browser custom events:

- `roll_start`
- `dice_collision`
- `dice_land`
- `resonance_trigger`
- `legendary_pulse`

## Particles

`particlePool.ts` provides a pooled points-based burst system with no per-frame allocations, automatic decay, and optional disablement in low/reduced modes.

## Quality profiles

`diceQualityProfiles.ts` exposes `low`, `medium`, `high`, and `auto`:

- **Low**: no transmission bloom/fresnel/particles, DPR cap 1.
- **Medium**: physical material with environment and shadows, DPR cap 1.5.
- **High**: transmission + bloom + fresnel + particles, DPR cap 2.
- **Auto**: selects profile from WebGL2, DPR, hardware concurrency, and warm FPS.

## Accessibility

System responds to `prefers-reduced-motion` and explicit reduced-effects toggles:

- shorter roll timeline,
- reduced wobble,
- particles disabled,
- resonance pulses restrained.

Magical effects and post-processing are independently togglable.

## Performance and cleanup

Renderer avoids per-frame material/light recreation. Resource cleanup covers geometries, materials, textures, PMREM targets, particle buffers, composer, event listeners, and animation frame loop.

## Extension points

- Add selective bloom ownership if future effects need isolation.
- Add AO pass if maintaining current readability baseline.
- Add dedicated numeral mesh inlays when STL assets include engraved channels.

## Validation commands

Run from `frontend/`:

- `npm test`
- `npm run typecheck`
- `npm run lint`
- `npm run build`

Backend regression command from `backend/`:

- `pytest`

If backend dependencies are unavailable in the environment, install `backend/requirements-dev.txt` before running `pytest`.

## Manual visual QA checklist

Validate at least these scenarios after any renderer change:

- All seven STL dice load with stable scale.
- Canonical outcome mapping remains unchanged.
- Final lock orientation remains deterministic for the same roll input.
- Numerals remain readable in dark resin, red resin, pale crystal, black gemstone, and transparent glass.
- Contact shadow keeps dice grounded without heavy blotting.
- No severe z-fighting or inverted normals.
- Reduced-motion mode shortens motion and suppresses repeated effects.
- Low and high quality modes both render correctly.
- Repeated rolling does not leak resources or duplicate animation loops.

## Known limitations

- STL numerals are not geometry inlays yet; readability is badge-based.
- Bloom is global and tuned subtle rather than strict selective bloom.
- Auto profile currently uses lightweight heuristics, not long telemetry windows.
