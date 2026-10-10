import { AccountMoveListController } from "@account/views/account_move_list/account_move_list_controller";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

// La lista de facturas de proveedor usa la vista "account_tree" de account:
// se parchea su controlador en vez de reemplazarlo para no perder el botón
// "Subir" ni el resto del comportamiento estándar.
patch(AccountMoveListController.prototype, {
    setup() {
        super.setup();
        this.actionService = useService("action");
    },

    get showYpfButton() {
        return this.props.context.default_move_type === "in_invoice";
    },

    onClickNuevaFacturaYPF() {
        return this.actionService.doAction("ypf_route.action_ypf_import_wizard");
    },
});
