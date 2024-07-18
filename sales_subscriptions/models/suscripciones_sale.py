# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta 

class product_template(models.Model):
    _inherit = 'product.template'

    no_generar_etiqueta = fields.Boolean('No generar Etiqueta',default=False)

class type_contract_yaros(models.Model):
    _name = 'type.contract.yaros'

    name = fields.Char('Tipo Contrato',required="1")


class format_delivery_yaros(models.Model):
    _name = 'format.delivery.yaros'

    name = fields.Char('Forma Entrega',required="1")

class route_yaros(models.Model):
    _name = 'route.yaros'

    name = fields.Char('Ruta',required="1")
    day_week = fields.Selection([("monday","LUN"),("tuesday","MAR"),("wednesday","MIE"),("thursday","JUE"),("friday","VIE"),("saturday","SAB"),("sunday","DOM")],'Dia')
    district_ids = fields.Many2many('res.country.state','district_route_yaros_rel','district_id','route_id','Distritos')


class suscription_sale_order(models.Model):
    _name = 'suscription.sale.order'

    
   
    name = fields.Char(u'Suscripción')
    orden = fields.Char('Orden')
    state = fields.Selection([('draft','Borrador'),('open','En Progreso'),('pending','Para Renovar'),('close','Cerrado'),('cancel','Cancelado')],'Estado',default="draft")
    partner_id = fields.Many2one('res.partner','Cliente')
    parent_new_id = fields.Many2one('res.partner','Empresa')
    type_contract_id = fields.Many2one('type.contract.yaros','Tipo Contrato')
    new_suscription_id = fields.Many2one('suscription.sale.order',u'Nueva Suscripción')
    order_ids = fields.Many2many('sale.order','order_suscrpitions_rel','order_id','suscription_id','Ordenes de Venta')
    manager_id = fields.Many2one('res.users','Ejecutivo Venta')
    product_yaros_id = fields.Many2one('product.product','Producto')
    package = fields.Char('Paquete')
    not_etiquet = fields.Boolean('No generar etiqueta')
    recurring_rule_type= fields.Selection([("monthly","Mensual"),("yearly","Anual")],'Recurrencia')
    
    etiquetas_ids = fields.One2many('sync.se.sesi.etiquetas','contract_id','Etiquetas')

    date_start = fields.Date(string='Fecha Inicio')
    date= fields.Date(string='Fecha Fin')
    quantity_yaros = fields.Integer('Cantidad')
    description = fields.Text(string='Plazos Condiciones')
    information = fields.Many2one('suscription.sale.order',string='Informacion')

    partner_contacts_id = fields.Many2one('res.partner','Contactos')
    email_partner_contacts = fields.Char('Email',related="partner_contacts_id.email")
    last_order_id = fields.Many2one('sale.order','Orden de Venta Activa',compute="get_last_order_id")

    def get_last_order_id(self):
        for i in self:
            if len(i.order_ids)>0:
                i.last_order_id = i.order_ids.sorted(lambda m: m.id)[-1].id
            else:
                i.last_order_id = False

    route_yaros_id = fields.Many2one('route.yaros','Rutas')
    format_delivery_id = fields.Many2one('format.delivery.yaros','Forma Entrega')
    sender_id = fields.Many2one('res.partner','Remitente Cortesia')
    courtesy = fields.Char('Cortesia')
    note = fields.Text(string='Nota')


    @api.model
    def create(self,vals):
        id_seq = self.env['ir.sequence'].search([('name','=','Suscripciones SE')], limit=1)        
        if not id_seq:
            id_seq = self.env['ir.sequence'].create({'name':'Suscripciones SE','implementation':'no_gap','active':True,'prefix':'SE-','padding':6,'number_increment':1,'number_next_actual' :1})
        vals['orden'] = id_seq._next()
        t = super(suscription_sale_order,self).create(vals)
        if not t.product_yaros_id.no_generar_etiqueta:
            data = {
                'orden':u'Suscripción en Odoo',
                'contract_id':t.id,
                'contactid': t.partner_contacts_id.id,
                'saludo': t.partner_contacts_id.id,
                'remitente':'Semana Económica',
                'fecha_registro':fields.Date.context_today(self),
                'cantidad': t.quantity_yaros,
                'state':'draft',
            }
            self.env['sync.se.sesi.etiquetas'].create(data)

        return t


    def write(self,vals):
        t = super(suscription_sale_order,self).write(vals)
        self.refresh()
        if 'state' in vals:
            for i in self:
                for l in i.etiquetas_ids:
                    l.state = vals['state']
        if 'partner_contacts_id' in vals:
            for i in self:
                for l in i.etiquetas_ids:
                    l.contactid = i.partner_contacts_id.id
                    l.saludo = i.partner_contacts_id.id

        return t


    def en_progreso(self):#draft,cancel,close,pending
        for i in self:
            i.state = 'open'            
            for l in i.etiquetas_ids:
                l.state = 'open'

    def para_renovar(self):#open
        for i in self:
            i.state = 'pending'
            for l in i.etiquetas_ids:
                l.state = 'pending'

    def cerrar_contrat(self):#draft,pending
        for i in self:
            i.state = 'close'
            for l in i.etiquetas_ids:
                l.state = 'close'

    def cancelar_contrat(self):#draft,pending
        for i in self:
            i.state = 'cancel'
            for l in i.etiquetas_ids:
                l.state = 'cancel'


class suscription_sale_order_etiquetas(models.Model):
    _name = 'sync.se.sesi.etiquetas'


    orden = fields.Char('Orden')
    contract_id = fields.Many2one('suscription.sale.order','Tipo Contrato')
    
    salesorderid = fields.Many2one('sale.order','SO Codigo',compute="get_salesorderid")
    numerodeordeninterno = fields.Char(string='Numero de Orden Interno',compute="get_salesorderid")

    def get_salesorderid(self):
        for i in self:
            if len(i.contract_id.order_ids) >0:                    
                sale = i.contract_id.order_ids.sorted(lambda r : r.id)[-1]
                i.salesorderid = sale.id
                i.numerodeordeninterno = sale.name
            else:
                i.salesorderid = False
                i.numerodeordeninterno = False

    contactid = fields.Many2one('res.partner','Contacto')
    saludo = fields.Many2one('res.partner','Señor')
    nombre = fields.Char(string='Nombre',compute="get_names")
    apellido = fields.Char(string='Apellido',compute="get_names")
    cargo = fields.Char(string='Cargo',compute="get_names")

    def get_names(self):
        for i in self:
            if i.contactid:
                i.nombre = ' '.join(i.contactid.name.split(' ')[:-2]) if i.contactid.name else ''
                i.apellido = ' '.join(i.contactid.name.split(' ')[-2:]) if i.contactid.name else ''
                i.cargo = i.contactid.title.name
            else:
                i.nombre = ''
                i.apellido = ''
                i.cargo = ''

    direccion = fields.Char(string='Direccion',related='contactid.street')
    distrito =fields.Many2one('res.country.state','Distrito',related='contactid.district_id')
    provincia =fields.Many2one('res.country.state','Provincia',related='contactid.province_id')
    pais = fields.Many2one('res.country','Pais',related='contactid.country_id')
    remitente = fields.Char(string='Remitente')
    fecha_registro = fields.Date(string='Fecha Registro')


    accountid = fields.Char('Cuenta')
    empresa_name = fields.Char('Empresa')
    cantidad = fields.Integer('Cantidad')
    fecha_inicio = fields.Date('Fecha Inicio')
    fecha_fin = fields.Date('Fecha Fin')
    state = fields.Selection([('draft','Nuevo'),('open','En Progreso'),('pending','Para Renovar'),('close','Cerrado'),('cancelled','Cancelado')],'Estado',default="draft")
    formaentrega = fields.Char('Forma de Entrega')
    product = fields.Many2one('product.product','Producto',related='contract_id.product_yaros_id')
    codproduct = fields.Char('Cod. Producto')
    prioridad = fields.Selection([('normal','Normal'),('urgent','Urgente'),('very_urgent','Muy Urgente')],'Prioridad')
    ruta = fields.Many2one('route.yaros','Ruta')
    tipo_revista = fields.Char('Tipo de Revista')
    orden_entrega = fields.Char('Orden Entrega')
    categoria = fields.Char('Categoria')
    propietario_cortesia = fields.Char('Propietario cortesia')

class sale_order_line_agent(models.Model):
    _name = 'sale.order.line.agent'

    order_line_id = fields.Many2one('sale.order.line','Linea de Pedido')
    agente = fields.Many2one('res.partner','Agente')
    comision = fields.Float(u'Comisión')


class Sale_Order_Line(models.Model):
    _inherit = 'sale.order.line'

    suscription_id = fields.Many2one('suscription.sale.order','Suscripcion')
    subscription_start_date  = fields.Date(string='Fecha Inio de Suscripcion')
    pw_original_price = fields.Float('Precio Original')
    pw_discount = fields.Float('Descuento Especial')
    agents = fields.One2many('sale.order.line.agent','order_line_id','Agentes y Comisiones')
    #periodo = fields.Char('Periodo')

    def open_agents(self):
        return {            
            'name': 'Agentes',
            'domain' : [('id','in',self.agents.ids)],
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line.agent',
            'context': {'default_order_line_id':self.id},
            'view_mode': 'tree',
        }



class Sale_Order(models.Model):
    _inherit = 'sale.order'

    ident_culqi = fields.Text("Culqi Identificador")
    suscription_count = fields.Integer(compute='_compute_suscription_count', string='Suscription Count')

    suscriptions_ids = fields.Many2many('suscription.sale.order','order_suscrpitions_rel','suscription_id','order_id','Suscriptions')
    assisted = fields.Boolean('Asistida')

    def _compute_suscription_count(self):
        for i in self:
            i.suscription_count = len( i.suscriptions_ids )

    def open_suscriptions(self):
        return {            
            'name': 'Suscripciones',
            'domain' : [('id','in',self.suscriptions_ids.ids)],
            'type': 'ir.actions.act_window',
            'res_model': 'suscription.sale.order',
            'view_mode': 'tree,form',
        }

            
class purchase_order(models.Model):
    _inherit = 'purchase.order'

    sale_order_agent_id = fields.Many2one('sale.order','Pedido de Venta Comisionable')







class SaleReport(models.Model):
    _inherit = "sale.report"

    f_ini_sol = fields.Date('F. Inicial')
    f_fin_sol = fields.Date('F. Final')
    f_ini_sus = fields.Date('Suscripción F. Inicial')
    f_fin_sus = fields.Date('Suscripción F. Final')
    suscripcion_name = fields.Char('Suscripción')
    f_entrega = fields.Date('Fecha Entrega')
    edicion = fields.Char('Edición')

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(l.id) as id,
            l.product_id as product_id,
            t.uom_id as product_uom,
            sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
            sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
            sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
            sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
            sum(l.price_total / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as price_total,
            sum(l.price_subtotal / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as price_subtotal,
            sum(l.untaxed_amount_to_invoice / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as untaxed_amount_to_invoice,
            sum(l.untaxed_amount_invoiced / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as untaxed_amount_invoiced,
            count(*) as nbr,
            s.name as name,
            s.date_order as date,
            s.state as state,
            s.partner_id as partner_id,
            s.user_id as user_id,
            s.company_id as company_id,
            s.campaign_id as campaign_id,
            s.medium_id as medium_id,
            s.source_id as source_id,
            extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
            t.categ_id as categ_id,
            s.pricelist_id as pricelist_id,
            s.analytic_account_id as analytic_account_id,
            s.team_id as team_id,
            p.product_tmpl_id,
            partner.country_id as country_id,
            partner.industry_id as industry_id,
            partner.commercial_partner_id as commercial_partner_id,
            sum(p.weight * l.product_uom_qty / u.factor * u2.factor) as weight,
            sum(p.volume * l.product_uom_qty / u.factor * u2.factor) as volume,
            l.discount as discount,
            sum((l.price_unit * l.product_uom_qty * l.discount / 100.0 / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END)) as discount_amount,
            s.id as order_id,
            l.subscription_start_date as f_ini_sol,
            l.fin as f_fin_sol,
            osr.names_sub  as suscripcion_name,
            sub.date_start as f_ini_sus,
            sub.date as f_fin_sus,
            (s.date_order - interval '5 hours')::date as f_entrega,
            pei.edition_name as edicion
        """

        fields['days_to_confirm'] = ", DATE_PART('day', s.date_order::timestamp - s.create_date::timestamp) as days_to_confirm"
        fields['invoice_status'] = ', s.invoice_status as invoice_status'

        for field in fields.values():
            select_ += field

        from_ = """
                sale_order_line l
                      join sale_order s on (l.order_id=s.id)
                      join res_partner partner on s.partner_id = partner.id
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join uom_uom u on (u.id=l.product_uom)
                    left join uom_uom u2 on (u2.id=t.uom_id)
                    left join product_pricelist pp on (s.pricelist_id = pp.id)
                    left join (
                            select osr_i.suscription_id ,min(osr_i.order_id) as order_id,sub_i.product_yaros_id as product_id, array_agg(sub_i.orden)::varchar as names_sub from
                            order_suscrpitions_rel osr_i
                            inner join suscription_sale_order sub_i on sub_i.id = osr_i.order_id
                            group by sub_i.product_yaros_id,EXTRACT(YEAR FROM date_start),EXTRACT(MONTH FROM date_start),suscription_id
                        ) as osr on osr.suscription_id = s.id and osr.product_id = l.product_id
                    left join suscription_sale_order sub on sub.id = osr.order_id
                    left join product_edition_it pei on pei.id = l.edition_id
                %s
        """ % from_clause

        groupby_ = """
            l.product_id,
            l.order_id,
            t.uom_id,
            t.categ_id,
            s.name,
            s.date_order,
            s.partner_id,
            s.user_id,
            s.state,
            s.company_id,
            s.campaign_id,
            s.medium_id,
            s.source_id,
            s.pricelist_id,
            s.analytic_account_id,
            s.team_id,
            p.product_tmpl_id,
            partner.country_id,
            partner.industry_id,
            partner.commercial_partner_id,
            l.discount,            
            l.subscription_start_date,
            l.fin,
            osr.names_sub,
            sub.date_start,
            sub.date,
            (s.date_order - interval '5 hours')::date,
            pei.edition_name,
            s.id %s
        """ % (groupby)

        groupby += ', s.invoice_status'

        return '%s (SELECT %s FROM %s WHERE l.product_id IS NOT NULL GROUP BY %s)' % (with_, select_, from_, groupby_)
