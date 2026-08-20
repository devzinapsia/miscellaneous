This module synchronizes validated incoming stock receipts (Receipts,
``stock.picking`` records whose operation type code is ``incoming``) with
Zoho, through an external HTTP endpoint.

To avoid slowing down the validation transaction, the receipt is not sent
synchronously. Instead, validating a receipt flags it as pending
synchronization, and a scheduled action running every 10 minutes picks up
all pending receipts and sends them to Zoho.

For each product line, the unit price ("valor") sent to Zoho is taken from
the linked purchase order line's unit price. If a receipt line has no
linked purchase order (a manual receipt with no purchase order), the
product's cost price is used instead as a fallback.
