# PigPen avatar assets — version 1

Original SVG adaptation of the existing PigPen animation mascot: pink skin, dark rose outlines, separate eyebrows, closed-mouth smile, coin slot, seated body and curly tail. These static vector assets are a new rendition, not extracted animation frames.

## Confirmed scope

The user requested independently interchangeable hats, bandana colors (including no bandana), glasses, optional eyelashes, and flat background colors. Each accessory can be selected independently. No application routes, profile persistence, backend API, or dependencies were added.

## Included palette and styles

The particular styles and colors below are initial artwork choices, not fixed product requirements.

- Hats: baseball cap, beanie, bucket hat, party hat, crown, beret, or none.
- Bandanas: grass, teal, blue, purple, coral, gold, rose, charcoal, or none.
- Glasses: round, square, sunglasses, cat-eye, monocle, or none.
- Eyelashes: classic lashes or none, independently selectable.
- Backgrounds: cream, sage, sky, lilac, peach, rose, butter, slate.

29 independent SVG assets provide 8 × 7 × 9 × 6 × 2 = **6,048 combinations**. Accessory and base SVGs have transparent backgrounds. Background SVGs fill the square with one solid color.

## Preview

Open `preview.html` in a browser. It is a standalone asset review tool, with embedded SVGs, keyboard-operable option buttons, and a Download SVG button. It does not fetch data or require a server. `contact-sheet.png` and `contact-sheet.svg` show eight representative combinations. Selections are temporary and reset on reload.

## Local asset contract

`manifest.json` describes this asset pack, **not a frontend/backend JSON API contract**. All paths are relative to this directory. `version` is the asset version; `viewBox` is `[0, 0, 512, 512]`; `groups` lists valid option IDs, labels, files, and optional palette colors. The base is always present.

Composite in exactly this back-to-front order:

1. background
2. base
3. bandana
4. eyelashes
5. glasses
6. hat

Every SVG has the same 512 × 512 canvas and origin. Stack them at identical dimensions without trimming, independent scaling, repositioning, or additional margins. `file: null` means omit that layer; `none` is an explicit choice, not an error. Hats intentionally cover the coin slot. Eyelashes sit behind glasses; opaque sunglasses naturally hide them. Missing `eyelashes` in an older selection should default to `none`. The bandana is removable without exposing a hole or a baked-in duplicate. The set is static; these layers are not aligned to the animation sprite frames.

Proposed selection representation for later application integration:

```json
{
  "assetVersion": 1,
  "background": "cream",
  "hat": "none",
  "bandana": "grass",
  "glasses": "none",
  "eyelashes": "none"
}
```

Resolve only option IDs listed in the manifest. Do not interpret arbitrary profile strings as paths or SVG markup. Present one accessible description for the composite and mark stacked image layers decorative. Example: “Pig wearing a beanie, coral bandana, and square glasses on sky blue.”

TODO before profile integration: document and approve the actual JSON API contract, choose persistence/migration behavior and fallback for unavailable versions, and implement the Vue presentation separately from request code. Animation attachment and cross-device UI verification remain future work.

## Rebuild

From the project root:

```sh
python tools/build_avatar_assets.py
rsvg-convert assets/avatars/pig-v1/contact-sheet.svg -o assets/avatars/pig-v1/contact-sheet.png
```

The generator uses the Python standard library only. PNG contact-sheet rendering uses the already-installed `rsvg-convert` executable. Neither command installs dependencies. Edit the generator for artwork changes so SVGs, manifest, contact sheet, and the embedded preview remain consistent.

## Verification

All 29 SVG layers were parsed as XML and checked for the shared canvas. All manifest IDs and file references were checked, and all 6,048 option combinations were structurally composed and parsed. The contact sheet was rendered and visually reviewed for placement, occlusion, and the no-accessories state. Browser automation could not launch in the current environment, so interactive controls, download behavior, and cross-browser rendering have not been runtime-verified.
