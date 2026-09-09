"""Content for each Zinapsia email style, keyed by the same slug used in reference/
(the 6 slugs extracted from the Word doc) or authored directly for this module
(purchase/self-billing/proforma/helpdesk/auth -- no source document for these).

TEMPLATE_XMLIDS maps each slug to the real mail.template xmlid it overrides.
The closing signature on every letter-style template is a static
"El equipo de {company}" line -- no per-user name or personal signature.
"""

TEMPLATE_XMLIDS = {
    "factura": "account.email_template_edi_invoice",  # Factura
    "notas_credito": "account.email_template_edi_credit_note",  # Notas de Crédito
    "pagos": "account.mail_template_data_payment_receipt",  # Pagos
    "cotizacion_orden_venta": "sale.email_template_edi_sale",  # Cotización y Orden de Venta
    "orden_venta_confirmada": "sale.mail_template_sale_confirmation",  # Orden de Venta Confirmada
    "orden_venta_confirmacion_pago": "sale.mail_template_sale_payment_executed",  # Orden de Venta - Confirmación de Pago
    "compra_solicitud_cotizacion": "purchase.email_template_edi_purchase",  # Compras: Solicitud de Cotización (RFQ)
    "compra_orden_confirmada": "purchase.email_template_edi_purchase_done",  # Compras: Orden de Compra
    "compra_recordatorio": "purchase.email_template_edi_purchase_reminder",  # Compras: Recordatorio al Proveedor
    "autofactura": "account.email_template_edi_self_billing_invoice",  # Autofactura
    "autofactura_nota_credito": "account.email_template_edi_self_billing_credit_note",  # Autofactura: Nota de Crédito
    "factura_proforma": "sale.email_template_proforma",  # Ventas: Factura Proforma
    "helpdesk_ticket_recibido": "helpdesk.new_ticket_request_email_template",  # Help Desk: Ticket Recibido
    "helpdesk_ticket_cerrado": "helpdesk.solved_ticket_request_email_template",  # Help Desk: Ticket Cerrado
    "helpdesk_encuesta_satisfaccion": "helpdesk.rating_ticket_request_email_template",  # Help Desk: Encuesta de Satisfacción
    "usuario_invitacion": "auth_signup.set_password_email",  # Usuarios: Invitación a Odoo
    "usuario_recordatorio_pendiente": "auth_signup.mail_template_data_unregistered_users",  # Usuarios: Recordatorio de Invitación Pendiente
    "usuario_cuenta_creada": "auth_signup.mail_template_user_signup_account_created",  # Usuarios: Cuenta de Portal Creada
    "portal_invitacion": "auth_signup.portal_set_password_email",  # Usuarios: Invitación a Portal
    "usuario_invitacion_2fa": "auth_totp_mail.mail_template_totp_invite",  # Usuarios: Invitación a Activar 2FA
}


def odoo_subject_param(slug):
    """ir.config_parameter key holding the pristine subject captured on install."""
    return f"email_template_style.odoo_subject.{slug}"


def odoo_body_param(slug):
    """ir.config_parameter key holding the pristine body_html captured on install."""
    return f"email_template_style.odoo_body.{slug}"

FORMAL_CONTENT = {
    "factura": {
        "subject": """{{ object.company_id.name }} - {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Estimado&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>

        Le enviamos el comprobante 
        <span style="font-weight: bold;" t-out="(object.name or '').replace('/', '-') or ''">FA-A00001-00000001</span>
        por un total de 
        <span style="font-weight: bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 1000.00</span>.
    </p>

    <div><br/></div>

    <div>
        Por favor, no dude en contactarnos si tiene alguna consulta sobre esta transacción.
        <br/><br/>
        Saludos cordiales.
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "notas_credito": {
        "subject": """{{ object.company_id.name }} - Nota de crédito {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Estimado&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>

        Le enviamos la siguiente 
        <t t-if="object.name">
            nota de crédito <span style="font-weight:bold;" t-out="object.name or ''">RINV/2021/05/0001</span>
        </t>
        <t t-else="">
            nota de crédito
        </t>
        <t t-if="object.reversed_entry_id">
            (con referencia: <t t-out="object.reversed_entry_id.name or ''"></t>)
        </t>
        <t t-elif="object.invoice_origin">
            (con referencia: <t t-out="object.invoice_origin or ''"></t>)
        </t>
        por un importe total de 
        <span style="font-weight:bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">
            $143,750.00
        </span>.
        <br/><br/>
    </p>

    <div>
        Por favor, no dude en contactarnos si tiene alguna consulta sobre esta transacción.
        <br/><br/>
        Saludos cordiales.
    </div> 

<div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>
</div>

<div>
    <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
    <div><br/></div>
</div>""",
    },
    "pagos": {
        "subject": """{{ object.company_id.name }} - {{ 'Recibo' if object.payment_type == 'inbound' else 'Orden de pago' }} {{ object.name }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-radius:0px; border-style:none; box-sizing:border-box;&#10;              border-width:0px; margin: 0px; padding: 0px; font-size: 13px;">
        Estimado&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>

        <t t-if="object.payment_type == 'inbound'">
            Le enviamos el recibo de cobranza 
            <span style="font-weight:bold;" t-out="(object.name or '').replace('/','-') or ''">RE00001-00000001</span>
            por un total de 
            <span style="font-weight:bold;" t-out="format_amount(object.amount, object.currency_id) or ''">$ 1000.00</span>.
        </t>

        <t t-if="object.payment_type == 'outbound'">
            Le enviamos la orden de pago 
            <span style="font-weight:bold;" t-out="(object.name or '').replace('/','-') or ''">P00001-00000001</span>
            por un total de 
            <span style="font-weight:bold;" t-out="format_amount(object.amount, object.currency_id) or ''">$ 1000.00</span>.
        </t>
    </p>

    <div><br/></div>

    <div>
        Por favor, no dude en contactarnos si tiene alguna consulta sobre esta transacción.
        <br/><br/>
        Saludos cordiales.
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>
</div>

<div>
    <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
    <div><br/></div>
</div>""",
    },
    "cotizacion_orden_venta": {
        "subject": """{{ object.company_id.name }} - {{ object.state in ('draft', 'sent') and (ctx.get('proforma') and 'Proforma' or 'Cotización') or 'Orden' }} {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border-radius:0px; border-style:none; box-sizing:border-box;&#10;              border-width:0px; margin: 0px; padding: 0px; font-size: 13px;">

        <t t-set="doc_name" t-value="'cotización' if object.state in ('draft', 'sent') else 'orden'"></t>

        Estimado&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>

        <t t-if="ctx.get('proforma')">
            Le enviamos la factura proforma invoice para la 
            <t t-out="doc_name or ''">cotización</t> 
            <span style="font-weight: bold;" t-out="object.name or ''">S00052</span>
            <t t-if="object.origin">
                (con referencia: <t t-out="object.origin or ''"></t>)
            </t>
            por un total de 
            <span style="font-weight: bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$10.00</span>.
        </t>

        <t t-else="">
            <t t-set="is_quotation" t-value="object.state in ('draft', 'sent')"></t>

            <t t-if="is_quotation">
                Le enviamos la cotización 
                <span t-att-style="'font-weight: bold;'">
                    <t t-esc="object.name or ''"></t>
                </span>
                <t t-if="object.origin">
                    (con referencia: <t t-esc="object.origin or ''"></t>)
                </t>
                por un total de 
                <span t-att-style="'font-weight: bold;'">
                    <t t-esc="format_amount(object.amount_total, object.currency_id) or ''"></t>
                </span>.
            </t>

            <t t-else="">
                Registramos su orden 
                <span t-att-style="'font-weight: bold;'">
                    <t t-esc="object.name or ''"></t>
                </span>
                <t t-if="object.origin">
                    (con referencia: <t t-esc="object.origin or ''"></t>)
                </t>
                por un total de 
                <span t-att-style="'font-weight: bold;'">
                    <t t-esc="format_amount(object.amount_total, object.currency_id) or ''"></t>
                </span>.
            </t>
        </t>

        <br/>

        <t t-set="documents" t-value="object._get_product_documents()"></t>

        <t t-if="documents">
            <br/>
            <t t-if="len(documents) &gt; 1">
                Aquí hay algunos documentos adicionales que podrían interesarle:
            </t>
            <t t-else="">
                Aquí hay otro documento que podría interesarle:
            </t>

            <ul style="border-radius:0px; border-style:none; padding:0 0 0 32px; margin:0px 0 0px 0;&#10;                       box-sizing:border-box; border-width:0px; list-style-type:disc; margin-bottom: 0;">
                <t t-foreach="documents" t-as="document">
                    <li style="font-size: 13px;">
                        <a t-out="document.ir_attachment_id.name" t-att-href="object.get_portal_url('/document/' + str(document.id))" t-att-target="target" style="color: #374151; text-decoration: none; border: none;">
                        </a>
                    </li>
                </t>
            </ul>
        </t>

        <br/>

        </p><div>
            Por favor, no dude en contactarnos si tiene alguna consulta sobre esta transacción.
            <br/><br/>
            Saludos cordiales.
        </div>

        <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>
    

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "orden_venta_confirmada": {
        "subject": """{{ object.company_id.name }} - {{ (object.get_portal_last_transaction().state == 'pending') and 'Orden pendiente' or 'Orden' }} {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border-radius:0px; border-style:none; box-sizing:border-box;&#10;              border-width:0px; margin: 0px; padding: 0px; font-size: 13px;">
        Estimado&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>
        <t t-set="tx_sudo" t-value="object.get_portal_last_transaction()"></t>
        Su orden <span style="font-weight:bold;" t-out="object.name or ''">S00049</span> por un importe de <span style="font-weight:bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 10.00</span>
        <t t-if="object.state == 'sale' or (tx_sudo and tx_sudo.state in ('done', 'authorized'))">
            quedó confirmada.<br/>
         </t>
        <t t-elif="tx_sudo and tx_sudo.state == 'pending'">
            está pendiente. Se confirmará cuando recibamos su pago.
            <t t-if="object.reference">
                La referencia de pago es <span style="font-weight:bold;" t-out="object.reference or ''"></span>.
            </t>
        </t>
        <br/>
        <t t-set="documents" t-value="object._get_product_documents()"></t>
        <t t-if="documents">
            <br/> 
            <t t-if="len(documents)&gt;1">
                A continuación encontrará algunos documentos adicionales que podrían interesarle:
            </t>
            <t t-else="">
                A continuación encontrará otro documento que podría interesarle:
            </t>
            </t></p><ul style="margin-bottom: 0;">
                <t t-foreach="documents" t-as="document">
                    <li style="font-size: 13px;">
                        <a t-out="document.ir_attachment_id.name" t-att-href="object.get_portal_url('/document/' + str(document.id))" t-att-target="target"></a>
                    </li>
                </t>
            </ul>
        
        <div>
            Por favor, no dude en contactarnos si tiene alguna consulta sobre esta transacción.
            <br/><br/>
            Saludos cordiales.
        </div>
        <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>
        <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
        <br/><br/>
    <p/>
<t t-if="hasattr(object, 'website_id') and object.website_id">
    <div style="margin: 0px; padding: 0px;">
        <table width="100%" style="color: #454748; font-size: 12px; border-collapse: collapse; white-space: nowrap;">
            <tbody><tr style="border-bottom: 2px solid #dee2e6;">
                <td style="width: 150px;"><span style="font-weight:bold;">Productos</span></td>
                <td>
                </td><td width="15%" align="center"><span style="font-weight:bold;">Cantidad</span></td>
                <td width="20%" align="right">
                    <span style="font-weight:bold;">
                        <t t-if="object.website_id.show_line_subtotals_tax_selection == 'tax_excluded'">
                            Sin IVA
                        </t>
                        <t t-else="">
                            Con IVA
                        </t>
                    </span>
                </td>
            </tr>
        </tbody></table>
        <t t-set="current_subtotal" t-value="0"></t>
        <t t-foreach="object.order_line" t-as="line">
            <t t-set="line_subtotal" t-value="                     line.price_subtotal                     if object.website_id.show_line_subtotals_tax_selection == 'tax_excluded'                     else line.price_total                 "></t>
            <t t-set="current_subtotal" t-value="current_subtotal + line_subtotal"></t>
            <t t-if="(not hasattr(line, 'is_delivery') or not line.is_delivery) and (                     line.display_type in ['line_section', 'line_note']                     or line.product_type == 'combo'                 )">
                <t t-set="loop_cycle_number" t-value="loop_cycle_number or 0"></t><t t-set="loop_cycle_number" t-value="loop_cycle_number + 1"></t><table width="100%" style="color: #454748; font-size: 12px; border-collapse: collapse;">
                    
                    <tbody><tr t-att-style="'background-color: #f2f2f2' if loop_cycle_number % 2 == 0 else 'background-color: #ffffff'">
                        
                        <td colspan="4">
                            <t t-if="line.display_type == 'line_section' or line.product_type == 'combo'">
                                <span style="font-weight:bold;" t-out="line.name or ''">Curso sobre el cuidado de los árboles</span>
                                <t t-set="current_section" t-value="line"></t>
                                <t t-set="current_subtotal" t-value="0"></t>
                            </t>
                            <t t-elif="line.display_type == 'line_note'">
                                <i t-out="line.name or ''">Curso sobre el cuidado de los árboles</i>
                            </t>
                        </td>
                    </tr>
                </tbody></table>
            </t>
            <t t-elif="(not hasattr(line, 'is_delivery') or not line.is_delivery)">
                <t t-set="loop_cycle_number" t-value="loop_cycle_number or 0"></t><t t-set="loop_cycle_number" t-value="loop_cycle_number + 1"></t><table width="100%" style="color: #454748; font-size: 12px; border-collapse: collapse;">
                    
                    <tbody><tr t-att-style="'background-color: #f2f2f2' if loop_cycle_number % 2 == 0 else 'background-color: #ffffff'">
                        
                        <td style="width: 150px;">
                            <img t-attf-src="/web/image/product.product/{{ line.product_id.id }}/image_128" style="width: 64px; height: 64px; object-fit: contain;" alt="Product image"/>
                        </td>
                        <td align="left" t-out="line.product_id.name or ''">	Curso sobre el cuidado de los árboles</td>
                        <td width="15%" align="center" t-out="line.product_uom_qty or ''">1</td>
                        <td width="20%" align="right"><span style="font-weight:bold; white-space: nowrap;">
                        <t t-if="object.website_id.show_line_subtotals_tax_selection == 'tax_excluded'">
                            <t t-out="format_amount(line.price_reduce_taxexcl, object.currency_id) or ''">$ 10.00</t>
                        </t>
                        <t t-else="">
                            <t t-out="format_amount(line.price_reduce_taxinc, object.currency_id) or ''">$ 10.00</t>
                        </t>
                        </span></td>
                    </tr>
                </tbody></table>
            </t>
            <t t-if="current_section and (                     line_last                     or object.order_line[line_index+1].display_type == 'line_section'                     or object.order_line[line_index+1].product_type == 'combo'                     or (                         line.combo_item_id                         and not object.order_line[line_index+1].combo_item_id                     )                 ) and not line.is_downpayment">
                <t t-set="current_section" t-value="None"></t>
                <t t-set="loop_cycle_number" t-value="loop_cycle_number or 0"></t><t t-set="loop_cycle_number" t-value="loop_cycle_number + 1"></t><table width="100%" style="color: #454748; font-size: 12px; border-collapse: collapse;">
                    
                    <tbody><tr t-att-style="'background-color: #f2f2f2' if loop_cycle_number % 2 == 0 else 'background-color: #ffffff'">
                        
                        <td style="width: 100%" align="right">
                            <span style="font-weight: bold;">Subtotal:</span>
                            <span t-out="format_amount(current_subtotal, object.currency_id) or ''">$ 10.00</span>
                        </td>
                    </tr>
                </tbody></table>
            </t>
        </t>
    </div>
    <div style="margin: 0px; padding: 0px;" t-if="hasattr(object, 'carrier_id') and object.carrier_id">
        <table width="100%" style="color: #454748; font-size: 12px; border-spacing: 0px 4px; white-space: nowrap;" align="right">
            <tbody><tr>
                <td style="width: 60%">
                </td><td style="width: 30%; border-top: 1px solid #dee2e6;" align="right"><span style="font-weight:bold;">Entrega:</span></td>
                <td style="width: 10%; border-top: 1px solid #dee2e6;" align="right" t-out="format_amount(object.amount_delivery, object.currency_id) or ''">$ 0.00</td>
            </tr>
            <tr>
                <td style="width: 60%">
                </td><td style="width: 30%;" align="right"><span style="font-weight:bold;">Subtotal:</span></td>
                <td style="width: 10%;" align="right" t-out="format_amount(object.amount_untaxed, object.currency_id) or ''">$ 10.00</td>
            </tr>
        </tbody></table>
    </div>
    <div style="margin: 0px; padding: 0px;" t-else="">
        <table width="100%" style="color: #454748; font-size: 12px; border-spacing: 0px 4px; white-space: nowrap;" align="right">
            <tbody><tr>
                <td style="width: 60%">
                </td><td style="width: 30%; border-top: 1px solid #dee2e6;" align="right"><span style="font-weight:bold;">Subtotal:</span></td>
                <td style="width: 10%; border-top: 1px solid #dee2e6;" align="right" t-out="format_amount(object.amount_untaxed, object.currency_id) or ''">$ 10.00</td>
            </tr>
        </tbody></table>
    </div>
    <div style="margin: 0px; padding: 0px;">
        <table width="100%" style="color: #454748; font-size: 12px; border-spacing: 0px 4px; white-space: nowrap;" align="right">
            <tbody><tr>
                <td style="width: 60%">
                </td><td style="width: 30%;" align="right"><span style="font-weight:bold;">Impuestos:</span></td>
                <td style="width: 10%;" align="right" t-out="format_amount(object.amount_tax, object.currency_id) or ''">$ 0.00</td>
            </tr>
            <tr>
                <td style="width: 60%">
                </td><td style="width: 30%; border-top: 1px solid #dee2e6;" align="right"><span style="font-weight:bold;">Total:</span></td>
                <td style="width: 10%; border-top: 1px solid #dee2e6;" align="right" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 10.00</td>
            </tr>
        </tbody></table>
    </div>
    <div t-if="object.partner_invoice_id" style="margin: 0px; padding: 0px;">
        <table width="100%" style="color: #454748; font-size: 12px;">
            <tbody><tr>
                <td style="padding-top: 10px;">
                    <span style="font-weight:bold;">Dirección de facturación:</span>
                    <t t-out="object.partner_invoice_id.street or ''">1201 S Figueroa St</t>
                    <t t-out="object.partner_invoice_id.city or ''">Los Angeles</t>
                    <t t-out="object.partner_invoice_id.state_id.name or ''">California</t>
                    <t t-out="object.partner_invoice_id.zip or ''">90015</t>
                    <t t-out="object.partner_invoice_id.country_id.name or ''">Estados Unidos</t>
                </td>
            </tr>
            <tr>
                <td>
                    <span style="font-weight:bold;">Método de pago:</span>
                    <t t-if="tx_sudo.token_id">
                        <t t-out="tx_sudo.token_id.display_name or ''"></t>
                    </t>
                    <t t-else="">
                        <t t-out="tx_sudo.provider_id.sudo().name or ''"></t>
                    </t>
                    (<t t-out="format_amount(tx_sudo.amount, object.currency_id) or ''">$ 10.00</t>)
                </td>
            </tr>
        </tbody></table>
    </div>
    <div t-if="object.partner_shipping_id and not object.only_services" style="margin: 0px; padding: 0px;">
        <table width="100%" style="color: #454748; font-size: 12px;">
            <tbody><tr>
                <td>
                    <br/>
                    <span style="font-weight:bold;">Dirección de envío:</span>
                    <t t-out="object.partner_shipping_id.street or ''">1201 S Figueroa St</t>
                    <t t-out="object.partner_shipping_id.city or ''">Los Angeles</t>
                    <t t-out="object.partner_shipping_id.state_id.name or ''">California</t>
                    <t t-out="object.partner_shipping_id.zip or ''">90015</t>
                    <t t-out="object.partner_shipping_id.country_id.name or ''">Estados Unidos</t>
                </td>
            </tr>
        </tbody></table>
        <table t-if="hasattr(object, 'carrier_id') and object.carrier_id" width="100%" style="color: #454748; font-size: 12px;">
            <tbody><tr>
                <td>
                    <span style="font-weight:bold;">Método de envío:</span>
                    <t t-out="object.carrier_id.name or ''"></t>
                    <t t-if="object.amount_delivery == 0.0">
                        (Gratis)
                    </t>
                    <t t-else="">
                        (<t t-out="format_amount(object.amount_delivery, object.currency_id) or ''">$ 10.00</t>)
                    </t>
                </td>
            </tr>
            <tr t-if="object.carrier_id.carrier_description">
                <td>
                    <strong>Descripción de envío:</strong>
                    <t t-out="object.carrier_id.carrier_description"></t>
                </td>
            </tr>
        </tbody></table>
    </div>
</t>
</div>""",
    },
    "orden_venta_confirmacion_pago": {
        "subject": """{{ object.company_id.name }} - {{ (object.get_portal_last_transaction().state == 'pending') and 'Orden pendiente' or 'Orden' }} {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border-radius:0px; border-style:none; box-sizing:border-box;&#10;              border-width:0px; margin: 0px; padding: 0px; font-size: 13px;">
        <t t-set="transaction_sudo" t-value="object.get_portal_last_transaction()"></t>
        Estimado&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>
        El pago con la referencia
        <span style="font-weight:bold;" t-out="transaction_sudo.reference or ''">SOOO49</span>
        por un total de
        <span style="font-weight:bold;" t-out="format_amount(transaction_sudo.amount, object.currency_id) or ''">$ 10.00</span>
        para la orden
        <span style="font-weight:bold;" t-out="object.name or ''">S00049</span>
        <t t-if="transaction_sudo and transaction_sudo.state == 'pending'">
            está pendiente.
            <br/>
            <t t-if="object.currency_id.compare_amounts(object.amount_paid + transaction_sudo.amount, object.amount_total) &gt;= 0 and object.state in ('draft', 'sent')">
                Confirmaremos su orden una vez recibido el pago.
            </t>
            <t t-else="">
                Una vez que se confirmen, faltarán
                <span style="font-weight:bold;" t-out="format_amount(object.amount_total - object.amount_paid - transaction_sudo.amount, object.currency_id) or ''">$ 10.00</span>
                por pagar.
            </t>
        </t>
        <t t-else="">
            quedó confirmado.
            <t t-if="object.currency_id.compare_amounts(object.amount_paid, object.amount_total) &lt; 0">
                <br/>
                Saldo pendiente de pago:
               <span style="font-weight:bold;" t-out="format_amount(object.amount_total - object.amount_paid, object.currency_id) or ''">$ 10.00</span>.                
            </t>
        </t>
        <br/><br/>
        </p><div>
            Por favor, no dude en contactarnos si tiene alguna consulta sobre esta transacción.
            <br/><br/>
            Saludos cordiales.
        </div>
        <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>
        <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
       </div>
</div>""",
    },
    "compra_solicitud_cotizacion": {
        "subject": """{{ object.company_id.name }} - Solicitud de cotización {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Estimado&nbsp;<t t-out="object.partner_id.name or ''">NombreProveedor</t>.
        <br/><br/>
        Le adjuntamos una solicitud de cotización
        <span style="font-weight: bold;" t-out="object.name or ''">P00015</span>
        <t t-if="object.partner_ref">
            (con referencia: <t t-out="object.partner_ref or ''"></t>)
        </t>
        de <t t-out="object.company_id.name or ''">NuestraEmpresa</t>.
    </p>

    <div><br/></div>

    <div>
        Por favor, no dude en contactarnos si tiene alguna consulta sobre esta transacción.
        <br/><br/>
        Saludos cordiales.
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "compra_orden_confirmada": {
        "subject": """{{ object.company_id.name }} - Orden de compra {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Estimado&nbsp;<t t-out="object.partner_id.name or ''">NombreProveedor</t>.
        <br/><br/>
        Le adjuntamos la orden de compra
        <span style="font-weight: bold;" t-out="object.name or ''">P00015</span>
        <t t-if="object.partner_ref">
            (con referencia: <t t-out="object.partner_ref or ''"></t>)
        </t>
        por un total de
        <span style="font-weight: bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 1000.00</span>
        de <t t-out="object.company_id.name or ''">NuestraEmpresa</t>.
        <t t-if="object.date_planned">
            <br/><br/>
            La recepción está prevista para el <span style="font-weight: bold;" t-out="format_date(object.date_planned) or ''">05/05/2025</span>.
            ¿Podría confirmarnos la recepción de esta orden?
        </t>
    </p>
    <t t-if="object.date_planned">
        <div style="text-align: center; padding: 8px 0;">
            <a t-att-href="object.get_acknowledge_url()" target="_blank" style="padding: 8px 16px; color: #FFFFFF; text-decoration: none; background-color: #714B67; border-radius: 4px; font-size: 13px;">Confirmar recepción</a>
        </div>
    </t>
    <div><br/></div>

    <div>
        Por favor, no dude en contactarnos si tiene alguna consulta sobre esta transacción.
        <br/><br/>
        Saludos cordiales.
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "compra_recordatorio": {
        "subject": """{{ object.company_id.name }} - Recordatorio de entrega {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Estimado&nbsp;<t t-out="object.partner_id.name or ''">NombreProveedor</t>.
        <br/><br/>
        Le recordamos que la entrega de la orden de compra
        <span style="font-weight: bold;" t-out="object.name or ''">P00015</span>
        <t t-if="object.partner_ref">
            (con referencia: <t t-out="object.partner_ref or ''"></t>)
        </t>
        está prevista para el
        <t t-if="object.date_planned">
            <span style="font-weight: bold;" t-out="format_date(object.date_planned) or ''">05/05/2025</span>.
        </t>
        <t t-else="">
            <span style="font-weight: bold;">fecha a confirmar</span>.
        </t>
        ¿Podría confirmarnos que se entregará en término?
    </p>
    <div style="text-align: center; padding: 8px 0;">
        <a t-att-href="object.get_acknowledge_url()" target="_blank" style="padding: 8px 16px; color: #FFFFFF; text-decoration: none; background-color: #714B67; border-radius: 4px; font-size: 13px;">Confirmar entrega</a>
    </div>
    <div><br/></div>

    <div>
        Por favor, no dude en contactarnos si tiene alguna consulta sobre esta transacción.
        <br/><br/>
        Saludos cordiales.
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "autofactura": {
        "subject": """{{ object.company_id.name }} - Autofactura {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Estimado&nbsp;<t t-out="object.partner_id.name or ''">NombreProveedor</t>.
        <br/><br/>
        Le enviamos la autofactura
        <span style="font-weight: bold;" t-out="(object.name or '').replace('/', '-') or ''">FA-A00001-00000001</span>
        <t t-if="object.invoice_origin">
            (con referencia: <t t-out="object.invoice_origin or ''"></t>)
        </t>
        por un total de
        <span style="font-weight: bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 1000.00</span>.
    </p>

    <div><br/></div>

    <div>
        Por favor, no dude en contactarnos si tiene alguna consulta sobre esta transacción.
        <br/><br/>
        Saludos cordiales.
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "autofactura_nota_credito": {
        "subject": """{{ object.company_id.name }} - Autofactura, nota de crédito {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Estimado&nbsp;<t t-out="object.partner_id.name or ''">NombreProveedor</t>.
        <br/><br/>
        Le enviamos la siguiente nota de crédito de autofactura
        <span style="font-weight: bold;" t-out="object.name or ''">RINV/2025/05/0001</span>
        <t t-if="object.invoice_origin">
            (con referencia: <t t-out="object.invoice_origin or ''"></t>)
        </t>
        por un total de
        <span style="font-weight: bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 1000.00</span>.
    </p>

    <div><br/></div>

    <div>
        Por favor, no dude en contactarnos si tiene alguna consulta sobre esta transacción.
        <br/><br/>
        Saludos cordiales.
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "factura_proforma": {
        "subject": """{{ object.company_id.name }} - {{ object.state in ('draft', 'sent') and 'Proforma' or 'Orden' }} {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Estimado&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>
        Le enviamos la factura proforma de
        <t t-out="'cotización' if object.state in ('draft', 'sent') else 'orden'">cotización</t>
        <span style="font-weight: bold;" t-out="object.name or ''">S00052</span>
        <t t-if="object.origin">
            (con referencia: <t t-out="object.origin or ''"></t>)
        </t>
        por un total de
        <span style="font-weight: bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 10.00</span>.
    </p>

    <div><br/></div>

    <div>
        Por favor, no dude en contactarnos si tiene alguna consulta sobre esta transacción.
        <br/><br/>
        Saludos cordiales.
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "helpdesk_ticket_recibido": {
        "subject": """{{ object.name }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Estimado&nbsp;<t t-out="object.sudo().partner_id.name or object.sudo().partner_name or 'Sr./Sra.'">NombreCliente</t>.
        <br/><br/>
        Recibimos su solicitud
        <t t-if="hasattr(object.team_id, 'website_id') and object.get_portal_url()">
            <a t-attf-href="{{ object.team_id.website_id.domain }}/my/ticket/{{ object.id }}/{{ object.access_token }}" t-out="object.name or ''">Título del ticket</a>
        </t>
        y está siendo revisada por nuestro equipo de <t t-out="object.team_id.name or ''">Soporte</t>.
        La referencia de su ticket es <strong><t t-out="object.ticket_ref or ''">15</t></strong>.
        <br/><br/>
        Para agregar información adicional, simplemente responda este email.
    </p>

    <div style="text-align: center; padding: 16px 0px 16px 0px;">
        <t t-if="hasattr(object.team_id, 'website_id') and object.team_id.use_website_helpdesk_form">
            <a t-attf-style="background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px; font-size: 13px;" t-att-href="'%s%s' % (object.team_id.website_id.domain or '', object.get_portal_url())" target="_blank">Ver ticket</a>
        </t>
        <t t-else="">
            <a t-attf-style="background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px; font-size: 13px;" t-att-href="object.get_portal_url()" target="_blank">Ver ticket</a>
        </t>
        <t t-if="hasattr(object.team_id, 'website_id') and object.team_id.allow_portal_ticket_closing">
            <a t-attf-style="background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px; font-size: 13px;" t-att-href="'%s/my/ticket/close/%s/%s' % (object.team_id.website_id.domain or '', object.id, object.access_token)" target="_blank">Cerrar ticket</a>
        </t>
        <t t-elif="object.team_id.allow_portal_ticket_closing">
            <a t-attf-style="background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px; font-size: 13px;" t-att-href="'/my/ticket/close/%s/%s' % (object.id, object.access_token)" target="_blank">Cerrar ticket</a>
        </t>
    </div>

    <div><br/></div>

    <div>
        Por favor, no dude en contactarnos si tiene alguna consulta.
        <br/><br/>
        Saludos cordiales.
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "helpdesk_ticket_cerrado": {
        "subject": """Ticket cerrado - Referencia {{ object.id if object.id else 15 }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Estimado&nbsp;<t t-out="object.sudo().partner_id.name or 'Sr./Sra.'">NombreCliente</t>.
        <br/><br/>
        Le informamos que hemos cerrado su ticket (referencia
        <t t-out="object.id or ''">15</t>).
        Esperamos que el servicio brindado haya cumplido sus expectativas.
        <br/><br/>
        Si tiene alguna consulta adicional, no dude en responder este email para reabrir su ticket.
    </p>

    <div><br/></div>

    <div>
        Por favor, no dude en contactarnos si tiene alguna consulta sobre esta transacción.
        <br/><br/>
        Saludos cordiales.
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "helpdesk_encuesta_satisfaccion": {
        "subject": """{{ object.company_id.name or object.user_id.company_id.name or 'Soporte' }}: Encuesta de satisfacción""",
        "body_html": """<div>
    <t t-set="access_token" t-value="object._rating_get_access_token()"/>
    <t t-set="partner" t-value="object._rating_get_partner()"/>
    <table border="0" cellpadding="0" cellspacing="0" style="width:100%; margin:0;">
    <tbody>
        <tr><td valign="top" style="font-size: 14px;">
            <t t-if="partner.name">
                Estimado&nbsp;<t t-out="partner.name or ''">NombreCliente</t>,<br/><br/>
            </t>
            <t t-else="">
                Estimado&nbsp;cliente,<br/><br/>
            </t>
            Le pedimos un momento para calificar nuestro servicio en el ticket "<strong t-out="object.name or ''">Título del ticket</strong>"
            <t t-if="object._rating_get_operator().name">
                atendido por <strong t-out="object._rating_get_operator().name or ''">Nombre Apellido</strong>.<br/>
            </t>
            <t t-else="">
                .<br/><br/>
            </t>
        </td></tr>
        <tr><td style="text-align: center;">
            <table border="0" cellpadding="0" cellspacing="0" style="width:100%; margin: 32px 0px 32px 0px; display: inline-table;">
                <tr><td style="font-size: 14px; text-align:center;">
                    <strong>Cuéntenos cómo se sintió con nuestro servicio</strong><br/>
                    <span style="text-color: #888888">(haga clic en una de estas caritas)</span>
                </td></tr>
                <tr><td style="font-size: 14px;">
                    <table style="width:100%;text-align:center;margin-top:2rem;">
                        <tr>
                            <td>
                                <a t-attf-href="/rate/{{ access_token }}/5" t-att-class="'pe-none' if object._rating_get_operator() else ''">
                                    <img alt="Contento" src="/rating/static/src/img/rating_5.png" title="Contento"/>
                                </a>
                            </td>
                            <td>
                                <a t-attf-href="/rate/{{ access_token }}/3" t-att-class="'pe-none' if object._rating_get_operator() else ''">
                                    <img alt="Neutral" src="/rating/static/src/img/rating_3.png" title="Neutral"/>
                                </a>
                            </td>
                            <td>
                                <a t-attf-href="/rate/{{ access_token }}/1" t-att-class="'pe-none' if object._rating_get_operator() else ''">
                                    <img alt="Descontento" src="/rating/static/src/img/rating_1.png" title="Descontento"/>
                                </a>
                            </td>
                        </tr>
                    </table>
                </td></tr>
            </table>
        </td></tr>
        <tr><td valign="top" style="font-size: 14px;">
            Agradecemos su opinión, nos ayuda a mejorar continuamente.
            <br/><br/><span style="margin: 0px 0px 0px 0px; font-size: 12px; opacity: 0.5; color: #454748;">Esta encuesta se envió porque su ticket pasó a la etapa <b t-out="object.stage_id.name or ''">En curso</b>.</span>
        </td></tr>
    </tbody>
    </table>
</div>""",
    },
    "usuario_invitacion": {
        "subject": """{{ object.create_uid.name }} de {{ object.company_id.name }} lo invita a conectarse a Odoo""",
        "body_html": """<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">
<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
<tbody>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="middle">
                    <span style="font-size: 10px;">Bienvenido a Odoo</span><br/>
                    <span style="font-size: 20px; font-weight: bold;">
                        <t t-out="object.name or ''">Marc Demo</t>
                    </span>
                </td><td valign="middle" align="right" t-if="not object.company_id.uses_default_logo">
                    <img t-attf-src="/logo.png?company={{ object.company_id.id }}" style="padding: 0px; margin: 0px; height: auto; width: 80px;" t-att-alt="object.company_id.name"/>
                </td></tr>
                <tr><td colspan="2" style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="top" style="font-size: 13px;">
                    <div>
                        Estimado/a <t t-out="object.name or ''">Marc Demo</t>,<br /><br />
                        Ha sido invitado/a por <t t-out="object.create_uid.name or ''">OdooBot</t> de <t t-out="object.company_id.name or ''">SuEmpresa</t> a conectarse a Odoo.
                        <div style="margin: 16px 0px 16px 0px;">
                            <a t-att-href="object.partner_id._get_signup_url()"
                                t-attf-style="background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px; font-size:13px;">
                                Aceptar invitación
                            </a>
                        </div>
                        <b>Este enlace será válido durante <t t-out="int(int(object.env['ir.config_parameter'].sudo().get_param('auth_signup.signup.validity.hours',144))/24)"></t> días</b> <br/>
                        <t t-set="website_url" t-value="object.get_base_url()"></t>
                        Su dominio de Odoo es: <b><a t-att-href='website_url' t-out="website_url or ''">http://suempresa.odoo.com</a></b><br />
                        Su email de acceso es: <b><a t-attf-href="/web/login?login={{ object.email }}" target="_blank" t-out="object.email or ''">nombre@ejemplo.com</a></b><br /><br />
                        Ante cualquier consulta, no dude en contactarnos.
                        <br /><br />
                        Saludos cordiales,<br />
                        --<br/>El equipo de <t t-out="object.company_id.name or ''">SuEmpresa</t>
                    </div>
                </td></tr>
                <tr><td style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="middle" align="left">
                    <t t-out="object.company_id.name or ''">SuEmpresa</t>
                </td></tr>
                <tr><td valign="middle" align="left" style="opacity: 0.7;">
                    <t t-out="object.company_id.phone or ''">+54 11 1234-5678</t>
                    <t t-if="object.company_id.email">
                        | <a t-att-href="'mailto:%s' % object.company_id.email" style="text-decoration:none; color: #454748;" t-out="object.company_id.email or ''">info@suempresa.com</a>
                    </t>
                    <t t-if="object.company_id.website">
                        | <a t-att-href="'%s' % object.company_id.website" style="text-decoration:none; color: #454748;" t-out="object.company_id.website or ''">http://www.ejemplo.com</a>
                    </t>
                </td></tr>
            </table>
        </td>
    </tr>
</tbody>
</table>
</td></tr>
<tr><td align="center" style="min-width: 590px;">
    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
      <tr><td style="text-align: center; font-size: 13px;">
        Desarrollado por <a target="_blank" href="https://www.odoo.com?utm_source=db&amp;utm_medium=auth" t-attf-style="color: {{object.company_id.email_secondary_color or '#875A7B'}};">Odoo</a>
      </td></tr>
    </table>
</td></tr>
</table>""",
    },
    "usuario_recordatorio_pendiente": {
        "subject": """Recordatorio de usuarios sin registrar""",
        "body_html": """<table border="0" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">
<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
<tbody>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <t t-set="invited_users" t-value="ctx.get('invited_users', [])" />
                <td style="text-align : left">
                    <span style="font-size: 20px; font-weight: bold;">
                        Invitaciones pendientes
                    </span><br/><br/>
                </td>
                <tr><td valign="top" style="font-size: 13px;">
                    <div>
                        Estimado/a <t t-out="object.name or ''">Mitchell Admin</t>,<br/> <br/>
                        Agregó a la base de datos los siguientes usuarios, pero todavía no se registraron:
                        <ul>
                            <t t-foreach="invited_users" t-as="invited_user">
                                <li t-out="invited_user or ''">demo@ejemplo.com</li>
                            </t>
                        </ul>
                        Le sugerimos hacer un seguimiento para que puedan acceder a la base de datos y empezar a trabajar.
                        <br /><br/>
                        Saludos cordiales,<br />
                        --<br/>El equipo de <t t-out="object.company_id.name or ''">SuEmpresa</t>
                    </div>
                </td></tr>
                <tr><td style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
</tbody>
</table>
</td></tr>
</table>""",
    },
    "usuario_cuenta_creada": {
        "subject": """¡Bienvenido a {{ object.company_id.name }}!""",
        "body_html": """<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">
<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
<tbody>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="middle">
                    <span style="font-size: 10px;">Su cuenta</span><br/>
                    <span style="font-size: 20px; font-weight: bold;">
                        <t t-out="object.name or ''">Marc Demo</t>
                    </span>
                </td><td valign="middle" align="right" t-if="not object.company_id.uses_default_logo">
                    <img t-attf-src="/logo.png?company={{ object.company_id.id }}" style="padding: 0px; margin: 0px; height: auto; width: 80px;" t-att-alt="object.company_id.name"/>
                </td></tr>
                <tr><td colspan="2" style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="top" style="font-size: 13px;">
                    <div>
                        Estimado/a <t t-out="object.name or ''">Marc Demo</t>,<br/><br/>
                        ¡Su cuenta fue creada con éxito!<br/>
                        Su usuario de acceso es <strong><t t-out="object.email or ''">nombre@ejemplo.com</t></strong><br/>
                        Para acceder a su cuenta, puede usar el siguiente enlace:
                        <div style="margin: 16px 0px 16px 0px;">
                            <a t-attf-href="/web/login?auth_login={{object.email}}"
                                t-attf-style="background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px; font-size:13px;">
                                Ir a mi cuenta
                            </a>
                        </div>
                        Gracias,<br/>
                        <t t-if="user.signature">
                            <br/>
                            <div>--<br/><t t-out="user.signature or ''">Mitchell Admin</t></div>
                        </t>
                    </div>
                </td></tr>
                <tr><td style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="middle" align="left">
                    <t t-out="object.company_id.name or ''">SuEmpresa</t>
                </td></tr>
                <tr><td valign="middle" align="left" style="opacity: 0.7;">
                    <t t-out="object.company_id.phone or ''">+54 11 1234-5678</t>
                    <t t-if="object.company_id.email">
                        | <a t-attf-href="mailto:{{object.company_id.email}}" style="text-decoration:none; color: #454748;" t-out="object.company_id.email or ''">info@suempresa.com</a>
                    </t>
                    <t t-if="object.company_id.website">
                        | <a t-att-href="object.company_id.website" style="text-decoration:none; color: #454748;" t-out="object.company_id.website or ''">http://www.ejemplo.com</a>
                    </t>
                </td></tr>
            </table>
        </td>
    </tr>
</tbody>
</table>
</td></tr>
<tr><td align="center" style="min-width: 590px;">
    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
      <tr><td style="text-align: center; font-size: 13px;">
        Desarrollado por <a target="_blank" href="https://www.odoo.com?utm_source=db&amp;utm_medium=auth" t-attf-style="color: {{object.company_id.email_secondary_color or '#875A7B'}};">Odoo</a>
      </td></tr>
    </table>
</td></tr>
</table>""",
    },
    "portal_invitacion": {
        "subject": """Su cuenta en {{ object.company_id.name }}""",
        "body_html": """<table border="0" cellpadding="0" cellspacing="0"
    style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
    <tr><td align="center">
        <table border="0" cellpadding="0" cellspacing="0" width="590"
            style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">
            <tbody>
                <tr>
                    <td align="center" style="min-width: 590px;">
                        <table border="0" cellpadding="0" cellspacing="0" width="590"
                            style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                            <tr>
                                <td valign="middle">
                                    <span style="font-size: 10px;">Su cuenta</span><br/>
                                    <span style="font-size: 20px; font-weight: bold;" t-out="object.name or ''">Marc Demo</span>
                                </td>
                                <td valign="middle" align="right" t-if="not object.company_id.uses_default_logo">
                                    <img t-attf-src="/logo.png?company={{ object.company_id.id }}" style="padding: 0px; margin: 0px; height: auto; width: 80px;"
                                        t-att-alt="object.company_id.name"/>
                                </td>
                            </tr>
                            <tr><td colspan="2" style="text-align:center;">
                                <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin:16px 0px 16px 0px;"/>
                            </td></tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td align="center" style="min-width: 590px;">
                        <table border="0" cellpadding="0" cellspacing="0" width="590"
                            style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                            <tr><td valign="top" style="font-size: 13px;">
                                <div>
                                    Estimado/a <t t-out="object.name or ''">Marc Demo</t>,<br/> <br/>
                                    ¡Bienvenido/a al Portal de <t t-out="object.company_id.name">SuEmpresa</t>!<br/><br/>
                                    Se creó una cuenta a su nombre con el siguiente usuario: <t t-out="object.login">demo</t><br/><br/>
                                    Haga clic en el botón de abajo para elegir una contraseña y activar su cuenta.
                                    <div style="margin: 16px 0px 16px 0px; text-align: center;">
                                        <a t-att-href="object.partner_id._get_signup_url()"
                                        t-attf-style="display: inline-block; padding: 10px; text-decoration: none; font-size: 12px; background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px;">
                                            <strong>Activar cuenta</strong>
                                        </a>
                                    </div>
                                    <t t-out="ctx.get('welcome_message') or ''">Bienvenido/a al portal de nuestra empresa.</t>
                                </div>
                            </td></tr>
                            <tr><td style="text-align:center;">
                                <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                            </td></tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td align="center" style="min-width: 590px;">
                        <table border="0" cellpadding="0" cellspacing="0" width="590"
                            style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">
                            <tr><td valign="middle" align="left">
                                <t t-out="object.company_id.name or ''">SuEmpresa</t>
                            </td></tr>
                            <tr><td valign="middle" align="left" style="opacity: 0.7;">
                                <t t-out="object.company_id.phone or ''">+54 11 1234-5678</t>
                                <t t-if="object.company_id.email">
                                    | <a t-attf-href="mailto:{{ object.company_id.email }}" style="text-decoration: none; color: #454748;" t-out="object.company_id.email or ''">info@suempresa.com</a>
                                </t>
                                <t t-if="object.company_id.website">
                                    | <a t-att-href="object.company_id.website" style="text-decoration: none; color: #454748;" t-out="object.company_id.website or ''">http://www.ejemplo.com</a>
                                </t>
                            </td></tr>
                        </table>
                    </td>
                </tr>
            </tbody>
        </table>
    </td></tr>
    <tr><td align="center" style="min-width: 590px;">
        <table border="0" cellpadding="0" cellspacing="0" width="590"
            style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
            <tr><td style="text-align: center; font-size: 13px;">
                Desarrollado por <a target="_blank" t-attf-href="https://www.odoo.com?utm_source=db&amp;utm_medium={{ ctx.get('medium', 'auth') }}" t-attf-style="color: {{object.company_id.email_secondary_color or '#875A7B'}};">Odoo</a>
            </td></tr>
        </table>
    </td></tr>
</table>""",
    },
    "usuario_invitacion_2fa": {
        "subject": """Invitación para activar la autenticación en dos pasos en su cuenta de Odoo""",
        "body_html": """<div style="margin: 0px; padding: 0px; font-size: 13px;">
    <p style="margin: 0px; padding: 0px; font-size: 13px;">
        Estimado/a <t t-out="object.partner_id.name or ''"></t>,<br/><br/>
        <t t-out="user.name or ''"></t> le solicitó activar la autenticación en dos pasos para proteger su cuenta.<br/><br/>
        La autenticación en dos pasos ("2FA") es un sistema de doble verificación.
        La primera se realiza con su contraseña y la segunda con un código que obtiene desde una aplicación móvil dedicada.
        Algunas de las más usadas son Authy, Google Authenticator o Microsoft Authenticator.

        <p style="margin: 16px 0px 16px 0px; text-align: center;">
            <a t-att-href="object.get_totp_invite_url()"
                t-attf-style="background-color:{{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px;">
                Activar mi autenticación en dos pasos
            </a>
        </p>
    </p>
</div>""",
    },
}

INFORMAL_CONTENT = {
    "factura": {
        "subject": """{{ object.company_id.name }} - {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Hola&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>

        Te enviamos el comprobante 
        <span style="font-weight: bold;" t-out="(object.name or '').replace('/', '-') or ''">FA-A00001-00000001</span>
        por un importe total de 
        <span style="font-weight: bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 1000.00</span>.
    </p>

    <div><br/></div>

    <div>
        Por favor, no dudes en contactarnos si tenés alguna consulta sobre esta transacción.
        <br/><br/>
        ¡Saludos!
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div><div>
    <br/></div>

    <div>
  <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
</div>
        <div><br/></div>
    </div>""",
    },
    "notas_credito": {
        "subject": """{{ object.company_id.name }} - Nota de crédito {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Hola&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>

        Te enviamos la siguiente 
        <t t-if="object.name">
            nota de crédito <span style="font-weight:bold;" t-out="object.name or ''">RINV/2021/05/0001</span>
        </t>
        <t t-else="">
            nota de crédito
        </t>
        <t t-if="object.reversed_entry_id">
            (con referencia: <t t-out="object.reversed_entry_id.name or ''"></t>)
        </t>
        <t t-elif="object.invoice_origin">
            (con referencia: <t t-out="object.invoice_origin or ''"></t>)
        </t>
        por un importe total de 
        <span style="font-weight:bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">
            $143,750.00
        </span>.
        <br/><br/>
    </p>

    <div>
        Por favor, no dudes en contactarnos si tenés alguna consulta sobre esta transacción.
        <br/><br/>
        ¡Saludos!
    </div> 

<div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div><div>
    <br/></div>

    <div>
  <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
</div>
        <div><br/></div>
    </div>""",
    },
    "pagos": {
        "subject": """{{ object.company_id.name }} - {{ 'Recibo' if object.payment_type == 'inbound' else 'Orden de pago' }} {{ object.name }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-radius:0px; border-style:none; box-sizing:border-box;&#10;              border-width:0px; margin: 0px; padding: 0px; font-size: 13px;">
        Hola&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>

        <t t-if="object.payment_type == 'inbound'">
            Te enviamos el recibo de cobranza 
            <span style="font-weight:bold;" t-out="(object.name or '').replace('/','-') or ''">RE00001-00000001</span>
            por un importe total de 
            <span style="font-weight:bold;" t-out="format_amount(object.amount, object.currency_id) or ''">$ 1000.00</span>.
        </t>

        <t t-if="object.payment_type == 'outbound'">
            Te enviamos la orden de pago 
            <span style="font-weight:bold;" t-out="(object.name or '').replace('/','-') or ''">P00001-00000001</span>
            por un importe total de 
            <span style="font-weight:bold;" t-out="format_amount(object.amount, object.currency_id) or ''">$ 1000.00</span>.
        </t>
    </p>

    <div><br/></div>

    <div>
        Por favor, no dudes en contactarnos si tenés alguna consulta sobre esta transacción.
        <br/><br/>
        ¡Saludos!
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div><div>
    <br/></div>

    <div>
  <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
</div>
        <div><br/></div>
    </div>""",
    },
    "cotizacion_orden_venta": {
        "subject": """{{ object.company_id.name }} - {{ object.state in ('draft', 'sent') and (ctx.get('proforma') and 'Proforma' or 'Cotización') or 'Orden' }} {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border-radius:0px; border-style:none; box-sizing:border-box;&#10;              border-width:0px; margin: 0px; padding: 0px; font-size: 13px;">

        <t t-set="doc_name" t-value="'cotización' if object.state in ('draft', 'sent') else 'orden'"></t>

        Hola&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>

        <t t-if="ctx.get('proforma')">
            Te enviamos la factura proforma invoice para la 
            <t t-out="doc_name or ''">cotización</t> 
            <span style="font-weight: bold;" t-out="object.name or ''">S00052</span>
            <t t-if="object.origin">
                (con referencia: <t t-out="object.origin or ''"></t>)
            </t>
            por un importe total de 
            <span style="font-weight: bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$10.00</span>.
        </t>

        <t t-else="">
            <t t-set="is_quotation" t-value="object.state in ('draft', 'sent')"></t>

            <t t-if="is_quotation">
                Te enviamos la cotización 
                <span t-att-style="'font-weight: bold;'">
                    <t t-esc="object.name or ''"></t>
                </span>
                <t t-if="object.origin">
                    (con referencia: <t t-esc="object.origin or ''"></t>)
                </t>
                por un importe total de 
                <span t-att-style="'font-weight: bold;'">
                    <t t-esc="format_amount(object.amount_total, object.currency_id) or ''"></t>
                </span>.
            </t>

            <t t-else="">
                Registramos tu orden 
                <span t-att-style="'font-weight: bold;'">
                    <t t-esc="object.name or ''"></t>
                </span>
                <t t-if="object.origin">
                    (con referencia: <t t-esc="object.origin or ''"></t>)
                </t>
                por un importe total de 
                <span t-att-style="'font-weight: bold;'">
                    <t t-esc="format_amount(object.amount_total, object.currency_id) or ''"></t>
                </span>.
            </t>
        </t>

        <br/>

        <t t-set="documents" t-value="object._get_product_documents()"></t>

        <t t-if="documents">
            <br/>
            <t t-if="len(documents) &gt; 1">
                Aquí hay algunos documentos adicionales que podrían interesarte:
            </t>
            <t t-else="">
                Aquí hay otro documento que podría interesarte:
            </t>

            <ul style="border-radius:0px; border-style:none; padding:0 0 0 32px; margin:0px 0 0px 0;&#10;                       box-sizing:border-box; border-width:0px; list-style-type:disc; margin-bottom: 0;">
                <t t-foreach="documents" t-as="document">
                    <li style="font-size: 13px;">
                        <a t-out="document.ir_attachment_id.name" t-att-href="object.get_portal_url('/document/' + str(document.id))" t-att-target="target" style="color: #374151; text-decoration: none; border: none;">
                        </a>
                    </li>
                </t>
            </ul>
        </t>

        <br/>

        </p><div>
            Por favor, no dudes en contactarnos si tenés alguna consulta sobre esta transacción.
            <br/><br/>
            ¡Saludos!
        </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div><div>
    <br/></div>

    <div>
  <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
</div>
        <div><br/></div>
    </div>""",
    },
    "orden_venta_confirmada": {
        "subject": """{{ object.company_id.name }} - {{ (object.get_portal_last_transaction().state == 'pending') and 'Orden pendiente' or 'Orden' }} {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border-radius:0px; border-style:none; box-sizing:border-box;&#10;              border-width:0px; margin: 0px; padding: 0px; font-size: 13px;">
        Hola&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>
        <t t-set="tx_sudo" t-value="object.get_portal_last_transaction()"></t>
        Tu orden <span style="font-weight:bold;" t-out="object.name or ''">S00049</span> por un importe total de <span style="font-weight:bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 10.00</span>
        <t t-if="object.state == 'sale' or (tx_sudo and tx_sudo.state in ('done', 'authorized'))">
            quedó confirmada.<br/>
         </t>
        <t t-elif="tx_sudo and tx_sudo.state == 'pending'">
            está pendiente. Se confirmará cuando recibamos tu pago.
            <t t-if="object.reference">
                La referencia de pago es <span style="font-weight:bold;" t-out="object.reference or ''"></span>.
            </t>
        </t>
        <br/>
        <t t-set="documents" t-value="object._get_product_documents()"></t>
        <t t-if="documents">
            <br/> 
            <t t-if="len(documents)&gt;1">
                A continuación encontrarás algunos documentos adicionales que podrían interesarte:
            </t>
            <t t-else="">
                A continuación encontrarás otro documento que podría interesarte:
            </t>
            </t></p><ul style="margin-bottom: 0;">
                <t t-foreach="documents" t-as="document">
                    <li style="font-size: 13px;">
                        <a t-out="document.ir_attachment_id.name" t-att-href="object.get_portal_url('/document/' + str(document.id))" t-att-target="target"></a>
                    </li>
                </t>
            </ul>
        
        <div>
            Por favor, no dudes en contactarnos si tenés alguna consulta sobre esta transacción.
            <br/><br/>
            ¡Saludos!
        </div>
            <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div><div>
    <br/></div>

    <div>
  <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
</div>
        <div><br/></div>
    </div>
<t t-if="hasattr(object, 'website_id') and object.website_id">
    <div style="margin: 0px; padding: 0px;">
        <table width="100%" style="color: #454748; font-size: 12px; border-collapse: collapse; white-space: nowrap;">
            <tbody><tr style="border-bottom: 2px solid #dee2e6;">
                <td style="width: 150px;"><span style="font-weight:bold;">Productos</span></td>
                <td>
                </td><td width="15%" align="center"><span style="font-weight:bold;">Cantidad</span></td>
                <td width="20%" align="right">
                    <span style="font-weight:bold;">
                        <t t-if="object.website_id.show_line_subtotals_tax_selection == 'tax_excluded'">
                            Sin IVA
                        </t>
                        <t t-else="">
                            Con IVA
                        </t>
                    </span>
                </td>
            </tr>
        </tbody></table>
        <t t-set="current_subtotal" t-value="0"></t>
        <t t-foreach="object.order_line" t-as="line">
            <t t-set="line_subtotal" t-value="                     line.price_subtotal                     if object.website_id.show_line_subtotals_tax_selection == 'tax_excluded'                     else line.price_total                 "></t>
            <t t-set="current_subtotal" t-value="current_subtotal + line_subtotal"></t>
            <t t-if="(not hasattr(line, 'is_delivery') or not line.is_delivery) and (                     line.display_type in ['line_section', 'line_note']                     or line.product_type == 'combo'                 )">
                <t t-set="loop_cycle_number" t-value="loop_cycle_number or 0"></t><t t-set="loop_cycle_number" t-value="loop_cycle_number + 1"></t><table width="100%" style="color: #454748; font-size: 12px; border-collapse: collapse;">
                    
                    <tbody><tr t-att-style="'background-color: #f2f2f2' if loop_cycle_number % 2 == 0 else 'background-color: #ffffff'">
                        
                        <td colspan="4">
                            <t t-if="line.display_type == 'line_section' or line.product_type == 'combo'">
                                <span style="font-weight:bold;" t-out="line.name or ''">Curso sobre el cuidado de los árboles</span>
                                <t t-set="current_section" t-value="line"></t>
                                <t t-set="current_subtotal" t-value="0"></t>
                            </t>
                            <t t-elif="line.display_type == 'line_note'">
                                <i t-out="line.name or ''">Curso sobre el cuidado de los árboles</i>
                            </t>
                        </td>
                    </tr>
                </tbody></table>
            </t>
            <t t-elif="(not hasattr(line, 'is_delivery') or not line.is_delivery)">
                <t t-set="loop_cycle_number" t-value="loop_cycle_number or 0"></t><t t-set="loop_cycle_number" t-value="loop_cycle_number + 1"></t><table width="100%" style="color: #454748; font-size: 12px; border-collapse: collapse;">
                    
                    <tbody><tr t-att-style="'background-color: #f2f2f2' if loop_cycle_number % 2 == 0 else 'background-color: #ffffff'">
                        
                        <td style="width: 150px;">
                            <img t-attf-src="/web/image/product.product/{{ line.product_id.id }}/image_128" style="width: 64px; height: 64px; object-fit: contain;" alt="Product image"/>
                        </td>
                        <td align="left" t-out="line.product_id.name or ''">	Curso sobre el cuidado de los árboles</td>
                        <td width="15%" align="center" t-out="line.product_uom_qty or ''">1</td>
                        <td width="20%" align="right"><span style="font-weight:bold; white-space: nowrap;">
                        <t t-if="object.website_id.show_line_subtotals_tax_selection == 'tax_excluded'">
                            <t t-out="format_amount(line.price_reduce_taxexcl, object.currency_id) or ''">$ 10.00</t>
                        </t>
                        <t t-else="">
                            <t t-out="format_amount(line.price_reduce_taxinc, object.currency_id) or ''">$ 10.00</t>
                        </t>
                        </span></td>
                    </tr>
                </tbody></table>
            </t>
            <t t-if="current_section and (                     line_last                     or object.order_line[line_index+1].display_type == 'line_section'                     or object.order_line[line_index+1].product_type == 'combo'                     or (                         line.combo_item_id                         and not object.order_line[line_index+1].combo_item_id                     )                 ) and not line.is_downpayment">
                <t t-set="current_section" t-value="None"></t>
                <t t-set="loop_cycle_number" t-value="loop_cycle_number or 0"></t><t t-set="loop_cycle_number" t-value="loop_cycle_number + 1"></t><table width="100%" style="color: #454748; font-size: 12px; border-collapse: collapse;">
                    
                    <tbody><tr t-att-style="'background-color: #f2f2f2' if loop_cycle_number % 2 == 0 else 'background-color: #ffffff'">
                        
                        <td style="width: 100%" align="right">
                            <span style="font-weight: bold;">Subtotal:</span>
                            <span t-out="format_amount(current_subtotal, object.currency_id) or ''">$ 10.00</span>
                        </td>
                    </tr>
                </tbody></table>
            </t>
        </t>
    </div>
    <div style="margin: 0px; padding: 0px;" t-if="hasattr(object, 'carrier_id') and object.carrier_id">
        <table width="100%" style="color: #454748; font-size: 12px; border-spacing: 0px 4px; white-space: nowrap;" align="right">
            <tbody><tr>
                <td style="width: 60%">
                </td><td style="width: 30%; border-top: 1px solid #dee2e6;" align="right"><span style="font-weight:bold;">Entrega:</span></td>
                <td style="width: 10%; border-top: 1px solid #dee2e6;" align="right" t-out="format_amount(object.amount_delivery, object.currency_id) or ''">$ 0.00</td>
            </tr>
            <tr>
                <td style="width: 60%">
                </td><td style="width: 30%;" align="right"><span style="font-weight:bold;">Subtotal:</span></td>
                <td style="width: 10%;" align="right" t-out="format_amount(object.amount_untaxed, object.currency_id) or ''">$ 10.00</td>
            </tr>
        </tbody></table>
    </div>
    <div style="margin: 0px; padding: 0px;" t-else="">
        <table width="100%" style="color: #454748; font-size: 12px; border-spacing: 0px 4px; white-space: nowrap;" align="right">
            <tbody><tr>
                <td style="width: 60%">
                </td><td style="width: 30%; border-top: 1px solid #dee2e6;" align="right"><span style="font-weight:bold;">Subtotal:</span></td>
                <td style="width: 10%; border-top: 1px solid #dee2e6;" align="right" t-out="format_amount(object.amount_untaxed, object.currency_id) or ''">$ 10.00</td>
            </tr>
        </tbody></table>
    </div>
    <div style="margin: 0px; padding: 0px;">
        <table width="100%" style="color: #454748; font-size: 12px; border-spacing: 0px 4px; white-space: nowrap;" align="right">
            <tbody><tr>
                <td style="width: 60%">
                </td><td style="width: 30%;" align="right"><span style="font-weight:bold;">Impuestos:</span></td>
                <td style="width: 10%;" align="right" t-out="format_amount(object.amount_tax, object.currency_id) or ''">$ 0.00</td>
            </tr>
            <tr>
                <td style="width: 60%">
                </td><td style="width: 30%; border-top: 1px solid #dee2e6;" align="right"><span style="font-weight:bold;">Total:</span></td>
                <td style="width: 10%; border-top: 1px solid #dee2e6;" align="right" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 10.00</td>
            </tr>
        </tbody></table>
    </div>
    <div t-if="object.partner_invoice_id" style="margin: 0px; padding: 0px;">
        <table width="100%" style="color: #454748; font-size: 12px;">
            <tbody><tr>
                <td style="padding-top: 10px;">
                    <span style="font-weight:bold;">Dirección de facturación:</span>
                    <t t-out="object.partner_invoice_id.street or ''">1201 S Figueroa St</t>
                    <t t-out="object.partner_invoice_id.city or ''">Los Angeles</t>
                    <t t-out="object.partner_invoice_id.state_id.name or ''">California</t>
                    <t t-out="object.partner_invoice_id.zip or ''">90015</t>
                    <t t-out="object.partner_invoice_id.country_id.name or ''">Estados Unidos</t>
                </td>
            </tr>
            <tr>
                <td>
                    <span style="font-weight:bold;">Método de pago:</span>
                    <t t-if="tx_sudo.token_id">
                        <t t-out="tx_sudo.token_id.display_name or ''"></t>
                    </t>
                    <t t-else="">
                        <t t-out="tx_sudo.provider_id.sudo().name or ''"></t>
                    </t>
                    (<t t-out="format_amount(tx_sudo.amount, object.currency_id) or ''">$ 10.00</t>)
                </td>
            </tr>
        </tbody></table>
    </div>
    <div t-if="object.partner_shipping_id and not object.only_services" style="margin: 0px; padding: 0px;">
        <table width="100%" style="color: #454748; font-size: 12px;">
            <tbody><tr>
                <td>
                    <br/>
                    <span style="font-weight:bold;">Dirección de envío:</span>
                    <t t-out="object.partner_shipping_id.street or ''">1201 S Figueroa St</t>
                    <t t-out="object.partner_shipping_id.city or ''">Los Angeles</t>
                    <t t-out="object.partner_shipping_id.state_id.name or ''">California</t>
                    <t t-out="object.partner_shipping_id.zip or ''">90015</t>
                    <t t-out="object.partner_shipping_id.country_id.name or ''">Estados Unidos</t>
                </td>
            </tr>
        </tbody></table>
        <table t-if="hasattr(object, 'carrier_id') and object.carrier_id" width="100%" style="color: #454748; font-size: 12px;">
            <tbody><tr>
                <td>
                    <span style="font-weight:bold;">Método de envío:</span>
                    <t t-out="object.carrier_id.name or ''"></t>
                    <t t-if="object.amount_delivery == 0.0">
                        (Gratis)
                    </t>
                    <t t-else="">
                        (<t t-out="format_amount(object.amount_delivery, object.currency_id) or ''">$ 10.00</t>)
                    </t>
                </td>
            </tr>
            <tr t-if="object.carrier_id.carrier_description">
                <td>
                    <strong>Descripción de envío:</strong>
                    <t t-out="object.carrier_id.carrier_description"></t>
                </td>
            </tr>
        </tbody></table>
    </div>
</t>
</div>""",
    },
    "orden_venta_confirmacion_pago": {
        "subject": """{{ object.company_id.name }} - {{ (object.get_portal_last_transaction().state == 'pending') and 'Orden pendiente' or 'Orden' }} {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border-radius:0px; border-style:none; box-sizing:border-box;&#10;              border-width:0px; margin: 0px; padding: 0px; font-size: 13px;">
        <t t-set="transaction_sudo" t-value="object.get_portal_last_transaction()"></t>
        Hola&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>
        El pago con la referencia
        <span style="font-weight:bold;" t-out="transaction_sudo.reference or ''">SOOO49</span>
        por un importe total de
        <span style="font-weight:bold;" t-out="format_amount(transaction_sudo.amount, object.currency_id) or ''">$ 10.00</span>
        para la orden
        <span style="font-weight:bold;" t-out="object.name or ''">S00049</span>
        <t t-if="transaction_sudo and transaction_sudo.state == 'pending'">
            está pendiente.
            <br/>
            <t t-if="object.currency_id.compare_amounts(object.amount_paid + transaction_sudo.amount, object.amount_total) &gt;= 0 and object.state in ('draft', 'sent')">
                Confirmaremos tu orden una vez recibido el pago.
            </t>
            <t t-else="">
                Una vez que se confirmen, faltarán
                <span style="font-weight:bold;" t-out="format_amount(object.amount_total - object.amount_paid - transaction_sudo.amount, object.currency_id) or ''">$ 10.00</span>
                por pagar.
            </t>
        </t>
        <t t-else="">
            quedó confirmado.
            <t t-if="object.currency_id.compare_amounts(object.amount_paid, object.amount_total) &lt; 0">
                <br/>
                Saldo pendiente de pago:
               <span style="font-weight:bold;" t-out="format_amount(object.amount_total - object.amount_paid, object.currency_id) or ''">$ 10.00</span>.                
            </t>
        </t>
        <br/><br/>
        </p><div>
            Por favor, no dudes en contactarnos si tenés alguna consulta sobre esta transacción.
            <br/><br/>
            ¡Saludos!
        </div>
        <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div><div>
    <br/></div>

    <div>
  <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
</div>
        <div><br/></div>
    </div>""",
    },
    "compra_solicitud_cotizacion": {
        "subject": """{{ object.company_id.name }} - Solicitud de cotización {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Hola&nbsp;<t t-out="object.partner_id.name or ''">NombreProveedor</t>.
        <br/><br/>
        Te adjuntamos una solicitud de cotización
        <span style="font-weight: bold;" t-out="object.name or ''">P00015</span>
        <t t-if="object.partner_ref">
            (con referencia: <t t-out="object.partner_ref or ''"></t>)
        </t>
        de <t t-out="object.company_id.name or ''">NuestraEmpresa</t>.
    </p>

    <div><br/></div>

    <div>
        Por favor, no dudes en contactarnos si tenés alguna consulta sobre esta transacción.
        <br/><br/>
        ¡Saludos!
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "compra_orden_confirmada": {
        "subject": """{{ object.company_id.name }} - Orden de compra {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Hola&nbsp;<t t-out="object.partner_id.name or ''">NombreProveedor</t>.
        <br/><br/>
        Te adjuntamos la orden de compra
        <span style="font-weight: bold;" t-out="object.name or ''">P00015</span>
        <t t-if="object.partner_ref">
            (con referencia: <t t-out="object.partner_ref or ''"></t>)
        </t>
        por un importe total de
        <span style="font-weight: bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 1000.00</span>
        de <t t-out="object.company_id.name or ''">NuestraEmpresa</t>.
        <t t-if="object.date_planned">
            <br/><br/>
            La recepción está prevista para el <span style="font-weight: bold;" t-out="format_date(object.date_planned) or ''">05/05/2025</span>.
            ¿Nos confirmás la recepción de esta orden?
        </t>
    </p>
    <t t-if="object.date_planned">
        <div style="text-align: center; padding: 8px 0;">
            <a t-att-href="object.get_acknowledge_url()" target="_blank" style="padding: 8px 16px; color: #FFFFFF; text-decoration: none; background-color: #714B67; border-radius: 4px; font-size: 13px;">Confirmar recepción</a>
        </div>
    </t>
    <div><br/></div>

    <div>
        Por favor, no dudes en contactarnos si tenés alguna consulta sobre esta transacción.
        <br/><br/>
        ¡Saludos!
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "compra_recordatorio": {
        "subject": """{{ object.company_id.name }} - Recordatorio de entrega {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Hola&nbsp;<t t-out="object.partner_id.name or ''">NombreProveedor</t>.
        <br/><br/>
        Te recordamos que la entrega de la orden de compra
        <span style="font-weight: bold;" t-out="object.name or ''">P00015</span>
        <t t-if="object.partner_ref">
            (con referencia: <t t-out="object.partner_ref or ''"></t>)
        </t>
        está prevista para el
        <t t-if="object.date_planned">
            <span style="font-weight: bold;" t-out="format_date(object.date_planned) or ''">05/05/2025</span>.
        </t>
        <t t-else="">
            <span style="font-weight: bold;">fecha a confirmar</span>.
        </t>
        ¿Nos confirmás que se entrega en término?
    </p>
    <div style="text-align: center; padding: 8px 0;">
        <a t-att-href="object.get_acknowledge_url()" target="_blank" style="padding: 8px 16px; color: #FFFFFF; text-decoration: none; background-color: #714B67; border-radius: 4px; font-size: 13px;">Confirmar entrega</a>
    </div>
    <div><br/></div>

    <div>
        Por favor, no dudes en contactarnos si tenés alguna consulta sobre esta transacción.
        <br/><br/>
        ¡Saludos!
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "autofactura": {
        "subject": """{{ object.company_id.name }} - Autofactura {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Hola&nbsp;<t t-out="object.partner_id.name or ''">NombreProveedor</t>.
        <br/><br/>
        Te enviamos la autofactura
        <span style="font-weight: bold;" t-out="(object.name or '').replace('/', '-') or ''">FA-A00001-00000001</span>
        <t t-if="object.invoice_origin">
            (con referencia: <t t-out="object.invoice_origin or ''"></t>)
        </t>
        por un importe total de
        <span style="font-weight: bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 1000.00</span>.
    </p>

    <div><br/></div>

    <div>
        Por favor, no dudes en contactarnos si tenés alguna consulta sobre esta transacción.
        <br/><br/>
        ¡Saludos!
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "autofactura_nota_credito": {
        "subject": """{{ object.company_id.name }} - Autofactura, nota de crédito {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Hola&nbsp;<t t-out="object.partner_id.name or ''">NombreProveedor</t>.
        <br/><br/>
        Te enviamos la siguiente nota de crédito de autofactura
        <span style="font-weight: bold;" t-out="object.name or ''">RINV/2025/05/0001</span>
        <t t-if="object.invoice_origin">
            (con referencia: <t t-out="object.invoice_origin or ''"></t>)
        </t>
        por un importe total de
        <span style="font-weight: bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 1000.00</span>.
    </p>

    <div><br/></div>

    <div>
        Por favor, no dudes en contactarnos si tenés alguna consulta sobre esta transacción.
        <br/><br/>
        ¡Saludos!
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "factura_proforma": {
        "subject": """{{ object.company_id.name }} - {{ object.state in ('draft', 'sent') and 'Proforma' or 'Orden' }} {{ object.name or 'n/a' }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Hola&nbsp;<t t-out="object.partner_id.name or ''">NombreEmpresa</t>.
        <br/><br/>
        Te enviamos la factura proforma de
        <t t-out="'cotización' if object.state in ('draft', 'sent') else 'orden'">cotización</t>
        <span style="font-weight: bold;" t-out="object.name or ''">S00052</span>
        <t t-if="object.origin">
            (con referencia: <t t-out="object.origin or ''"></t>)
        </t>
        por un importe total de
        <span style="font-weight: bold;" t-out="format_amount(object.amount_total, object.currency_id) or ''">$ 10.00</span>.
    </p>

    <div><br/></div>

    <div>
        Por favor, no dudes en contactarnos si tenés alguna consulta sobre esta transacción.
        <br/><br/>
        ¡Saludos!
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "helpdesk_ticket_recibido": {
        "subject": """{{ object.name }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Hola&nbsp;<t t-out="object.sudo().partner_id.name or object.sudo().partner_name or ''">NombreCliente</t>.
        <br/><br/>
        Recibimos tu solicitud
        <t t-if="hasattr(object.team_id, 'website_id') and object.get_portal_url()">
            <a t-attf-href="{{ object.team_id.website_id.domain }}/my/ticket/{{ object.id }}/{{ object.access_token }}" t-out="object.name or ''">Título del ticket</a>
        </t>
        y la está revisando nuestro equipo de <t t-out="object.team_id.name or ''">Soporte</t>.
        La referencia de tu ticket es <strong><t t-out="object.ticket_ref or ''">15</t></strong>.
        <br/><br/>
        Para agregar información, respondé directamente este email.
    </p>

    <div style="text-align: center; padding: 16px 0px 16px 0px;">
        <t t-if="hasattr(object.team_id, 'website_id') and object.team_id.use_website_helpdesk_form">
            <a t-attf-style="background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px; font-size: 13px;" t-att-href="'%s%s' % (object.team_id.website_id.domain or '', object.get_portal_url())" target="_blank">Ver ticket</a>
        </t>
        <t t-else="">
            <a t-attf-style="background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px; font-size: 13px;" t-att-href="object.get_portal_url()" target="_blank">Ver ticket</a>
        </t>
        <t t-if="hasattr(object.team_id, 'website_id') and object.team_id.allow_portal_ticket_closing">
            <a t-attf-style="background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px; font-size: 13px;" t-att-href="'%s/my/ticket/close/%s/%s' % (object.team_id.website_id.domain or '', object.id, object.access_token)" target="_blank">Cerrar ticket</a>
        </t>
        <t t-elif="object.team_id.allow_portal_ticket_closing">
            <a t-attf-style="background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px; font-size: 13px;" t-att-href="'/my/ticket/close/%s/%s' % (object.id, object.access_token)" target="_blank">Cerrar ticket</a>
        </t>
    </div>

    <div><br/></div>

    <div>
        Por favor, no dudes en contactarnos si tenés alguna consulta.
        <br/><br/>
        ¡Saludos!
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "helpdesk_ticket_cerrado": {
        "subject": """Ticket cerrado - Referencia {{ object.id if object.id else 15 }}""",
        "body_html": """<div style="margin: 0px; padding: 0px;" data-oe-version="1.2">
    <p style="border: none; box-sizing: border-box; margin: 0px; padding: 0px; font-size: 13px;">
        Hola&nbsp;<t t-out="object.sudo().partner_id.name or ''">NombreCliente</t>.
        <br/><br/>
        Te contamos que cerramos tu ticket (referencia
        <t t-out="object.id or ''">15</t>).
        Esperamos que el servicio haya cumplido tus expectativas.
        <br/><br/>
        Si tenés alguna consulta, respondé este email para reabrir el ticket.
    </p>

    <div><br/></div>

    <div>
        Por favor, no dudes en contactarnos si tenés alguna consulta sobre esta transacción.
        <br/><br/>
        ¡Saludos!
    </div>

    <div><br/></div>

    <div>
        <strong>El equipo de <t t-out="object.company_id.name or ''">NombreEmpresa</t></strong>
    </div>

    <div><br/></div>

    <div>
        <img src="/logo.png?company=1" style="border: none; padding: 0px; margin: 0px; box-sizing: border-box; border-radius: 0px; vertical-align: middle; max-width: 180px; max-height: 100px; width: auto; height: auto;" alt="Logo de la empresa"/>
        <div><br/></div>
    </div>
</div>""",
    },
    "helpdesk_encuesta_satisfaccion": {
        "subject": """{{ object.company_id.name or object.user_id.company_id.name or 'Soporte' }}: Encuesta de satisfacción""",
        "body_html": """<div>
    <t t-set="access_token" t-value="object._rating_get_access_token()"/>
    <t t-set="partner" t-value="object._rating_get_partner()"/>
    <table border="0" cellpadding="0" cellspacing="0" style="width:100%; margin:0;">
    <tbody>
        <tr><td valign="top" style="font-size: 14px;">
            <t t-if="partner.name">
                Hola&nbsp;<t t-out="partner.name or ''">NombreCliente</t>,<br/><br/>
            </t>
            <t t-else="">
                Hola,<br/><br/>
            </t>
            Te pedimos un momento para calificar nuestro servicio en el ticket "<strong t-out="object.name or ''">Título del ticket</strong>"
            <t t-if="object._rating_get_operator().name">
                atendido por <strong t-out="object._rating_get_operator().name or ''">Nombre Apellido</strong>.<br/>
            </t>
            <t t-else="">
                .<br/><br/>
            </t>
        </td></tr>
        <tr><td style="text-align: center;">
            <table border="0" cellpadding="0" cellspacing="0" style="width:100%; margin: 32px 0px 32px 0px; display: inline-table;">
                <tr><td style="font-size: 14px; text-align:center;">
                    <strong>Contanos cómo te sentiste con nuestro servicio</strong><br/>
                    <span style="text-color: #888888">(hacé clic en una de estas caritas)</span>
                </td></tr>
                <tr><td style="font-size: 14px;">
                    <table style="width:100%;text-align:center;margin-top:2rem;">
                        <tr>
                            <td>
                                <a t-attf-href="/rate/{{ access_token }}/5" t-att-class="'pe-none' if object._rating_get_operator() else ''">
                                    <img alt="Contento" src="/rating/static/src/img/rating_5.png" title="Contento"/>
                                </a>
                            </td>
                            <td>
                                <a t-attf-href="/rate/{{ access_token }}/3" t-att-class="'pe-none' if object._rating_get_operator() else ''">
                                    <img alt="Neutral" src="/rating/static/src/img/rating_3.png" title="Neutral"/>
                                </a>
                            </td>
                            <td>
                                <a t-attf-href="/rate/{{ access_token }}/1" t-att-class="'pe-none' if object._rating_get_operator() else ''">
                                    <img alt="Descontento" src="/rating/static/src/img/rating_1.png" title="Descontento"/>
                                </a>
                            </td>
                        </tr>
                    </table>
                </td></tr>
            </table>
        </td></tr>
        <tr><td valign="top" style="font-size: 14px;">
            Agradecemos tu opinión, nos ayuda a mejorar continuamente.
            <br/><br/><span style="margin: 0px 0px 0px 0px; font-size: 12px; opacity: 0.5; color: #454748;">Esta encuesta se envió porque tu ticket pasó a la etapa <b t-out="object.stage_id.name or ''">En curso</b>.</span>
        </td></tr>
    </tbody>
    </table>
</div>""",
    },
    "usuario_invitacion": {
        "subject": """{{ object.create_uid.name }} de {{ object.company_id.name }} lo invita a conectarse a Odoo""",
        "body_html": """<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">
<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
<tbody>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="middle">
                    <span style="font-size: 10px;">¡Bienvenido a Odoo!</span><br/>
                    <span style="font-size: 20px; font-weight: bold;">
                        <t t-out="object.name or ''">Marc Demo</t>
                    </span>
                </td><td valign="middle" align="right" t-if="not object.company_id.uses_default_logo">
                    <img t-attf-src="/logo.png?company={{ object.company_id.id }}" style="padding: 0px; margin: 0px; height: auto; width: 80px;" t-att-alt="object.company_id.name"/>
                </td></tr>
                <tr><td colspan="2" style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="top" style="font-size: 13px;">
                    <div>
                        Hola <t t-out="object.name or ''">Marc Demo</t>,<br /><br />
                        Te invitó <t t-out="object.create_uid.name or ''">OdooBot</t> de <t t-out="object.company_id.name or ''">SuEmpresa</t> a conectarte a Odoo.
                        <div style="margin: 16px 0px 16px 0px;">
                            <a t-att-href="object.partner_id._get_signup_url()"
                                t-attf-style="background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px; font-size:13px;">
                                Aceptar invitación
                            </a>
                        </div>
                        <b>Este enlace es válido durante <t t-out="int(int(object.env['ir.config_parameter'].sudo().get_param('auth_signup.signup.validity.hours',144))/24)"></t> días</b> <br/>
                        <t t-set="website_url" t-value="object.get_base_url()"></t>
                        Tu dominio de Odoo es: <b><a t-att-href='website_url' t-out="website_url or ''">http://suempresa.odoo.com</a></b><br />
                        Tu email de acceso es: <b><a t-attf-href="/web/login?login={{ object.email }}" target="_blank" t-out="object.email or ''">nombre@ejemplo.com</a></b><br /><br />
                        Ante cualquier consulta, no dudes en escribirnos.
                        <br /><br />
                        ¡Saludos!<br />
                        --<br/>El equipo de <t t-out="object.company_id.name or ''">SuEmpresa</t>
                    </div>
                </td></tr>
                <tr><td style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="middle" align="left">
                    <t t-out="object.company_id.name or ''">SuEmpresa</t>
                </td></tr>
                <tr><td valign="middle" align="left" style="opacity: 0.7;">
                    <t t-out="object.company_id.phone or ''">+54 11 1234-5678</t>
                    <t t-if="object.company_id.email">
                        | <a t-att-href="'mailto:%s' % object.company_id.email" style="text-decoration:none; color: #454748;" t-out="object.company_id.email or ''">info@suempresa.com</a>
                    </t>
                    <t t-if="object.company_id.website">
                        | <a t-att-href="'%s' % object.company_id.website" style="text-decoration:none; color: #454748;" t-out="object.company_id.website or ''">http://www.ejemplo.com</a>
                    </t>
                </td></tr>
            </table>
        </td>
    </tr>
</tbody>
</table>
</td></tr>
<tr><td align="center" style="min-width: 590px;">
    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
      <tr><td style="text-align: center; font-size: 13px;">
        Desarrollado por <a target="_blank" href="https://www.odoo.com?utm_source=db&amp;utm_medium=auth" t-attf-style="color: {{object.company_id.email_secondary_color or '#875A7B'}};">Odoo</a>
      </td></tr>
    </table>
</td></tr>
</table>""",
    },
    "usuario_recordatorio_pendiente": {
        "subject": """Recordatorio de usuarios sin registrar""",
        "body_html": """<table border="0" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">
<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
<tbody>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <t t-set="invited_users" t-value="ctx.get('invited_users', [])" />
                <td style="text-align : left">
                    <span style="font-size: 20px; font-weight: bold;">
                        Invitaciones pendientes
                    </span><br/><br/>
                </td>
                <tr><td valign="top" style="font-size: 13px;">
                    <div>
                        Hola <t t-out="object.name or ''">Mitchell Admin</t>,<br/> <br/>
                        Agregaste los siguientes usuarios a la base de datos, pero todavía no se registraron:
                        <ul>
                            <t t-foreach="invited_users" t-as="invited_user">
                                <li t-out="invited_user or ''">demo@ejemplo.com</li>
                            </t>
                        </ul>
                        Te sugerimos hacer un seguimiento para que puedan acceder a la base de datos y empezar a trabajar.
                        <br /><br/>
                        ¡Saludos!<br />
                        --<br/>El equipo de <t t-out="object.company_id.name or ''">SuEmpresa</t>
                    </div>
                </td></tr>
                <tr><td style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
</tbody>
</table>
</td></tr>
</table>""",
    },
    "usuario_cuenta_creada": {
        "subject": """¡Bienvenido a {{ object.company_id.name }}!""",
        "body_html": """<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">
<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
<tbody>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="middle">
                    <span style="font-size: 10px;">Su cuenta</span><br/>
                    <span style="font-size: 20px; font-weight: bold;">
                        <t t-out="object.name or ''">Marc Demo</t>
                    </span>
                </td><td valign="middle" align="right" t-if="not object.company_id.uses_default_logo">
                    <img t-attf-src="/logo.png?company={{ object.company_id.id }}" style="padding: 0px; margin: 0px; height: auto; width: 80px;" t-att-alt="object.company_id.name"/>
                </td></tr>
                <tr><td colspan="2" style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="top" style="font-size: 13px;">
                    <div>
                        Hola <t t-out="object.name or ''">Marc Demo</t>,<br/><br/>
                        ¡Tu cuenta ya está lista!<br/>
                        Tu usuario de acceso es <strong><t t-out="object.email or ''">nombre@ejemplo.com</t></strong><br/>
                        Para entrar a tu cuenta, usá este enlace:
                        <div style="margin: 16px 0px 16px 0px;">
                            <a t-attf-href="/web/login?auth_login={{object.email}}"
                                t-attf-style="background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px; font-size:13px;">
                                Ir a mi cuenta
                            </a>
                        </div>
                        ¡Gracias!<br/>
                        <t t-if="user.signature">
                            <br/>
                            <div>--<br/><t t-out="user.signature or ''">Mitchell Admin</t></div>
                        </t>
                    </div>
                </td></tr>
                <tr><td style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="middle" align="left">
                    <t t-out="object.company_id.name or ''">SuEmpresa</t>
                </td></tr>
                <tr><td valign="middle" align="left" style="opacity: 0.7;">
                    <t t-out="object.company_id.phone or ''">+54 11 1234-5678</t>
                    <t t-if="object.company_id.email">
                        | <a t-attf-href="mailto:{{object.company_id.email}}" style="text-decoration:none; color: #454748;" t-out="object.company_id.email or ''">info@suempresa.com</a>
                    </t>
                    <t t-if="object.company_id.website">
                        | <a t-att-href="object.company_id.website" style="text-decoration:none; color: #454748;" t-out="object.company_id.website or ''">http://www.ejemplo.com</a>
                    </t>
                </td></tr>
            </table>
        </td>
    </tr>
</tbody>
</table>
</td></tr>
<tr><td align="center" style="min-width: 590px;">
    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
      <tr><td style="text-align: center; font-size: 13px;">
        Desarrollado por <a target="_blank" href="https://www.odoo.com?utm_source=db&amp;utm_medium=auth" t-attf-style="color: {{object.company_id.email_secondary_color or '#875A7B'}};">Odoo</a>
      </td></tr>
    </table>
</td></tr>
</table>""",
    },
    "portal_invitacion": {
        "subject": """Su cuenta en {{ object.company_id.name }}""",
        "body_html": """<table border="0" cellpadding="0" cellspacing="0"
    style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
    <tr><td align="center">
        <table border="0" cellpadding="0" cellspacing="0" width="590"
            style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">
            <tbody>
                <tr>
                    <td align="center" style="min-width: 590px;">
                        <table border="0" cellpadding="0" cellspacing="0" width="590"
                            style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                            <tr>
                                <td valign="middle">
                                    <span style="font-size: 10px;">Su cuenta</span><br/>
                                    <span style="font-size: 20px; font-weight: bold;" t-out="object.name or ''">Marc Demo</span>
                                </td>
                                <td valign="middle" align="right" t-if="not object.company_id.uses_default_logo">
                                    <img t-attf-src="/logo.png?company={{ object.company_id.id }}" style="padding: 0px; margin: 0px; height: auto; width: 80px;"
                                        t-att-alt="object.company_id.name"/>
                                </td>
                            </tr>
                            <tr><td colspan="2" style="text-align:center;">
                                <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin:16px 0px 16px 0px;"/>
                            </td></tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td align="center" style="min-width: 590px;">
                        <table border="0" cellpadding="0" cellspacing="0" width="590"
                            style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                            <tr><td valign="top" style="font-size: 13px;">
                                <div>
                                    Hola <t t-out="object.name or ''">Marc Demo</t>,<br/> <br/>
                                    ¡Bienvenido/a al Portal de <t t-out="object.company_id.name">SuEmpresa</t>!<br/><br/>
                                    Creamos una cuenta a tu nombre con el siguiente usuario: <t t-out="object.login">demo</t><br/><br/>
                                    Hacé clic en el botón de abajo para elegir una contraseña y activar tu cuenta.
                                    <div style="margin: 16px 0px 16px 0px; text-align: center;">
                                        <a t-att-href="object.partner_id._get_signup_url()"
                                        t-attf-style="display: inline-block; padding: 10px; text-decoration: none; font-size: 12px; background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px;">
                                            <strong>Activar cuenta</strong>
                                        </a>
                                    </div>
                                    <t t-out="ctx.get('welcome_message') or ''">Bienvenido/a al portal de nuestra empresa.</t>
                                </div>
                            </td></tr>
                            <tr><td style="text-align:center;">
                                <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                            </td></tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td align="center" style="min-width: 590px;">
                        <table border="0" cellpadding="0" cellspacing="0" width="590"
                            style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">
                            <tr><td valign="middle" align="left">
                                <t t-out="object.company_id.name or ''">SuEmpresa</t>
                            </td></tr>
                            <tr><td valign="middle" align="left" style="opacity: 0.7;">
                                <t t-out="object.company_id.phone or ''">+54 11 1234-5678</t>
                                <t t-if="object.company_id.email">
                                    | <a t-attf-href="mailto:{{ object.company_id.email }}" style="text-decoration: none; color: #454748;" t-out="object.company_id.email or ''">info@suempresa.com</a>
                                </t>
                                <t t-if="object.company_id.website">
                                    | <a t-att-href="object.company_id.website" style="text-decoration: none; color: #454748;" t-out="object.company_id.website or ''">http://www.ejemplo.com</a>
                                </t>
                            </td></tr>
                        </table>
                    </td>
                </tr>
            </tbody>
        </table>
    </td></tr>
    <tr><td align="center" style="min-width: 590px;">
        <table border="0" cellpadding="0" cellspacing="0" width="590"
            style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
            <tr><td style="text-align: center; font-size: 13px;">
                Desarrollado por <a target="_blank" t-attf-href="https://www.odoo.com?utm_source=db&amp;utm_medium={{ ctx.get('medium', 'auth') }}" t-attf-style="color: {{object.company_id.email_secondary_color or '#875A7B'}};">Odoo</a>
            </td></tr>
        </table>
    </td></tr>
</table>""",
    },
    "usuario_invitacion_2fa": {
        "subject": """Invitación para activar la autenticación en dos pasos en su cuenta de Odoo""",
        "body_html": """<div style="margin: 0px; padding: 0px; font-size: 13px;">
    <p style="margin: 0px; padding: 0px; font-size: 13px;">
        Hola <t t-out="object.partner_id.name or ''"></t>,<br/><br/>
        <t t-out="user.name or ''"></t> te pidió activar la autenticación en dos pasos para proteger tu cuenta.<br/><br/>
        La autenticación en dos pasos ("2FA") es un sistema de doble verificación.
        La primera se hace con tu contraseña y la segunda con un código que obtenés desde una aplicación móvil dedicada.
        Algunas de las más usadas son Authy, Google Authenticator o Microsoft Authenticator.

        <p style="margin: 16px 0px 16px 0px; text-align: center;">
            <a t-att-href="object.get_totp_invite_url()"
                t-attf-style="background-color:{{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px;">
                Activar mi autenticación en dos pasos
            </a>
        </p>
    </p>
</div>""",
    },
}

