# PigPen functionality

## 1. Product and release scope

PigPen helps a household allocate money each month, record purchases, track wish-list items, and approve proposed uses of shared funds. Initially two people share the app, with support for adding more users later. All household information is visible to every user.

Version 1 includes profiles, monthly budgets, income, recurring bills, starting savings, manual purchases, image attachments, wish lists, approval toggles, push and in-app notifications, and offline viewing and purchase/approval entry.

Automatic receipt/screenshot extraction and LLM suggestions are deferred. Future document extraction must run locally. There are no savings goals or other goal objects: budgets specify monetary allocations per category.

## 2. Profiles and identity

- On a browser/device with no selected identity, show existing profiles and an option to create a profile. Creating one requires a name and a pig avatar from a built-in selection.
- Remember the selected profile in that browser/device and open under it on subsequent visits.
- The profile screen supports switching users and adding profiles. No password or PIN is required in version 1.
- Adding a user automatically creates their personal category.
- Attribute purchases, wish-list items, requests, and approval changes to the acting profile.
- All data is public within the household. Profile selection provides attribution, not verified authentication.
- Offline queued actions retain their original acting profile even if the device switches users before synchronization.

**Proposed defaults:** allow name/avatar edits; require distinct display names to avoid confusion; archive users instead of deleting their history. Creating and switching to an uncached profile requires connectivity.

## 3. Monthly budget

There is one shared household budget with an individual personal allowance for each user. Users define how much money is allocated to each category for a selected month. Display allocated, spent, and remaining amounts, plus household totals.

Initial shared categories:

- Housing
- Food
- Gas
- Dates
- Savings
- Phone
- Car insurance

Each user additionally has their own Personal category, visibly labeled with their name. Users may create, rename, and archive additional categories. Archiving removes a category from new-entry choices while preserving its transactions and historical allocations.

Only Personal categories can contain subcategories. Subcategories are defined by the user and have one nesting level. The parent Personal category represents that user's allowance; spending in its subcategories counts toward that allowance exactly once.

**Proposed defaults:**

- Set allocations in a single household currency, initially USD.
- Use calendar months in the household timezone, initially America/New_York.
- Copy the previous month's allocations when initializing a new month, with an opportunity to edit them. Preserve past months independently.
- Do not roll unused category allocations forward automatically. Recorded savings persist across months.
- Personal subcategories classify purchases without separate allocations in version 1. The Personal parent holds the allowance.
- Retain the system-created Personal category for each active user; it may be renamed but cannot be archived independently of that user.
- Warn about overspending or allocations exceeding expected income, but allow the user to continue.
- Treat an unallocated category as zero allocated, making its spending visible as over budget.

Example: Alex receives a $200 Personal allocation. Purchases of $30 in Books and $20 in Hobbies leave $150 in Alex's Personal allowance.

## 4. Income, recurring bills, and starting savings

Users can enter income, recurring bills, and starting savings in addition to purchases and category allocations.

**Proposed version 1 behavior:**

- Income entries contain a description, amount, date, and attributed user. They contribute to actual income for their month.
- Expected monthly income can be entered separately to support planning before income arrives. Expected and actual income must be labeled separately and never added together.
- Recurring bill definitions contain a name, expected amount, category, frequency, next due date, and optional notes. Initially support monthly recurrence and configurable due days.
- Bills appear as upcoming commitments. Marking a bill paid creates or links one purchase; the bill definition itself is not spending.
- For due days that do not occur in a month, use that month's final day.
- Starting savings is a dated opening amount recorded once, not new monthly income.
- Savings allocations represent intended contributions. Record actual contributions and withdrawals separately; do not count a savings contribution as both an expense and a savings movement.
- Show recorded savings as opening savings plus contributions minus withdrawals. Label it as manually tracked savings, not a bank-verified balance.

Account connections, reconciliation, debt management, and comprehensive account balances are outside the defined first-release scope.

## 5. Purchases and attachments

Users enter an item/service, amount, and category. The app records the acting user and current date automatically, while allowing the transaction date to be corrected. Purchases can be browsed by category and month; Personal purchases can also be filtered by user and subcategory.

**Proposed default fields:** required item/service, positive amount, category, purchaser, and transaction date; optional merchant and free-text description. Description can hold receipt line items. Purchase details show attachments, description, and any linked approval or recurring bill. Support editing and deleting an incorrectly entered purchase while retaining an audit event.

One receipt represents one total purchase. Version 1 lets users attach receipt photos or bank screenshots and enter their totals and descriptions manually. It does not extract transactions from images. Offline image uploads are not required in version 1; users can save the purchase offline and attach images after reconnecting.

Future extraction must run on the home server, propose a total and relevant details, and require review before saving. If available, line items belong in the expandable description. Extracted dates can replace the default transaction date after review. Duplicate-import detection and multi-transaction bank screenshot behavior must be specified before extraction ships.

**Proposed attachment defaults:** accept JPEG, PNG, and WebP up to 10 MB per file; preserve originals until explicitly deleted; allow removal of an attachment without removing its purchase. Split transactions, refunds, payment-account tracking, and recurring income are not yet specified.

## 6. Wish lists

Each item contains a name, price, description, and optional link, and records its owner and creation time. All users can view household wish lists. Creating an item notifies the other users.

**Proposed defaults:** the creator manages the item; support active, purchased, and archived states. A wish-list item may be used to prefill an approval request or purchase, but neither is created automatically. Marking an item purchased does not itself record spending.

## 7. Shared-fund approval requests

Users may explicitly submit any proposed purchase for approval, whether or not it already fits a category. A request contains an item name, estimated price, description, optional link, requester, and optional proposed category.

The other user controls an approval toggle. Turning it on approves the request; turning it off removes approval. Each accepted change sends a notification to the other user. The requester cannot approve their own request.

Approval does not create a purchase or reserve money. A user explicitly records the actual purchase and links it to the request. The actual amount and date can differ from the proposal. This is a household agreement workflow; the app cannot prevent spending outside the app.

**Proposed defaults requiring confirmation:**

- For more than two users, one approval from any active non-requester is sufficient. Each reviewer has their own toggle; the request is approved while at least one eligible reviewer has theirs on.
- Notify all other active household profiles about new requests and accepted toggle changes, even when another reviewer's approval keeps the overall request approved.
- An off toggle means "not approved by this reviewer," not a separate rejected state.
- The requester may cancel a request. Changing its price, item, or substantive description clears approvals and notifies reviewers.
- Once linked to a recorded purchase, retain the final approval history and make the toggles read-only.
- If a purchase has no suitable category, select or create one before recording it.
- Changes to a submitted request and its cancellation require connectivity in version 1.

## 8. Notifications

Provide both an in-app notification inbox and browser push notifications for:

- New wish-list items.
- New approval requests.
- Approval toggled on or off and resulting approval changes.
- Budget limits reached or exceeded.
- Comments.

Push requires the device/browser user's permission. In-app notifications remain available if permission is denied or push is unsupported. Users can open a notification to its associated record and mark notifications read.

**Proposed defaults:** support plain-text comments on wish-list items and approval requests, since comment notifications were requested. Notify other household profiles when a comment is added. Notify once per category/month for reaching its allocation and once for exceeding it; an allocation edit alone does not trigger spending alerts. Notify all active users for shared-category limits and the allowance owner for Personal limits.

Push subscriptions are associated with the profile currently selected on that installation. Switching profiles reassigns future push delivery for that installation. Notifications already displayed by the operating system may remain visible. Multiple devices may subscribe for the same profile.

Push delivery depends on browser/platform support and network access; it is not a guarantee that another user saw a request. Avoid financial details in push previews by default.

## 9. Offline use and synchronization

- After an initial online visit, show previously loaded data with a last-synchronized indicator.
- Permit offline purchase entry, approval-request creation, and approval-toggle changes on cached requests.
- Clearly distinguish queued changes from server-confirmed records. An offline approval displays "pending sync" and does not count as a shared confirmed approval.
- Retry synchronization on reconnect, app foregrounding, and explicit user action. Background synchronization may improve delivery where supported but is not required for correctness.
- Preserve the original purchase date and acting profile when uploading queued actions.
- Send notifications only after the server accepts the associated action.
- Never create duplicate purchases or notifications because an operation was retried.
- If another user changed the same approval while a device was offline, require review against the current request instead of silently overwriting it.
- Keep a failed or conflicting action visible with an explanation and a retry, revise, or discard option.

**Proposed default:** budget, profile, recurring-bill, wish-list, comment, and attachment mutations require connectivity in version 1. Offline purchase edits/deletions are also deferred; new purchases and approval actions are the guaranteed offline writes.

## 10. Decisions still open

The user confirmed the main requirements. The following unanswered details have proposed defaults above and can be revised before implementation:

1. Currency, allocation carryover, and whether Personal subcategories need individual allocations.
2. Required purchase fields and support for refunds, split purchases, and payment accounts.
3. Expected-income planning, bill frequencies, and savings movement behavior.
4. Multi-user approval aggregation, request revisions, and post-purchase toggle behavior.
5. Comment placement, budget-alert thresholds, and notification recipients/preferences.
6. Attachment limits/retention, backup retention, and home-network versus remote access.

These are working design choices, not blockers to documenting or starting the app. Receipt extraction and LLM advice remain explicitly deferred.

## 11. Avatar customization assets

Confirmed November 6, 2026: pig avatars support independently swappable hats, glasses, optional eyelashes, bandana colors (including no bandana), and flat background colors. The initial [layered SVG asset pack](../assets/avatars/pig-v1/README.md) includes a standalone customization preview. Its particular styles and palette are initial artwork choices. Profile UI integration, persistence, and the frontend/backend contract are not implemented by this asset work.
