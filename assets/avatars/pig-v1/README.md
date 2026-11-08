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

Profile portrait update, November 7, 2026: square glasses now use black frames (`#222222`). The application keeps all artwork layers aligned and crops their shared canvas to `[48, 24, 416, 416]` inside the circular avatar; the background still fills the circle. This closer framing includes the full head and bandana with upper body below. Source assets retain their original 512 × 512 alignment for the standalone preview and other artwork uses.

Additional portrait zoom, November 7: enlarged the foreground another 10% about the existing portrait center (256, 232). The resulting shared viewport is approximately `[66.9091,42.9091,378.1818,378.1818]`. Background and glasses color are unchanged.

Eyewear expansion, November 7, 2026: added rounded/wayfarer (inspired by the supplied rounded tortoiseshell reference), aviator and browline shapes. All eight shapes offer black, tortoiseshell, brown, gold, rose, blue, teal and purple, plus their original color. Existing option IDs/artwork remain compatible. The application exposes separate shape/color selectors while storing the same single glasses ID. There are now 96 SVG layers and 73,584 combinations, extending the historical counts above. Tortoiseshell uses an amber/brown/dark SVG pattern with transparent lenses. The contact sheet includes the reference-inspired option; the standalone preview lists complete shape/color combinations.
