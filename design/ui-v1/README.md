# PigPen UI direction 01

Static design studies, November 6, 2026. Open `index.html` to review the five desktop/mobile pairs and separate notification-list examples. Click a main screen to open its full-resolution PNG. `overview.png` provides a contact sheet; every screen also has an editable SVG source.

The user accepted this visual direction on November 6, 2026. It is indexed in [the project UI design reference](../../docs/ui-design.md). Acceptance covers the visual direction; illustrative content and provisional behavior remain distinguished below.

## Confirmed for this design pass

- Static mockups to establish visual direction.
- User-supplied Gusto screenshot as a visual reference: generous space, serif headings, clear navigation, and simple bordered cards. Its content is reference material, not PigPen functionality or instructions.
- Very light pink background, light pink and deeper pink accents, soft edges, and earthy pastels.
- Desktop and mobile designs, with tablet adaptation to be worked out during responsive implementation.
- Five equally prominent destinations: Dashboard, Purchases, Budget, Wish lists, and Approvals. Notifications open as a separate list from the corner bell.
- Dashboard direction accepted: monthly budget summary, personal allowance, approvals needing attention, recent purchases, and an Add purchase action.
- Budget remains within documented functionality; no new budgeting features are introduced.
- One household wish list filtered by owner.
- Assume all eligible household members must approve for now. The requester remains ineligible to self-approve, as already documented. This supersedes the architecture/functionality proposal that one other reviewer is sufficient for the mockup pass; it remains a provisional rule for implementation. The pictured two-profile household requires one other approval.

## Design choices and illustrative content

These artwork choices are reviewable proposals, not new product requirements:

- Desktop canvas: 1440 × 1040. Mobile canvas: 390 × 1040; this is a long static presentation canvas, not a required phone size.
- Warm blush `#fff8f7`, light pink `#f6dce4`, rose `#a94665`, sage `#e6eddf`, clay `#f2dfd2`, and butter `#f5edcd`.
- Liberation Serif headings and DejaVu Sans body text, using fonts already installed locally.
- Existing PigPen avatar base artwork reused from `assets/avatars/pig-v1/base/pig.svg` and embedded in the SVG files.
- Sample profiles Alex and Jamie; sample November 2026 figures in USD. Currency/timezone defaults are still subject to the existing documentation's open decisions.
- Sample category allocations total $3,180; recorded spending totals $2,360; remaining allocation is $820. Savings allocation and movements are zero in this sample. Personal subcategory spending is included once.
- Purchase lists show a subset of sample transactions. Pending coffee purchase ($18) is excluded from confirmed totals. An approved picnic request remains unpurchased; it is distinct from the recorded dinner purchase.
- Header/profile placement, filter controls, card arrangements, and income/bills/savings entry points are proposed layout choices.
- Wish-list lifecycle actions, comments, recurring-bill links, and allocation editing are presented as existing documented proposals where not already confirmed. Their appearance does not approve those rules.

## Scope and remaining work

No application features, Vue routes, API integration, persistence, dependencies, device installation, or network services were added. Existing product docs and the application scaffold were left unchanged.

These screens establish visual direction. Detailed forms, purchase/item detail screens, onboarding, loading/empty/error states, synchronization conflicts, multi-reviewer examples, accessibility validation, and tablet layouts need subsequent design passes. The pending-sync purchase is an illustrative state, not an implemented queue. Notification artwork does not implement delivery or read state. Mockup controls are not interactive.

## Build and verification

Run from the project root:

```sh
python design/ui-v1/build_mockups.py
```

The generator uses the Python standard library and the already-installed `rsvg-convert` renderer. No installation or dependency changes are required. It writes only within this design directory. Generated outputs: five desktop/mobile screen pairs, two notification examples, an overview (SVG + PNG for each), and `index.html`.

Commands used during this task: project inventory with `rg --files`; `cat`/`tail` to read project and avatar docs; `command -v` and `fc-list` for existing rendering tools/fonts; `git status --short` to inspect existing changes; the build command above; and a Python XML/PNG validation script. PNGs were visually inspected, including desktop/mobile layouts and notification lists. Category arithmetic was checked against the displayed totals. No app tests were run because application code was not changed. Browser rendering, real-device behavior, live responsive resizing, accessibility, and interactions are not verified by these static renders.

All task-created files are under `design/ui-v1/`: this README, generator, review HTML, and SVG/PNG artifacts. Existing changes in `docs/functionality.md`, `assets/`, `tools/`, and `output/` were present before this work and were not modified. No commit was created.
