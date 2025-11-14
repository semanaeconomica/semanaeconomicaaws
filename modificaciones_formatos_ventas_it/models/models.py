from odoo import api, fields, models, _
class Sale_Order_Line(models.Model):
    _inherit = 'sale.order.line'
    format_id = fields.Many2one('product.format.it',string="Formato")
    ini       = fields.Date(string="INI")
    fin       = fields.Date(string="FIN")


    @api.onchange('product_id')
    def change_format(self):
        for record in self:
            if record.product_id.product_tmpl_id.format_id:
                record.format_id = record.product_id.product_tmpl_id.format_id.id

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    format_id = fields.Many2one('product.format.it',string="Formato")