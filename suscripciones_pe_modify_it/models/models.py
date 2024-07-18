from odoo import models, fields, api
class CrmLead(models.Model):
    _inherit = 'crm.lead'
    tipo_doc = fields.Many2one('l10n_latam.identification.type',related="partner_id.l10n_latam_identification_type_id",
                               string="DOC")
    num_doc  = fields.Char(related='partner_id.vat',string="Nª Doc")

class SaleOrder(models.Model):
    _inherit    = 'sale.order'
    salesman_id = fields.Many2one('res.partner',string="Vendedor Encargado")
    edit_encargado    = fields.Boolean(compute="_is_encargado", default=False)
    def _is_encargado(self):
        for record in self:
            record.edit_encargado = self.env['res.users'].has_group('suscripciones_pe_modify_it.group_modify_vendedor_encargado')



