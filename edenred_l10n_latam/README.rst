==============================
Edenred - LATAM Document Type
==============================

Glue module: when ``l10n_latam_invoice_document`` is installed alongside
``edenred``, this module adds the ``l10n_latam_document_type_id`` and
``document_number`` fields to the Edenred import wizard, and passes them
through to the vendor bill created on confirmation.

**Table of contents**

.. contents::
   :local:

Configuration
=============

No configuration needed. This module installs itself automatically
(``auto_install``) whenever both ``edenred`` and
``l10n_latam_invoice_document`` are installed.

Usage
=====

Fill in "Document type" and "Document number" in the Edenred import
wizard, in addition to the base fields, before confirming.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/devzinapsia/miscellaneous/issues>`_.

Credits
=======

Authors
-------

* Zinapsia
