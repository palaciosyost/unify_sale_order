from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    state = fields.Selection(selection_add=[("fusionado", "Fusionado")])


class PurchaseUnify(models.TransientModel):
    _name = "purchase.unify"
    _description = "Unificar órdenes de compra"

    select_mode = fields.Selection(
        [
            ("new_order", "Nueva Orden de Compra"),
            ("delete_order", "Eliminar Ordenes Fusionadas"),
            ("readonly_order", "Solo lectura Ordenes Fusionadas"),
        ],
        required=True,
    )
    select_mode_proveedor = fields.Selection([
        ("new_partner", "Nuevo Proveedor"),
        ("partner_set", "Usar Proveedor Definido"),
    ], string="Proveedor", required=True)
    new_partner = fields.Many2one("res.partner", string="Nuevo Proveedor")

    def unify_purchase(self):
        purchase_ids = self.env["purchase.order"].browse(self.env.context.get("active_ids"))
        new_order = ''
        if any(p.state in ["fusionado", "purchase", "cancel"] for p in purchase_ids):
            raise UserError(_("Las órdenes de compra no deben estar en estado ['Fusionado', 'Orden de compra', 'Cancelado']"))
        
        if self.select_mode == "new_order":
            new_order = self._new_order_merge(purchase_ids)
        elif self.select_mode == "delete_order":
            new_order = self._delete_orders(purchase_ids)
        elif self.select_mode == "readonly_order":
            new_order = self._readonly_order_merge(purchase_ids)

        if isinstance(new_order, dict):
            return new_order

    def _validate_supplier(self, purchase_ids):
        if self.select_mode_proveedor == 'partner_set' and len(set(p.partner_id.id for p in purchase_ids)) > 1:
            raise UserError(_("Si desea mantener el mismo proveedor, seleccione órdenes con el mismo proveedor."))
        if self.select_mode_proveedor == 'new_partner' and not self.new_partner:
            raise UserError(_("Para crear una nueva orden de compra seleccione un proveedor nuevo."))

    def _create_purchase(self, purchase_ids):
        return self.env["purchase.order"].create({
            "partner_id": self.new_partner.id if self.select_mode_proveedor == "new_partner" else purchase_ids[0].partner_id.id
        })

    def _copy_lines(self, purchase_ids, new_order):
        for po in purchase_ids:
            for line in po.order_line:
                line.copy({"order_id": new_order.id})

    def _log_messages(self, new_order, purchase_ids, eliminar=False):
        for po in purchase_ids:
            po.message_post(body=f"Esta orden fue fusionada{' y eliminada' if eliminar else ''} en la orden {new_order.name}", subtype_xmlid="mail.mt_note")
        new_order.message_post(body=f"Esta orden fue creada a partir de la fusión de: {', '.join(po.name for po in purchase_ids)}", subtype_xmlid="mail.mt_note")

    def _new_order_merge(self, purchase_ids):
        self._validate_supplier(purchase_ids)
        new_order = self._create_purchase(purchase_ids)
        self._copy_lines(purchase_ids, new_order)
        self._log_messages(new_order, purchase_ids)
        return self._open_order_form(new_order)

    def _readonly_order_merge(self, purchase_ids):
        self._validate_supplier(purchase_ids)
        new_order = self._create_purchase(purchase_ids)
        self._copy_lines(purchase_ids, new_order)
        purchase_ids.write({"state": "fusionado"})
        self._log_messages(new_order, purchase_ids)
        return self._open_order_form(new_order)

    def _delete_orders(self, purchase_ids):
        self._validate_supplier(purchase_ids)
        new_order = self._create_purchase(purchase_ids)
        self._copy_lines(purchase_ids, new_order)
        self._log_messages(new_order, purchase_ids, eliminar=True)
        purchase_ids.unlink()
        return self._open_order_form(new_order)

    def _open_order_form(self, order):
        return {
            "type": "ir.actions.act_window",
            "name": _("Orden de Compra"),
            "res_model": "purchase.order",
            "view_mode": "form",
            "res_id": order.id,
            "target": "current",
            "flags": {"mode": "edit"},
            "views": [(self.env.ref("purchase.purchase_order_form").id, "form")],
        }
