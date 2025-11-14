from odoo import fields, models , api

class SaleOrderLineIT(models.Model):
    _inherit = 'sale.order.line'
    tax_id_it = fields.Many2one('account.tax',string='Edit Impuestos')
    @api.onchange('tax_id_it')
    def change_tax_it(self):
        for record in self:
            record.tax_id = False

            tax_ids = [record.tax_id_it.id]
            record.sudo().write = {
                'tax_id': [(6, 0, tax_ids)]
            }
            record.tax_id = [(6, 0, tax_ids)]
            '''
            tax_ids = []
            for t in record.tax_id_it:
                tax_ids.append(t.id)
            
            '''