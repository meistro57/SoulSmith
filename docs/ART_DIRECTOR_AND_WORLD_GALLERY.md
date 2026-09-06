# Art Director & World Gallery (Phase 15)

> **THE ART DIRECTOR CONTROLS INTERPRETATION. IT DOES NOT CONTROL CANON.**

SoulSmith accumulates a growing body of approved visual history: character
portrait versions, world-entity visual versions, Chronicle Paintings protected by
the Visual Canon Guardian, Group Memories, and a Living Biography. Phase 15 turns
that history into a coherent visual language and an explorable gallery of the
world across time, without letting style, aesthetics, curation, or generated
artwork rewrite historical truth.

---

## Canon vs. art direction boundary

The pipeline is directional:

```
CANON + HISTORICAL VISUAL REFERENCES + ART DIRECTION
    -> GENERATION
    -> VISUAL CANON GUARDIAN
    -> APPROVAL
    -> WORLD GALLERY
```

Never:

```
GALLERY / ART STYLE -> CANON
```

Four responsibilities stay distinct:

1. **Canon** determines *what may be depicted* (immutable roll record, Memory
   Objects, StoryMarks, equipment, historical versions).
2. **The Art Director** determines *how approved canon may be interpreted
   visually* (medium, palette, lighting, atmosphere, material, framing,
   composition, per-artifact treatments, negative guidance).
3. **The Visual Canon Guardian** determines whether a generated interpretation
   is safe and canonical to expose.
4. **Player approval** determines which valid interpretation is preferred.
5. **The Gallery** curates approved artifacts; it never promotes rejected,
   quarantined, blocked, or unreviewed work.

---

## Art Direction Profile / version model

Profiles are persistent and versioned. A profile has a stable `profile_id` and an
immutable sequence of `art_direction_profile_versions`. Updating a profile always
creates a new version; older artwork keeps the instructions it was actually made
with.

A profile version contains only stylistic treatment:

- `medium_style`, `palette_guidance`, `lighting_guidance`, `atmosphere`,
  `texture_material`, `camera_framing`, `composition_guidance`
- per-artifact treatments: `portrait_treatment`, `environment_treatment`,
  `relic_treatment`, `phenomenon_treatment`, `chronicle_treatment`
- `negative_guidance` (style/avoidance, not canon)
- `provider_hints` (workflow/provider suggestions, advisory only)
- `accessibility_notes`
- status `draft` / `current` / `superseded` / `archived`

**No canonical character/world facts live inside a style profile.** A profile
has no field for participants, events, locations, story marks, or other canon.

Storage: `art_direction_profiles` + `art_direction_profile_versions`
(relational, SQLite). See `backend/app/db.py`.

---

## Style hierarchy and inheritance

A small, understandable precedence model:

```
World Art Direction -> artifact-type treatment -> optional scene/collection override
```

- World-level style fields come from the selected profile version.
- The artifact-type treatment refines it (`portrait` -> `portrait_treatment`,
  `location`/`environment` -> `environment_treatment`, `relic` ->
  `relic_treatment`, `phenomenon` -> `phenomenon_treatment`,
  `chronicle_painting` -> `chronicle_treatment`).
- A scene/collection override may change presentation only; it cannot touch
  canonical facts.

Resolution is deterministic and inspectable via `resolve_art_direction` in
`backend/app/art_director.py`.

---

## Art-direction compiler

`compile_art_direction_spec` combines:

- canonical scene/entity specification
- historical visual references
- artifact type
- selected profile/version
- provider capabilities
- composition intent
- accessibility/presentation constraints

and outputs an inspectable `ArtDirectionSpec` plus a provider-facing prompt.
Canonical requirements and stylistic requirements are kept in **separate
fields** (`canonical` vs `style`) so they can never collapse into
indistinguishable prompt prose.

---

## Provider capability awareness

The Art Director reuses `ProviderCapabilitiesModel` (from Phase 12). It knows
whether the selected provider supports text-to-image, single/multiple references,
identity conditioning, regional conditioning, deterministic seeds, aspect-ratio
control, and workflow selection.

`capability_limitations` degrades honestly: e.g. a provider with
`multiple_references=False` does not pretend img2img preserves many identities.
Limitations are surfaced in the spec rather than silently discarding
identity/canon constraints.

---

## Relationship to the Visual Canon Guardian

Art direction does **not** weaken Phase 12. Any newly generated Chronicle
Painting still passes the Visual Canon Guardian before player visibility.
Regeneration/reinterpretation routes through the existing candidate/review/
approval lifecycles (portrait, world visual, Chronicle Painting).

The Guardian validates canon/identity/safety; it must not reject an image merely
because it prefers a different legitimate art style. Style compliance is checked
separately (below) and never confused with canonical validity.

---

## Optional style reviewer

`backend/app/style_reviewer.py` provides a lightweight Art Direction Reviewer
(mock) that answers whether a candidate follows the selected profile, not whether
the depicted event is canonical. Output is `pass`/`retry`, style confidence,
style deviations, and correction instructions.

`final_verdict_after_style_review` enforces precedence: a Guardian `block` or
`retry` always wins, and a style `pass` can never override a Guardian BLOCK. A
visually beautiful image that violates canon still fails.

---

## World Gallery architecture

`backend/app/world_gallery.py` is the consent-safe projection/query service. It
assembles approved artifacts from existing pipelines without duplicating them:

- **portraits** (`portrait_versions`)
- **world visuals** (`visual_entity_versions`)
- **Chronicle Paintings** (`chronicle_paintings` with `status = approved`)
- **shared moments** (approved paintings whose Memory Object belongs to a
  `group_memory` by exact `event_id`)
- **biography illustrations** (biography sections whose provenance links to an
  approved painting or portrait version)

Every read goes through consent/publication filtering. Private participants are
omitted (never counted) from public projections. Captions and alt text derive
only from safe known metadata.

Storage for collections: `gallery_collections` + `gallery_collection_items`.
Collections store references, ordering, captions, and presentation metadata; they
never copy or mutate canonical records.

---

## Gallery modes

- **The World** — approved locations, relics, phenomena, and world visuals.
- **The People** — consent-safe portrait histories.
- **The Chronicle** — approved paintings attached to canonical memories/events.
- **Shared Moments** — consent-safe Group Memory imagery.
- **A Life** — visual journey through a Living Biography.
- **Then & Now** — immutable historical timelines (via `/gallery/timeline`).

Only modes supported by actual data are implemented; empty states are graceful.

---

## Collections / exhibitions

Collections/exhibitions are built from approved artifact references with
ordering, captions, and presentation metadata. Operations:

- create/update/list collections
- add/remove items (references only)
- reorder items (position only; never mutates the referenced source)

System-generated and player-curated collections are supported. Generated
titles/captions are interpretation and must not introduce unsupported facts.

---

## Provenance

Every Gallery artifact exposes provenance: what canonical entity/event/memory it
depicts, historical version/date/context where known, which Art Direction
Profile/version produced it (tracked on candidate/painting rows), generation/
provider metadata where appropriate, and Guardian status where permitted.

Player-facing captions and alt text are human-readable and consent-safe.

---

## Privacy & publication

The Gallery is a publication surface:

- An approved private visual is **not** automatically approved for public
  exposure.
- Participant-specific consent (`visual_consent_settings`) and existing
  public-canon/publication states are respected for portraits, shared memories,
  Chronicle Paintings, biography illustrations, captions, and provenance.
- A public collection must not leak a private participant indirectly through
  image metadata, title, caption, tags, provenance, counts, alt text, or source
  links.

---

## Accessibility

- Meaningful alt text derived only from safe known metadata (`conservative_alt_text`).
- Keyboard navigation (buttons with visible focus states).
- Reduced-motion handling (`motion-reduce`).
- Responsive layouts; no essential information encoded only by color.

Alt text never invents visual/canonical details. When automated description is
unavailable/untrusted, alt text is derived conservatively from artifact metadata.

---

## Performance strategy

- Lazy-loaded images (`loading="lazy"`).
- Thumbnails/preview via existing SoulSmith-owned assets; full-resolution images
  are not fetched for every card.
- Incremental/paginated-ready query shape.
- Cache-safe immutable asset references (`/assets/...` URLs).
- Graceful missing-asset handling.

No large new image-processing dependency is introduced.

---

## Known v1 limitations

- Text/vision modules remain deterministic mocks; the Art Direction Reviewer and
  Gallery are deterministic and require no GPU or external provider.
- Multi-identity image conditioning remains out of scope for the v1 providers;
  the Art Director degrades honestly rather than pretending many faces can be
  preserved.
- The Gallery is query-driven (mode + optional entity filters), not a full
  database-filter taxonomy; pagination is a follow-up.
- Profile selection is optional on candidate/painting creation; legacy artifacts
  simply carry no `art_direction_profile_*` provenance.

---

## APIs

REST (under `/api/v1/`):

- `POST /art-direction/profiles` — create profile + first version
- `GET /art-direction/profiles` — list profiles
- `GET /art-direction/profiles/{profile_id}` — profile + versions
- `POST /art-direction/profiles/{profile_id}/versions` — append a new version
- `POST /art-direction/profiles/{profile_id}/status?status_value=...` — set status
- `GET /art-direction/current` — resolve current profile
- `POST /art-direction/resolve` — resolve a profile version for an artifact type
- `POST /art-direction/preview` — compile an inspectable Art Direction Spec
- `POST /art-direction/review` — run the optional style reviewer
- `GET /gallery?mode=...` — browse consent-safe Gallery artifacts
- `GET /gallery/timeline?entity_type=...&entity_id=...` — historical visual timeline
- `POST/GET/PATCH /gallery/collections` — collection CRUD
- `POST/DELETE /gallery/collections/{id}/items` — add/remove item references
- `POST /gallery/collections/{id}/reorder` — reorder items

Profile selection integrates with existing candidate creation endpoints via an
optional `art_direction_profile_version_id` on `CreatePortraitCandidateRequest`,
`CreateWorldVisualCandidateRequest`, and `CreateChroniclePaintingRequest`.

---

## Tests

- `backend/tests/test_art_director.py`
- `backend/tests/test_world_gallery.py`

Coverage includes profile creation/versioning, immutability, deterministic
resolution and spec compilation, provider capability degradation, Guardian
precedence over style approval, consent-safe Gallery projection, exclusion of
rejected/quarantined/blocked candidates, private-portrait non-leakage, collection
reference-without-mutation, reorder-without-canon-change, immutable timelines,
conservative alt text, and biography-illustration surfacing.
