from odoo import models, fields, api
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.exceptions import UserError
import base64
from dateutil.relativedelta import relativedelta

class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def create_returns(self):
        t = super(ReturnPicking,self).create_returns()
        picking_op = self.env['stock.picking'].browse(t['res_id'])

        for i in picking_op.move_ids_without_package:
            if i.product_id.tracking == 'serial':
                padre = i.origin_returned_move_id
                lotes_viejos = []
                for elem in padre.move_line_ids:
                    lotes_viejos.append(elem.lot_id.id)
                cont = 0
                for new_elem in i.move_line_ids:
                    new_elem.lot_id = lotes_viejos[cont]
                    cont +=1
            if i.product_id.tracking == 'lot':
                padre = i.origin_returned_move_id
                lotes_viejos = []
                for elem in padre.move_line_ids:
                    lotes_viejos.append([elem.lot_id.id,elem.qty_done])
                cont = 0
                if len(i.move_line_ids) >1:
                    for new_elem in i.move_line_ids:
                        new_elem.lot_id = lotes_viejos[cont][0]
                        cont +=1
                else:                    
                    restante = i.reserved_availability

                    i.move_line_ids[0].lot_id = lotes_viejos[cont][0]
                    cantidad = lotes_viejos[cont][1] if restante >= lotes_viejos[cont][1] else restante
                    i.move_line_ids[0].qty_done = cantidad
                    i.move_line_ids[0].product_uom_qty = cantidad
                    restante -= cantidad

                    cont += 1

                    while restante > 0:
                        nuevo = i.move_line_ids[0].copy()                        
                        nuevo.lot_id = lotes_viejos[cont][0]
                        cantidad = lotes_viejos[cont][1] if restante >= lotes_viejos[cont][1] else restante
                        nuevo.qty_done = cantidad                        
                        nuevo.product_uom_qty = cantidad
                        restante -= cantidad
                        cont += 1

        return t