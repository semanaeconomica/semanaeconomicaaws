from odoo import models, fields, api


class ModeloReporte(models.Model):
    _name = 'plantilla.reporte'
    name = fields.Char(required=True)
    contenido = fields.Html(default='''<p><strong>Facturar a:</strong>  @facturar</p>
                <p><strong>R.U.C: </strong> @ruc_factura</p>
                <p><strong>Dirección:</strong> @direccion_factura</p>
                <p><strong>Teléfono:</strong> @telefono_factura</p>
                <p><strong>Nombre:</strong> @cliente </p>
                <p><strong>E-mail:</strong>@cliente_email</p>
                <p>
                Aprobada la cotización y/o orden de venta (incluyendo aprobaciones vía correo electrónico),
                SemanaEconómica podrá aplicar estas penalidades </p>
                <p>   Para publicidad impresa:</p>
                <p>   50% del aviso, si Cliente anula publicación 7 días antes de cierre comercial según cronograma.</p>
                <p>   70% del aviso, si Cliente anula publicación 3 días antes de cierre comercial según cronograma.</p>
                <p>    100% del aviso, si Cliente anula publicación 1 día antes de cierre comercial o pasada fecha decierre según cronograma</p>
                <p> Publicidad en cualquier plataforma digital de Semana Económica (web, mobile, emailing o boletines):</p>
                <p>   50% de pauta contratada si Cliente anula publicación entre 15 y 8 días antes de inicio previstode campaña.</p>
                <p>   100% de pauta contratada si Cliente anula publicación 7 o menos días antes de inicio previsto de campaña.</p>

                <p>@empresa_name</p>
                <p>@empresa_direccion</p>
                <p>Director: @vendedor,</p>
                <p>Teléfono: @vendedor_telefono ,</p>
                <p>Celular: @vendedor_celular</p>
                <p>E-mail: @empresa_email </p>
                <p>@empresa_web</p>''')

    leyenda = fields.Html(compute="get_leyenda")

    @api.depends('leyenda')
    def get_leyenda(self):
        for record in self:
            record.leyenda = '''
                <p><strong>@facturar </strong> : Persona a facturar</p>
                <p><strong>@direccion_factura </strong> : Dirección de factura</p>
                <p><strong>@telefono_factura</strong></p>
                <p><strong>@cliente</strong></p>
                <p><strong>@cliente_email</strong></p>
                <p>@empresa_name</p>
                <p>@empresa_direccion</p>
                <p>@vendedor,</p>
                <p>@vendedor_telefono ,</p>
                <p@vendedor_celular</p>
                <p>@empresa_email </p>
                <p>@empresa_web</p>
                '''


class Ventas(models.Model):
    _inherit = 'sale.order'
    plantilla_rep = fields.Many2one('plantilla.reporte', string="Plantilla Reporte")
    plantilla_reporte = fields.Html(string="Contenido")
    plantilla_reporte_rem = fields.Html(compute="_set_plantilla")
    leyenda = fields.Html(related="plantilla_rep.leyenda")

    @api.onchange('plantilla_rep')
    def change_plantilla(self):
        self.plantilla_reporte = self.plantilla_rep.contenido


    @api.depends('plantilla_reporte_rem')
    def _set_plantilla(self):
        # buscar la plantilla
        for l in self:
            if l.plantilla_reporte:
                contenido = l.plantilla_reporte
                contenido = contenido.replace('@facturar', str(l.partner_invoice_id.name))
                contenido = contenido.replace('@ruc_factura', str(l.partner_invoice_id.vat))
                contenido = contenido.replace('@direccion_factura', str(l.partner_invoice_id.contact_address))
                contenido = contenido.replace('@telefono_factura', str(l.partner_invoice_id.phone))
                contenido =  contenido.replace('@cliente',str(l.partner_id.name))
                contenido =  contenido.replace('@empresa_name',str(l.company_id.name))
                contenido =  contenido.replace('@empresa_direccion',str(l.company_id.partner_id.contact_address))
                contenido =  contenido.replace('@vendedor',str(l.user_id.name))
                contenido =  contenido.replace('@vendedor_telefono',str(l.user_id.phone))
                contenido =  contenido.replace('@empresa_email',str(l.user_id.company_id.email))
                contenido =  contenido.replace('@empresa_web',str(l.user_id.company_id.website))
                l.plantilla_reporte_rem = contenido
            else:
                l.plantilla_reporte_rem = None
