from odoo import api, fields, models
class Rutas(models.Model):
    _inherit          = 'route.yaros'
    etiquetas         = fields.Many2many('sync.se.sesi.etiquetas',compute="get_etiquetas")
    route_type        = fields.Selection([('lima','LIMA'),('externo','EXTERNO')],string="Tipo de Ruta")
    cantidad          = fields.Integer()
    count_etique      = fields.Integer(compute="total_etiquetas")
    def total_etiquetas(self):
        for record in self:
            if record.etiquetas:
                record.count_etique = len(record.etiquetas)
            else:
                record.count_etique = 0


    @api.depends('etiquetas')
    def get_etiquetas(self):
        for record in self:
            record.etiquetas = None
            etiquetas = self.env['sync.se.sesi.etiquetas'].search([('product.no_generar_etiqueta','=',False),
                                                                   ('state','in',('open','pending')),('ruta','=',record.id)],order="orden_entrega")
            list_etiquetas = []
            for e in etiquetas:
                list_etiquetas.append(e.id)
            if list_etiquetas:
                record.etiquetas = [(6, 0, list_etiquetas)]
            else:
                record.etiquetas = None

class Etiquetas(models.Model):
    _inherit = 'sync.se.sesi.etiquetas'
    partner_id = fields.Many2one('res.partner',string="Related Company",related="salesorderid.partner_id")


