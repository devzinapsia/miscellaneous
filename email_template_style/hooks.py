from .models.template_content import TEMPLATE_XMLIDS, odoo_body_param, odoo_subject_param


def snapshot_odoo_defaults(env):
    """Snapshot each target mail.template's pristine subject/body_html.

    Per slug, only runs once: if a snapshot already exists (e.g. the module
    was uninstalled and reinstalled after the templates were already
    overridden by a style, or this slug was already present in an earlier
    version of the module), it is left untouched so "Odoo" in Settings keeps
    restoring the real original, not whatever was last applied.

    Also called from ResConfigSettings._register_hook() (see models/res_config_settings.py)
    so that a slug added to TEMPLATE_XMLIDS in a later version still gets its
    snapshot captured on the next `-u` module update, not only on first install.
    """
    icp = env["ir.config_parameter"].sudo()
    for slug, xmlid in TEMPLATE_XMLIDS.items():
        subject_key = odoo_subject_param(slug)
        if icp.get_param(subject_key) is not False:
            continue
        template = env.ref(xmlid, raise_if_not_found=False)
        if not template:
            continue
        icp.set_param(subject_key, template.subject or "")
        icp.set_param(odoo_body_param(slug), template.body_html or "")


def post_init_hook(env):
    snapshot_odoo_defaults(env)
