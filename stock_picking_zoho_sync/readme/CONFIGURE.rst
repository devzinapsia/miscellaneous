Go to *Inventory > Configuration > Settings* and, under the *Zoho* section:

#. Enable *Synchronize with Zoho*.
#. Set the *Zoho sync URL*, the full Zoho endpoint used to receive the
   documents (including any query string parameters required by Zoho,
   such as a public key).
#. Optionally set the *Zoho sync token*. It is stored for future use but
   is not sent in the outgoing request yet, since the current integration
   endpoint does not require it as a separate header.

The scheduled action *Stock Picking: sync pending receipts with Zoho*
(*Settings > Technical > Automation > Scheduled Actions*, in developer
mode) runs every 10 minutes by default and can be adjusted there if a
different frequency is needed.
