Validate a Receipt (an incoming ``stock.picking``) normally. Once it
reaches the *Done* state, it is automatically flagged as pending Zoho
synchronization - no manual action is required.

The *Zoho pending* and *Zoho sent on* fields are available as optional
(hidden by default) columns in the *Inventory > Reporting/Operations >
Transfers* list view, and can be added from the column selector to
monitor the synchronization status of each receipt.

If a send to Zoho fails (network error, timeout, or an unexpected
response), the receipt stays flagged as pending and is retried
automatically on the next scheduled run. The error is logged with the
receipt's reference for troubleshooting.
