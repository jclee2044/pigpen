# Receipt scanning implementation plan

November 9, 2026. Branch: `codex/receipt-scan`. Status: implementation authorized November 9, 2026; see the implementation verification record below. The original proposed steps are retained as the planning history.

## Recommendation

Use local RapidOCR with ONNX Runtime to recognize receipt text and positions, a small framework-free Python parser to produce purchase suggestions, and the existing purchase form for review. Generate a conservative name from recognized merchant/item text. Save only after confirmation through PigPen's operation executor. Keep one receipt as one purchase; place readable line items in its description and retain the image as an attachment.

This is the recommended starting point under PigPen's local-processing requirement, not a demonstrated accuracy winner. Benchmark representative receipt photos before committing to the engine. OCR recognizes text; identifying the correct total and associating line-item prices still require parsing and validation.

## Requirements and proposed scope

The current request authorizes research and planning for receipt scanning, name/total extraction or generation, optional line items, and creation of a purchase record. Existing requirements in [functionality.md](functionality.md) specify home-server extraction, review before saving, one purchase per receipt, and line items in the description. Earlier statements deferring extraction remain historical; this plan does not claim the feature is implemented.

Proposed first release: one JPEG/PNG/WebP receipt photo per scan, English receipts, USD, online scanning, manual category selection, editable date/merchant/name/total/description, and automatic attachment on confirmed save. Keep manual purchase entry available when scanning fails or the server is unreachable. Bank screenshots, PDFs, multiple photos per receipt, refunds, split transactions, automatic categorization and LLM advice are outside this iteration. Unsupported formats should give an actionable message, including HEIC if a phone supplies it; verify actual iPhone capture behavior before release.

TODO before implementation: obtain a representative set of receipt layouts and confirm whether photo-only input and description-based line items meet the intended workflow. Do not introduce a separate line-item ledger without a new requirement. Local processing and review already have documented answers and need no repeated confirmation.

## Receipt photo retention

Confirmed November 9, 2026: automatically delete receipt photos after three months of storage, with a per-photo option to keep them indefinitely. Keep the purchase record and its confirmed name, amount, date and line-item description after the image expires. This replaces indefinite retention as the default for receipt photos in this feature.

Proposed implementation details: calculate expiry as three calendar months from the original server storage timestamp, clamping to the last valid day of the destination month. Show the expiry date and a “Keep indefinitely” toggle during review and in purchase details. The override removes the expiry; turning it off restores the original expiry and must warn if the photo is already overdue. A daily cleanup processes due photos, so actual removal occurs on the first successful cleanup after expiry. Reprocessing must not reset the storage age.

Add retention metadata and a revision-checked operation to the documented contract before client integration. Cleanup must recheck overrides and all references immediately before unlinking a checksum-shared object: an unexpired or indefinitely retained reference protects the bytes. Expire the relevant attachment metadata through normal audit/sync behavior, preserve an image-expired state for the UI, and remove derived image copies as well. Use retryable cleanup state so crashes cannot leave silently broken attachments. Coordinate with backup creation so cleanup cannot invalidate an in-progress snapshot.

Existing full backups can retain a copy after its live photo expires. Proposed policy: omit expired photo bytes from new backups while preserving record metadata; let existing snapshots age out under the confirmed seven-daily/four-weekly schedule. Restore must preserve retention metadata and apply expired-image handling before serving attachments. Confirmed November 9: delete from live storage; allow normal backup retention, including preserving separately retained upgrade backups. Strict all-copy deletion requires a revised backup policy; do not rewrite or delete historical backups implicitly. Also confirm treatment of pre-feature receipt attachments whose receipt type is not recorded; do not apply cleanup to unrelated bank screenshots.

Add tests for calendar-month boundaries, indefinite retention, reverting overrides, races between override and cleanup, shared checksums, pending/canceled scans, crash recovery, backup/restore and unchanged purchase totals. No existing photos are deleted by this planning change.

## Options considered

| Option | Benefit | Cost or limitation | Decision |
| --- | --- | --- | --- |
| RapidOCR with ONNX Runtime | Local Python OCR with a CPU inference path; avoids a separate hosted API | Requires model assets, native wheels and receipt parsing | First candidate to benchmark |
| PaddleOCR directly | Local OCR pipeline with orientation and document correction options | Additional inference-engine setup and configuration | Compare if the first candidate misses accuracy targets |
| Tesseract | Established local OCR engine | Image preprocessing and receipt parsing still needed; system executable may need installation | Baseline if already available; do not install globally without approval |
| Local vision language model | Can potentially interpret varied layouts and produce names | Adds model serving, resource demands and generated-field validation | Escalation only if OCR plus parsing proves insufficient |
| Amazon Textract AnalyzeExpense | Purpose-built vendor, total and line-item extraction | Sends documents to a cloud service and introduces account/billing configuration | Excluded by current local-processing requirement |

RapidOCR's official [installation guide](https://rapidai.github.io/RapidOCRDocs/main/en/install_usage/rapidocr/install/) specifies the maintained `rapidocr` package and a separately installed inference engine such as `onnxruntime`; older engine-specific packages are being retired. Its [repository](https://github.com/RapidAI/RapidOCR) documents local integration. Pin the tested package/model combination instead of following changing defaults.

The [PaddleOCR pipeline documentation](https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/OCR.html) documents model configuration and local model paths. [Tesseract's quality guide](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html) identifies skew, uneven backgrounds and segmentation as recognition concerns. These support testing phone photos rather than relying on clean scanned examples. [Textract's receipt documentation](https://docs.aws.amazon.com/textract/latest/dg/invoices-receipts.html) lists vendor, total, quantity and item-price fields; it provides a useful comparison, but does not establish accuracy on this household's receipts.

The preference for RapidOCR is an engineering judgment about integration size and local operation. No provider benchmark establishes PigPen accuracy, latency or Python 3.14 compatibility.

## Existing integration points

- `frontend/src/components/PurchaseForm.vue` already collects item, amount, category, date, merchant and description, then calls `mutate('purchase.create', ...)`.
- `backend/pigpen/contracts.py` defines `PurchaseCreate`; `backend/pigpen/budget.py` validates category/approval relationships and creates purchases with notifications and spending alerts.
- `backend/pigpen/attachments.py` validates decoded JPEG/PNG/WebP images, enforces 10 MiB and 25 million pixels, and stores immutable checksum-addressed objects. Existing attachment uploads require an existing purchase, so scanning needs a draft image path before a purchase exists.
- Purchases already store `item`, integer `amount_minor`, `merchant`, `description` and `transaction_date`. The form limits item/merchant to 200 characters and description to 4,000. No purchase line-item table is needed for the proposed scope.
- Writes use `/api/v1/operations` with replay protection, audit/change records and notifications. Scanning must not bypass these services with direct purchase inserts.

## Execution steps

### 1 Prove extraction feasibility

Prepare approximately 30–50 labeled receipts spanning grocery stores, restaurants, fuel, retail, discounts, taxes, tips, long receipts, rotated photos, shadows and faint print. Keep real receipts and OCR results in private approved storage outside Git; commit only synthetic fixtures. Separate parser-development examples from held-out evaluation receipts.

Explain new dependencies before installing them in a project-owned environment. Test RapidOCR and ONNX Runtime wheels on the existing Python 3.14/Linux deployment. Check CPU/RAM needs, model licenses and transitive dependencies. If incompatible, propose a separate project-owned worker interpreter/runtime; do not change the application interpreter or machine packages silently. Pin dependencies, models and checksums; provision models before deployment and prove inference works with outbound network disabled.

Measure exact total accuracy, merchant accuracy, line-item description/price pairing, abstention rate, latency and peak memory. Proposed gate: at least 95% exact totals on readable supported held-out receipts, with ambiguous totals left blank or visibly flagged; target warm p95 extraction under 10 seconds on the actual server. Report counts as well as percentages, and assess cold start separately. These are acceptance targets, not current performance claims. If missed, compare direct PaddleOCR/preprocessing on the same set before adding an LLM or expanding scope.

### 2 Specify the contract before connecting clients

Document the final JSON schemas, state transitions, errors and examples in `docs/backend-api.md`, then generate TypeScript types. Proposed routes are multipart `POST /api/v1/receipt-scans` and JSON `GET /api/v1/receipt-scans/{id}`. POST includes stable operation/scan IDs, actor, client timestamp and image; it returns 202 with the persisted scan. Replays of the same request return the same scan; changed content with reused IDs returns 409.

The proposed result contains scan ID/revision/status, nullable merchant/item/amount/date suggestions, line-item suggestions, a formatted description, field evidence and warning codes. Money uses integer cents; uncertain values are null. Each line item may carry description, quantity as a decimal string, unit price and line total, with absent values left null. Recognition scores are evidence, not calibrated probabilities that a financial field is correct.

Document online-only confirmation, unsupported media, corrupt/oversized files, busy queues, worker timeouts, missing models, stale drafts, duplicates and canceled scans. Keep image access controlled and responses out of service-worker caches. Scanning produces no purchase or notification.

### 3 Add durable scan storage and execution

Add an additive migration for scan jobs: actor, image metadata/checksum, status, engine/model/parser versions, extracted result, revision, timestamps, attempts/lease, failure code and confirmed purchase ID. Proposed states: queued, processing, ready, failed, canceled and confirmed. Keep scan internals outside normal purchase sync; confirmed purchases and attachments use existing sync behavior.

Reuse validated immutable storage for the draft image. A small local worker claims jobs with short leases, performs OCR outside SQLite transactions, and persists results with lease/revision guards. Recover expired claims after restart; bound concurrency, queue size, attempts and execution time. Begin with one worker and no Redis/Celery dependency. Wire lifecycle into approved deployment tooling; ask before new machine-level service configuration.

Extend backup/restore to include unexpired or indefinitely retained images referenced by unconfirmed scans, not just purchase attachments. Apply the receipt photo retention policy above to canceled drafts as well. Avoid logging receipt text. Test backups while scans are pending and processing.

### 4 Implement conservative parsing

Keep the engine adapter separate from framework-free parsing functions and thin FastAPI routes. Normalize EXIF orientation using existing Pillow support, retain the original, and apply bounded preprocessing only when benchmark results justify it.

Group text using spatial coordinates. Rank explicitly labeled final totals; distinguish subtotal, tax, savings, tendered cash, change, balances and suggested tips. Never assume the largest number is the total. Use decimal parsing to integer cents; reject unsupported currency, ambiguous decimal formats and nonpositive totals under current purchase rules.

Extract line-item descriptions and their associated prices when supported by layout evidence. Keep discounts/tax/tips distinct and use arithmetic only as a consistency check; incomplete item recognition must not replace a printed total. Flag restaurant receipts with incomplete handwritten totals rather than guessing.

Generate a name using readable recognized text: a single reliable item description, otherwise `Purchase at {merchant}`, otherwise an editable `Receipt purchase` placeholder. Do not invent a product category. Suggest a date only when unambiguous; otherwise retain the visible current-date default for review. Format line items into the description. Never silently truncate beyond 4,000 characters: retain full extraction in the draft and require the user to edit the description or explicitly accept a shortened summary.

### 5 Make confirmation atomic and replay safe

Extend `purchase.create` with an optional receipt scan reference and expected scan revision, preserving old clients. Inside its existing transaction, validate that the scan is ready/unconfirmed, apply reviewed purchase fields through existing business rules, link the stored image as an attachment, mark the scan confirmed and commit normal audit/sync/notification records together. Reuse internal attachment validation; never accept a client-supplied filesystem path.

Require scan confirmation online initially; do not add it to the offline queue until dependencies and replay semantics are explicitly supported. Keep ordinary manual offline purchases working. Persist the operation ID and exact reviewed payload through timeouts so retry returns the original result.

Enforce one confirmation per scan even if two tabs use different operation IDs. Detect identical image checksums across scans and existing attachments and show the prior purchase before confirmation. Warn on same merchant/date/total for rephotographed receipts, but allow explicit override because legitimate repeat purchases exist. Check duplicates again at confirmation; exact-image overrides must be deliberate and audited. Define behavior for a previously deleted purchase; never silently recreate it on retry.

### 6 Build the capture and review flow

Add Scan receipt beside manual purchase creation. Offer mobile camera capture and a normal file picker fallback. Show preview, scanning progress, retry/cancel and recoverable errors. Keep API calls in `frontend/src/api/`, scan state in a composable/state module and presentation in Vue components.

Prefill the existing purchase form with suggestions, display the source image and warnings, and require the existing category selection. Make every suggested field editable. Do not overwrite edits if a delayed result arrives or the user switches profiles; bind each draft to its originating actor. Saving creates exactly one purchase with its receipt attached. Closing or canceling never records spending. Support resuming a persisted draft after refresh.

### 7 Verify the complete workflow

Test parsing against labeled fixtures and held-out photos. Test worker crashes, lease expiry, corrupt images, large dimensions, missing models, timeouts, duplicate uploads, concurrent confirmations, changed replay payloads, stale revisions, archived categories and profile changes. Assert no purchase exists before review and one purchase/attachment/notification set exists after successful confirmation or retries.

Run backend tests, generated-contract checks, frontend unit tests, lint and build. Add focused browser tests for capture/upload, review/correction, cancel/resume, failure/manual fallback, duplicate warning and exactly-once save. Verify existing manual/offline entry still works. Check backup/restore with draft and confirmed receipts. Test real Safari/iPhone and installed-PWA camera behavior; Chromium file-upload mocks cannot prove it.

Expected commands: `backend/.venv/bin/python -m pytest -q backend/tests`, `backend/.venv/bin/python tools/generate_api_types.py --check`, `npm --prefix frontend test`, `npm --prefix frontend run lint:check`, `npm --prefix frontend run build`, and the relevant Playwright/PWA configurations. Record actual commands, counts and unresolved failures during implementation.

### 8 Deploy the verified feature

Update functionality, API, operations and deployment docs. Under the standing deployment authorization, take and verify a consistent backup, retain previous application assets/backend and pinned OCR models, apply the additive migration, deploy the tested worker/application and verify HTTPS health and release bytes. Keep scanning disabled until model/worker readiness passes.

Verify the live UI with synthetic intercepted data and no production financial mutations. An actual receipt-to-database acceptance run requires an explicitly identified test record or user-driven household purchase. Preserve a rollback path that disables scanning and restores prior application behavior without destructively downgrading the database. Test compatibility of old application code with the additive schema and retain the backup for recovery.

## Planning verification

Created and switched to `codex/receipt-scan` from `master`. The initial sandboxed Git command could not write refs; the authorized elevated retry succeeded. Inspected project docs and purchase/attachment/contract code with `rg`, `cat` and `sed`; researched official OCR documentation. Only this plan was added. Existing untracked screenshots/test output were preserved. No commit, push, dependency installation, application change or deployment was performed. OCR accuracy, resource use, runtime compatibility and real-device capture remain implementation gates.

## Implementation decisions and verification

The user authorized implementation and verification step by step. The implemented save operation is `receipt.confirm`, wrapping existing purchase validation/creation inside the normal operation transaction, rather than changing `purchase.create`; this preserves old payload hashes and offline clients. Scan confirmation is online-only, while normal manual purchase entry remains available offline. The existing API service starts the bounded OCR worker; no new machine service is installed. Existing unclassified/manual image attachments are preserved; three-month retention applies to scanned receipt images.

Python 3.14 compatibility passed in a separate project-owned environment. RapidOCR 3.10.0/ONNX Runtime 1.31.1 and bundled PP-OCRv6 small detection/recognition plus the legacy angle classifier are pinned, with model checksums and license notices retained. Initial environment/model sizes are 382 MiB and 31 MiB. Thirty synthetic tilted/blurred receipt variations produced 30 exact totals and zero incorrect totals/abstentions, p95 whole-process time 1.754 seconds, peak child RSS 298,600 KiB. This verifies a constrained synthetic smoke set, not the proposed real-receipt accuracy gate. Real household receipts and physical iPhone/Safari capture remain acceptance checks.

See `output/receipt-scan/verification.md` for final commands, test counts, deployment result and limitations.

### Public receipt acceptance results — November 9, 2026

The user requested online receipt-image testing. The unchanged deployed extractor was evaluated on 12 preselected ExpressExpense receipt photos plus an independent Walmart example. Of 12 visible final totals, 9 were correct, 3 were blank and none were wrong; a separate unfilled-tip receipt correctly abstained. Merchant detection and line-item association also failed on several ordinary layouts. **The real-image extraction acceptance gate remains unmet; the feature must not be described as fully done.** These findings supersede any inference of broad reliability from the 30 synthetic examples. The application was not changed during this evaluation. See [case results, sources and remaining work](../output/receipt-online/report.md).

## Real-photo reliability follow-up

The user requested continued implementation after the public-image failures. The follow-up adds framework-free spatial matching, additional total/payment/gratuity handling, stricter separation of discounts and fees, date formats, currency cautions, and a required review acknowledgement. No OCR model/runtime dependency was changed. Successive randomly selected public batches exposed additional defects and became development/regression cases as soon as they informed changes; they must not be reported as untouched acceptance results afterward. The dataset contains repeated photographs of the same receipts, which further limits independence.

Recommendation scope is an editable **scan-and-review assistant** for ordinary printed receipts, with manual correction/fallback. The proposed 95% held-out exact-total target remains a proposed gate for a broader extraction-reliability claim, not permission to silently guess or reinterpret a test failure. The final report separates regression measurements, untouched results, optional/incomplete item extraction and physical-device checks. See [follow-up evidence](../output/receipt-online/follow-up.md).


Receipt camera entry — November 9, 2026 (confirmed): the Purchases + dropdown uses the same household-dropdown transition and sits flush against the button's bottom edge. Scan receipt automatically requests the rear-facing camera in a fullscreen view, with a shutter and bottom-left existing-photo picker. Captures and selected photos show a preview before Scan photo; Retake photo returns to the camera. Camera permission/unavailability errors retain library and native-camera fallback options. Streams stop on capture, close, backgrounding and component removal; late permission results are released. Browser permission is still required, and physical iPhone/Safari behavior remains a device acceptance check.

Removed the Resume a receipt UI and its explanatory copy, superseding earlier resume-entry requirements. Durable backend scans and their existing retention remain unchanged; reopening starts a fresh capture. The purchase form suppresses the two generic review/line-item notices while preserving concrete extraction-problem warnings, required review acknowledgement and photo-retention controls. No API, backend or dependency changes.


Receipt camera polish — November 9, 2026 (confirmed): camera preview fills the viewport with cover scaling instead of letterboxing, and captured JPEGs use a centered portrait crop (at most 3:4, matching a portrait viewport). Keep the whole receipt visible within the viewfinder; library images remain unchanged. Camera controls use PigPen's pink header, rose buttons, serif heading and theme surfaces. File-input cancel is stopped before it reaches the dialog cancel handler; an interrupted stream restarts when returning. Desktop pointer users see only Enter manually; primary coarse-pointer devices expose scanning (capability heuristic, not user-agent sniffing). Review checkboxes use inline flex labels, “I verified the receipt” and “Cancel”. No dependencies or API changes.


### Automatic capture feasibility (proposal, not implemented)

Automatic shutter is possible, but low camera motion alone cannot establish receipt presence or readable text. Proposed pipeline: detect a receipt-shaped document with all edges inside a safe viewfinder area; require sufficiently large text/receipt coverage, acceptable exposure and sharpness; compare successive frames for motion; then capture once after roughly one second of stable acceptable frames. Reset on movement, lost edges, glare or blur. Keep a manual shutter and preview/retake. A document detector can confuse other paper with a receipt, so receipt/text validation needs its own evaluation. No system can promise every printed character is readable merely from steadiness.

For privacy and server cost, evaluate low-resolution frames locally on the device; do not repeatedly upload camera frames to server OCR. A reliable detector/model and phone-specific thresholds require a separately evaluated implementation; no camera-analysis dependencies were added in this change. Validate moving/blurred/glare/cropped/no-receipt negatives as well as successful captures before enabling automatically. Remaining acceptance includes actual iPhone/Safari camera and picker behavior.

References: [file-input cancel bubbles when a picker is dismissed](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/cancel_event); [OpenCV edge detection](https://opencv.org/edge-detection-using-opencv/); [focus measure evaluation research](https://arxiv.org/abs/1604.00546). The proposed combined detector/stability policy above is an implementation recommendation, not a capability guaranteed by these APIs.


Receipt zoom and compact review — November 9, 2026: explicit zero shutter padding and equal minmax grid columns center both outer shutter and inner disk. Camera supports pinch, 1×/2×/3× presets and a 1–4× slider using a center digital crop; captured JPEG uses the same zoom. This does not claim native iPhone optical/ultrawide lens switching. Camera view disables browser pan/zoom with touch-action and local Safari gesture suppression; normal page zoom elsewhere remains unchanged. The reusable ReceiptPhotoPreview opens the existing image viewer from pre-upload and review screens; saved purchase attachments already use that viewer. The expiry note is 12px with a 4px gap beneath Keep photo indefinitely. No dependency/API/backend changes.

The supplied KFC receipt was run through the actual local OCR adapter/parser: merchant KFC, item Purchase at KFC, total 1588 cents, date 2024-11-21, three items 899/349/229 cents. “lelp” could not be reproduced from the attached file; no merchant alias/guess was added. The failing camera image would be needed to isolate that recognition error. Automatic receipt detection/capture remains proposed, not enabled. Manual shutter remains required.

Browser references: [touch-action](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/touch-action), [camera constraints and capabilities](https://developer.mozilla.org/en-US/docs/Web/API/Media_Capture_and_Streams_API/Constraints). Digital crop is the chosen portable implementation rather than an assumption of hardware zoom support.


Direct scanning and full-frame 1× — November 9, 2026 (confirmed): captured/selected images upload immediately and advance through OCR to the editable purchase form without a separate photo-approval/Scan photo step. The form offers Retake photo, which cancels that unsaved scan through the existing operation contract and opens a fresh camera at 1×. Retake is blocked during saving/replay and offline; errors remain visible in the form. Upload failures retain the file and idempotency key for Retry scan, with a retake alternative. Review and explicit Save purchase remain required. This change does not implement automatic receipt detection/shutter release.

Camera 1× now fits the complete source frame in a dedicated viewfinder between the header and controls, rather than cropping a landscape feed to a screen-shaped portrait. Image aspect ratio follows the actual feed; original width/height are preserved at 1×, and 2×–4× use a matching centered digital crop. This supersedes the earlier forced portrait image requirement to resolve the reported excessive zoom and preserve receipt edges. The app stays in a portrait-friendly full-screen layout but a landscape feed has surrounding space. Request resizeMode none where supported, without forcing an aspect ratio; browser/device lens selection can still limit the available field of view. Device camera is now available alongside the shutter to use native capture controls; ultrawide lens availability is not promised. No dependencies/API/backend changes.

Reference: [camera constraints and resizeMode](https://developer.mozilla.org/en-US/docs/Web/API/MediaTrackConstraints). The full-frame solution removes PigPen's extra cropping; physical iPhone lens selection and native picker behavior still require device verification.

Current implementation checkpoint (November 9, 2026): later confirmed UI requirements supersede the historical proposal-only notes above. Automatic capture is enabled using local receipt-shaped-paper/text, sharpness and motion heuristics; four sharp frames across 700ms are required. Manual capture remains. The 3:4 viewfinder and image crop match; no Device camera button or approval preview remains. Current controls are Hold steady, Cancel, Save, and Keep editing / Leave. The date is inline and purchase categories are parent-only. Three-month expiry with indefinite override and normal backup retention is implemented. Physical iPhone capture calibration remains unverified; heuristic detection and OCR require review.
