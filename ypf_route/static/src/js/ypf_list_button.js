/** @odoo-module **/
import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { useService } from "@web/core/utils/hooks";

export class YpfListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    onClickNuevaFacturaYPF() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "ypf.import.wizard",
            name: "Nueva factura YPF Ruta",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }
}

// SIN asignar template propio — hereda el de ListController (web.ListView)
// El botón se inyecta via extensión del template web.ListView en el XML

export const ypfInvoiceListView = {
    ...listView,
    Controller: YpfListController,
};

registry.category("views").add("ypf_invoice_list", ypfInvoiceListView);