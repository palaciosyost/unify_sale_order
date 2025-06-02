from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder (models.Model):
    _inherit = "sale.order"

    state = fields.Selection(selection_add=[("fusionado", "Fusionado")])



class SaleUnify(models.TransientModel):
    _name = "sale.unify"

    select_mode = fields.Selection(
        [
            ("new_order", "Nueva Cotizacion"),
            ("delete_order", "Eliminar Cotizaciones Fusionadas"),
            ("readonly_order", "Solo lectura Cotizaciones Fusionada"),
        ],
        required=True
    )
    select_mode_cliente = fields.Selection([("new_cliente", "Nuevo Cliente"), ("cliente_set", "Usar Cliente Definido"),], string="Cliente")
    new_cliente_sale = fields.Many2one("res.partner", string="Nuevo Cliente")
    def unify_sale(self):
        sale_ids = self.env["sale.order"].browse(self.env.context.get("active_ids"))
        new_cotizacion = ''
        if any( sale.state in ["fusionado", "sale", "cancel"] for sale in sale_ids):
            raise UserError(_("Las cotizaciones no deben estar en el estado  ['Fusionado', 'Orden de venta', 'Cancelado']"))
        else:
            if self.select_mode == "new_order":
                new_cotizacion = self.new_order_merge(sale_ids,self.select_mode_cliente, self.new_cliente_sale )
            if self.select_mode == "delete_order":
                new_cotizacion =  self.delete_order(sale_ids,self.select_mode_cliente, self.new_cliente_sale )
            if self.select_mode == "readonly_order":
                new_cotizacion = self.new_readonly_order(sale_ids,self.select_mode_cliente, self.new_cliente_sale )
            if isinstance(new_cotizacion, dict):
                return new_cotizacion


    def new_order_merge(self, sale_ids, select_mode_cliente, new_cliente_sale):
        if select_mode_cliente == 'cliente_set' and len(set(sale.partner_id.id for sale in sale_ids)) > 1:
            raise UserError(_("Si se requiere mantener el mismo cliente para la nueva cotizacion, seleccione las cotizaciones con que tengan el mismo cliente"))
        if select_mode_cliente == 'new_cliente' and not new_cliente_sale:
            raise UserError(_("Para crear un nueva cotizacion seleccione un cliente nuevo"))
        
        new_cotizacion = self.env["sale.order"].create({
            "partner_id" : new_cliente_sale.id if select_mode_cliente == "new_cliente" else sale_ids[0].partner_id.id
        })

        for line in sale_ids.order_line:
            line.copy({
                "order_id" : new_cotizacion.id
            })

        # Mensaje en cotizaciones fusionadas
        for sale in sale_ids:
            sale.message_post(body=f"Esta cotizacion esta fusionada en la cotizacion {new_cotizacion.name}", message_type="comment", subtype_xmlid="mail.mt_note")
        # Mensaje en la nueva cotización
        new_cotizacion.message_post(body=f"Esta cotización fue creada a partir de la fusión de: {', '.join(sale.name for sale in sale_ids)}", message_type="comment", subtype_xmlid="mail.mt_note")

        return {
            "type": "ir.actions.act_window",
            "name": _("Cotización"),
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": new_cotizacion.id,
            "target": "current",
            "flags": {"mode": "edit"},
            "views": [(self.env.ref("sale.view_order_form").id, "form")],
        }

    def new_readonly_order(self, sale_ids, select_mode_cliente, new_cliente_sale):
        if select_mode_cliente == 'cliente_set' and len(set(sale.partner_id.id for sale in sale_ids)) > 1:
            raise UserError(_("Si se requiere mantener el mismo cliente para la nueva cotizacion, seleccione las cotizaciones con que tengan el mismo cliente"))
        if select_mode_cliente == 'new_cliente' and not new_cliente_sale:
            raise UserError(_("Para crear un nueva cotizacion seleccione un cliente nuevo"))
        
        new_cotizacion = self.env["sale.order"].create({
            "partner_id" : new_cliente_sale.id if select_mode_cliente == "new_cliente" else sale_ids[0].partner_id.id
        })

        for line in sale_ids.order_line:
            line.copy({
                "order_id" : new_cotizacion.id
            })

        sale_ids.write({
            "state" : "fusionado",
        })

        # Mensaje en cotizaciones fusionadas
        for sale in sale_ids:
            sale.message_post(
                body=f"Esta cotización fue fusionada con la cotización <b>{new_cotizacion.name}</b>.",
                message_type="comment",
                subtype_xmlid="mail.mt_note"
            )
        # Mensaje en la nueva cotización
        new_cotizacion.message_post(
            body=f"Esta cotización fue creada a partir de la fusión de: {', '.join(sale.name for sale in sale_ids)}",
            message_type="comment",
            subtype_xmlid="mail.mt_note"
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Cotización"),
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": new_cotizacion.id,
            "target": "current",
            "flags": {"mode": "edit"},
            "views": [(self.env.ref("sale.view_order_form").id, "form")],
        }

    def delete_order(self, sale_ids, select_mode_cliente, new_cliente_sale):
        if select_mode_cliente == 'cliente_set' and len(set(sale.partner_id.id for sale in sale_ids)) > 1:
            raise UserError(_("Si se requiere mantener el mismo cliente para la nueva cotizacion, seleccione las cotizaciones con que tengan el mismo cliente"))
        if select_mode_cliente == 'new_cliente' and not new_cliente_sale:
            raise UserError(_("Para crear un nueva cotizacion seleccione un cliente nuevo"))
        
        new_cotizacion = self.env["sale.order"].create({
            "partner_id" : new_cliente_sale.id if select_mode_cliente == "new_cliente" else sale_ids[0].partner_id.id
        })

        for line in sale_ids.order_line:
            line.copy({
                "order_id" : new_cotizacion.id
            })

        # Mensaje en cotizaciones fusionadas antes de eliminar
        for sale in sale_ids:
            sale.message_post(body=f"Esta cotizacion fue fusionada y eliminada en la cotizacion {new_cotizacion.name}", message_type="comment", subtype_xmlid="mail.mt_note")
        # Mensaje en la nueva cotización
        new_cotizacion.message_post(body=f"Esta cotización fue creada a partir de la fusión y eliminación de: {', '.join(sale.name for sale in sale_ids)}", message_type="comment", subtype_xmlid="mail.mt_note")

        sale_ids.unlink()

        return {
            "type": "ir.actions.act_window",
            "name": _("Cotización"),
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": new_cotizacion.id,
            "target": "current",
            "flags": {"mode": "edit"},
            "views": [(self.env.ref("sale.view_order_form").id, "form")],
        }
