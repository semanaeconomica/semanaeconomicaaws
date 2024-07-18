# -*- coding: utf-8 -*-

from odoo import models, fields, api
from decimal import *
from odoo.exceptions import UserError
import json
from datetime import *
import urllib3
import re
import base64
from odoo.addons.payment.models.payment_acquirer import ValidationError

FACT_DATA_LABELS = ['Nro Documento Emisor : ', 'Tipo de Comprobante : ', 'Serie : ', 'Numero : ', 'IGV : ', 'Total : ',
                    'Fecha Emision : ',
                    'Tipo de Documento : ', 'Nro de Documento : ', 'Codigo Hash : ', '']


class AccountMoveFunctionsEbill(models.Model):
    _inherit = 'account.move'

    def generate_lines(self, line, advance_product, advance_regularization ,c=None, anticipos=None, c_anticipos=None):
        parameters = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        error = ''
        free = ['2', '3', '4', '5', '6', '7', '10', '11', '12', '13', '14', '15']
        if self.billing_type == '0':
            # taxes with Nubefact
            igv_type = next(filter(lambda tax: tax.eb_afect_igv_id, line.tax_ids)).eb_afect_igv_id.pse_code
        if self.billing_type == '1':
            # taxes with OdooFacturacion
            igv_type = next(filter(lambda tax: tax.eb_afect_igv_id, line.tax_ids)).eb_afect_igv_id.code
            free = ['11', '12', '13', '14', '15', '16', '21', '31', '32', '33', '34', '35', '36', '37']

        tax_included = next(filter(lambda t: t.price_include, line.tax_ids), None)
        tax_line = next(
            filter(lambda tax: tax.eb_tributes_type_id and tax.eb_tributes_type_id.code != '7152', line.tax_ids), None)
        tax_percentage = tax_line.amount / 100
        quantity = abs(line.quantity)
        #price_subtotal = float(Decimal(str(abs(line.price_subtotal))).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP))

        line._onchange_price_subtotal_origin()
        price_subtotal = abs(line.price_subtotal_origin)
        #raise ValidationError(price_subtotal)
        if tax_included:
            price = abs(line.price_unit / (1 + tax_percentage))
            price_igv = abs(line.price_unit)
        else:
            price = abs(line.price_unit)
            price_igv = abs(line.price_unit * (1 + tax_percentage))
        discount = abs((price * quantity) * (line.discount / 100))
        #raise ValidationError(line.tax_for_ebill)
        igv = abs(price_subtotal * tax_percentage)
        #raise ValidationError(str(igv) + "=" +str(price_subtotal)+"+"+str(tax_percentage))
        bag_tax = next(
            filter(lambda tax: tax.eb_tributes_type_id and tax.eb_tributes_type_id.code == '7152', line.tax_ids), None)
        bag_tax = quantity * bag_tax.amount if bag_tax else 0
        total = price_subtotal + igv + bag_tax
        onu_code = line.product_id.onu_code.code if advance_product != line.product_id and line.product_id.type in [
            'service', 'product'] else ""
        rounded = int(parameters.rounded_ebill_line)
        if line.einvoice_line_id:
            if line.einvoice_line_id.save_changes:
                eil = line.einvoice_line_id
                price = eil.unit_value
                price_igv = eil.unit_price
                discount = eil.discount_value
                igv_type = eil.igv_type
                price_subtotal = eil.subtotal
                igv = eil.igv
                bag_tax = eil.icbper
                total = eil.total

        price = round(price, rounded)
        price_igv = round(price_igv, rounded)

        price_subtotal_origin = round(price_subtotal, 10)
        price_subtotal = round(price_subtotal, rounded)

        igv = round(igv,rounded)
        igv_origin = round(igv, 10)

        bag_tax = round(bag_tax,10)

        total = round(total,rounded)
        total_origin = round(total, 10)


        #raise ValidationError(total)

        if self.billing_type == '0':
            # Creating json line to send to Nubefact
            unidad_medida = 'ZZ' if line.product_id.type == 'service' else 'NIU'
            if line.product_uom_id.code_sunat:
                unidad_medida = line.product_uom_id.code_sunat.code

            ebill_line = {
                "unidad_de_medida": unidad_medida,
                "codigo": line.product_id.default_code if line.product_id.default_code else '',
                "descripcion": line.name + ' (Gratuita)' if igv_type in free else line.name,
                "cantidad": quantity,
                "valor_unitario": price,
                "precio_unitario": price_igv,
                "descuento": discount,
                "subtotal": price_subtotal,
                "tipo_de_igv": igv_type,
                "igv": 0 if igv_type in free else igv,
                "impuesto_bolsas": bag_tax,
                "total": total,
                "anticipo_regularizacion": "false",
                "anticipo_documento_serie": "",
                "anticipo_documento_numero": "",
                "codigo_producto_sunat": onu_code if onu_code else ""
                # "tipo_de_isc": tipo_isc Tipo de ISC (1, 2 o 3)
                # "isc": Monto de ISC por línea
            }
        if self.billing_type == '1':
            # Creating json line to send to OdooFacturacion
            if not line.move_advance_line_id:
            #if not advance_regularization:
                ebill_line = {
                    "unidad_de_medida": 'ZZ' if line.product_id.type == 'service' else 'NIU',
                    "codigo_interno": line.product_id.default_code if line.product_id.default_code else '',
                    "descripcion": line.name + ' (Trans.Gratuita)' if igv_type in free else line.name,
                    "cantidad": quantity,
                    "valor_unitario": 0.00 if igv_type in free else price,
                    "codigo_tipo_precio": "02" if igv_type in free else "01",
                    "precio_unitario": price_igv,
                    "descuento": discount,
                    "total_base_igv": price_subtotal,
                    "codigo_tipo_afectacion_igv": igv_type,
                    "porcentaje_igv": (tax_percentage * 100),
                    "total_valor_item": price_subtotal,
                    "total_igv": igv,
                    "total_icbper": bag_tax,
                    "total_impuestos": (igv + bag_tax),
                    "total_item": total,
                    "anticipo_regularizacion": "false",
                    "codigo_producto_sunat": onu_code if onu_code else ""
                }
            else:
                c_ebill_line = {
                    "unidad_de_medida": 'ZZ' if line.product_id.type == 'service' else 'NIU',
                    "codigo_interno": line.product_id.default_code if line.product_id.default_code else '',
                    "descripcion": line.name + ' (Trans.Gratuita)' if igv_type in free else line.name,
                    "cantidad": quantity,
                    "valor_unitario": 0.00 if igv_type in free else price,
                    "codigo_tipo_precio": "02" if igv_type in free else "01",
                    "precio_unitario": price_igv,
                    "descuento": discount,
                    "total_base_igv": price_subtotal,
                    "codigo_tipo_afectacion_igv": igv_type,
                    "porcentaje_igv": (tax_percentage * 100),
                    "total_valor_item": price_subtotal,
                    "total_igv": igv,
                    "total_icbper": bag_tax,
                    "total_impuestos": (igv + bag_tax),
                    "total_item": total,
                    "anticipo_regularizacion": "false",
                    "codigo_producto_sunat": onu_code if onu_code else ""
                }
                c_anticipos.append(c_ebill_line)
                ebill_line = None
        # Creating altern line to save into another model just for informative reasons
        einvoice_line = {
            'move_line_id': line.id,
            'code': line.product_id.default_code,
            'uom': 'ZZ' if line.product_id.type == 'service' else 'NIU',
            'unit_value': price,
            'unit_price': price_igv,
            'discount_value': discount,
            'percentage_discount': line.discount,
            'sunat_product_code': onu_code,
            'igv_type': igv_type,
            'subtotal': price_subtotal,
            'subtotal_origin': price_subtotal_origin,
            'igv': igv,
            'igv_origin': igv_origin,
            'icbper': bag_tax,
            'total': total,
            'total_origin': total_origin,
            'advance_regularization': False
        }
        '''
        if advance_regularization:
            series = self.advance_ids.mapped('serie')
            numbers = self.advance_ids.mapped('number')
        '''
        if line.move_advance_line_id:
            if not line.move_advance_line_id:
                raise ValidationError('indique el anticipo')
            anticipo = line.move_advance_line_id[0]


            #series = self.advance_ids.mapped('serie')
            serie = anticipo.serie
            numbs = anticipo.number
            #numbers = self.advance_ids.mapped('number')
            einvoice_line['advance_regularization'] = True
            if self.billing_type == '0':
                # Creating json line to send to Nubefact
                ebill_line['anticipo_regularizacion'] = "true"
                ebill_line['anticipo_documento_serie'] = einvoice_line['advance_document_serie'] = serie
                ebill_line['anticipo_documento_numero'] = einvoice_line['advance_document_number'] = numbs
                #validar el  total del anticipo con el total de la linea del anticipo
                if anticipo:
                    fact_anticipo = anticipo.anticipo_id
                    if fact_anticipo.einvoice_id.total_voucher != total:
                        error += f'''\n El monto {total} de la 
                                        linea {line.product_id.name} con el monto  {fact_anticipo.einvoice_id.total_voucher} facturado del anticipo no coincidem'''


            if self.billing_type == '1':
                # Creating json line to send to OdooFacturacion
                item_anticipo = {
                    "numero": serie + "-" + numbs,
                    "codigo_tipo_documento": "02",
                    "monto": price_subtotal
                }
                anticipos.append(item_anticipo)
        #line.einvoice_line_id.unlink()
        if not line.einvoice_line_id:
            line.write({'einvoice_line_id': self.env['einvoice.line'].create(einvoice_line).id})
        else:
            line.einvoice_line_id.update(einvoice_line)
        #raise UserError(str(ebill_line))
        return {
            'ebill_line': ebill_line,
            'einvoice_line': einvoice_line,
            'error': error
        }


    def body_function_ebill(self,parameters):
        error = ''
        self.verify_invoice_data(parameters)
        DetractionCodes = parameters.catalog_51_detraction_ids.mapped('code')
        AdvancesCodes = parameters.catalog_51_advance_ids.mapped('pse_code')

        # Defining variables
        ebill_lines, m_anticipos, c_anticipos, invoice_with_advance, exportation = [], [], [], False, None
        total_saved, total_free, total_exonerate, total_inafect, total_export, total_discount, total_igv, total_advance, total_icbper = 0, 0, 0, 0, 0, 0, 0, 0, 0
        einvoice_lines = []
        # stupid counter
        c = 0

        for line in self.invoice_line_ids:
            exportation_type = next(
                filter(lambda tax: tax.eb_afect_igv_id and tax.eb_afect_igv_id.code == '40', line.tax_ids), None)
            if exportation_type:
                exportation = True if exportation_type.eb_tributes_type_id.code == '9995' else False
            advance_product = next(
                filter(lambda a_line: a_line.product_id == line.product_id, parameters.advance_product_ids), None)
            if advance_product and self.op_type_sunat_id.pse_code in AdvancesCodes:
                if self.billing_type == '0':
                    resx = self.generate_lines(line, advance_product, True, c, m_anticipos, c_anticipos)
                    ebill_lines.append(resx['ebill_line'])
                    einvoice_lines.append(resx['einvoice_line'])
                    if resx['error'] != '':
                        error += resx['error']
                if self.billing_type == '1':
                    resx = self.generate_lines(line, advance_product, True, c, m_anticipos, c_anticipos)
                    if resx['error'] != '':
                        error += resx['error']

                    total_advance += abs(line.price_subtotal)
                # raise UserError(str(ebill_lines))
                c += 1
            # if not advance_product or not self.op_type_sunat_id.code in AdvancesCodes:
            else:
                resx = self.generate_lines(line, advance_product, False)
                ebill_lines.append(resx['ebill_line'])
                einvoice_lines.append(resx['einvoice_line'])
                if resx['error'] != '':
                    error += resx['error']

        #raise ValidationError(str(ebill_lines))
        #raise ValidationError(error)

        # raise UserError(str(ebill_lines))
        # Defining flag to know if the invoice is free or not
        free_flag = True
        counter = 0
        for e_line in ebill_lines:
            if self.billing_type == '0':
                # Creating json's totals to send to Nubefact
                total_icbper += e_line['impuesto_bolsas']
                total_discount += e_line['descuento']
                if e_line['anticipo_regularizacion'] == "true":
                    total_igv -= e_line['igv']
                else:
                    if e_line['tipo_de_igv'] not in ['2', '3', '4', '5', '6', '7', '10', '11', '12', '13', '14', '15']:
                        total_igv += e_line['igv']
                if e_line['tipo_de_igv'] in ['1']:
                    free_flag = False
                    if e_line['anticipo_regularizacion'] == "true":
                        #total_saved -= e_line['subtotal']
                        total_saved -= einvoice_lines[counter]['subtotal_origin']
                    else:
                        #total_saved += e_line['subtotal']
                        total_saved += einvoice_lines[counter]['subtotal_origin']
                if e_line['tipo_de_igv'] in ['2', '3', '4', '5', '6', '7', '10', '11', '12', '13', '14', '15']:
                    #total_free += e_line['subtotal']
                    total_free += einvoice_lines[counter]['subtotal_origin']
                if e_line['tipo_de_igv'] in ['8']:
                    free_flag = False
                    if e_line['anticipo_regularizacion'] == "true":
                        #total_exonerate -= e_line['subtotal']
                        total_exonerate -= einvoice_lines[counter]['subtotal_origin']
                    else:
                        #total_exonerate += e_line['subtotal']
                        total_exonerate += einvoice_lines[counter]['subtotal_origin']
                if e_line['tipo_de_igv'] in ['9']:
                    free_flag = False
                    if e_line['anticipo_regularizacion'] == "true":
                        #total_inafect -= e_line['subtotal']
                        total_inafect -= einvoice_lines[counter]['subtotal_origin']
                    else:
                        #total_inafect += e_line['subtotal']
                        total_inafect += einvoice_lines[counter]['subtotal_origin']
                if e_line['tipo_de_igv'] in ['16']:
                    if exportation:
                        #total_inafect += e_line['subtotal']
                        total_inafect += einvoice_lines[counter]['subtotal_origin']
                        free_flag = False
                    else:
                        #total_free += e_line['subtotal']
                        total_free += einvoice_lines[counter]['subtotal_origin']
                if e_line['anticipo_regularizacion'] == "true":
                    invoice_with_advance = True
                    #total_advance += e_line['subtotal']
                    total_advance += einvoice_lines[counter]['subtotal_origin']
                    free_flag = False

                counter += 1

            if self.billing_type == '1':
                # Creating json's totals to send to OdooFacturacion

                total_icbper += e_line['total_icbper']
                total_discount += e_line['descuento']
                if e_line['anticipo_regularizacion'] == "true":
                    total_igv -= e_line['total_igv']
                else:
                    if e_line['codigo_tipo_precio'] == "01":
                        total_igv += e_line['total_igv']
                if e_line['codigo_tipo_afectacion_igv'] in ['10']:
                    free_flag = False
                    total_saved += e_line['total_valor_item']
                if e_line['codigo_tipo_afectacion_igv'] in ['11', '12', '13', '14', '15', '16', '21', '31', '32', '33',
                                                            '34', '35', '36', '37']:
                    total_free += e_line['total_item']
                if e_line['codigo_tipo_afectacion_igv'] in ['20']:
                    total_exonerate += e_line['total_valor_item']
                    free_flag = False
                if e_line['codigo_tipo_afectacion_igv'] in ['30']:
                    total_inafect += e_line['total_valor_item']
                    free_flag = False
                if e_line['codigo_tipo_afectacion_igv'] in ['40']:
                    if exportation:
                        total_inafect += e_line['total_valor_item']
                        free_flag = False
                    else:
                        total_free += e_line['total_valor_item']


            # else:
            #	invoice_with_advance = True
            #	#total_advance +=  e_line['total_valor_item']
            #	free_flag = False

        if self.billing_type == '1' and c > 0:
            for c_line in c_anticipos:
                total_igv -= c_line['total_igv']
                total_saved -= c_line['total_valor_item']

        #total_saved = float(Decimal(str(abs(total_saved))).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP))

        #total_igv = float(Decimal(str(abs(total_igv))).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP))

        head_total = total_saved + total_inafect + total_exonerate + total_igv
        #raise ValidationError(str(head_total)+"="+str(total_saved)+"+"+str(total_inafect)+"+"+str(total_exonerate)+"+"+str(total_igv))


        invoice_footer = self.narration if parameters.comment_add_check and self.narration else ""
        invoice_footer += ('<br>' + parameters.bank_numbers) if parameters.bank_numbers else ""

        #buscar datos si ya tiene invoice line
        if self.einvoice_id:
            if self.einvoice_id.save_changes:
                ei = self.einvoice_id
                total_saved = ei.total_saved
                total_inafect = ei.total_inafect
                total_exonerate = ei.total_exonerate
                total_free = ei.total_free
                total_discount = ei.total_discount
                total_advance = ei.total_advance
                total_igv = ei.total_igv
                total_icbper = ei.total_icbper
                head_total = ei.total_voucher

        rounded = int(parameters.rounded_ebill)
        head_total = round(head_total, rounded)
        total_icbper = round(total_icbper, rounded)
        total_igv = round(total_igv, rounded)
        total_advance = round(total_advance, rounded)
        total_discount = round(total_discount, rounded)
        total_free = round(total_free, rounded)
        total_exonerate = round(total_exonerate, rounded)
        total_inafect = round(total_inafect,rounded)
        total_saved = round(total_saved,rounded)


        sent_purchase_doc = self.doc_origin_customer if self.doc_origin_customer else ""

        if self.billing_type == '0':
            # Creating json's header to send to Nubefact
            ebill_json = {
                "operacion": "generar_comprobante",
                "tipo_de_comprobante": self.type_document_id.pse_code,
                "serie": self.ref.split('-')[0],
                "numero": int(self.ref.split('-')[1]),
                "sunat_transaction": int(self.op_type_sunat_id.pse_code),
                "cliente_tipo_de_documento": self.partner_id.commercial_partner_id.l10n_latam_identification_type_id.code_sunat,
                "cliente_numero_de_documento": self.partner_id.commercial_partner_id.vat,
                "cliente_denominacion": self.partner_id.commercial_partner_id.name,
                "cliente_direccion": self.partner_id.street,
                "cliente_email": self.partner_id.email if self.partner_id.email else "",
                "cliente_email_1": "",
                "cliente_email_2": "",
                "fecha_de_emision": datetime.strftime(self.invoice_date, '%Y-%m-%d'),
                "fecha_de_vencimiento": datetime.strftime(self.invoice_date_due, '%Y-%m-%d'),
                "moneda": self.currency_id.pse_code,
                "tipo_de_cambio": self.currency_rate if self.currency_id.name != 'PEN' else "",
                "porcentaje_de_igv": float(
                    Decimal(str(parameters.igv_tax_id.amount)).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)),
                "descuento_global": "",
                "total_descuento": total_discount,
                "total_anticipo": total_advance,
                "total_gravada": total_saved,
                "total_inafecta": total_inafect,
                "total_exonerada": total_exonerate,
                "total_igv": total_igv,
                "total_gratuita": total_free,
                "total_otros_cargos": "",
                "total_impuestos_bolsas": total_icbper,
                "total": head_total,
                "percepcion_tipo": "",
                "percepcion_base_imponible": "",
                "total_percepcion": "",
                "total_incluido_percepcion": "",
                "detraccion": "true" if self.op_type_sunat_id.code in DetractionCodes else "false",
                "detraccion_tipo": int(
                    self.detraction_type_id.pse_code) if self.op_type_sunat_id.code in DetractionCodes else "",
                "detraccion_total": self.detraction_amount if self.op_type_sunat_id.code in DetractionCodes else 0,
                "medio_de_pago_detraccion": self.detraction_payment_id.pse_code if self.op_type_sunat_id.code in DetractionCodes else "",
                "observaciones": "Pedido: {0}\n{1}".format(self.invoice_origin,
                                                           invoice_footer) if parameters.invoice_origin_check and self.invoice_origin else (
                    invoice_footer),
                "documento_que_se_modifica_tipo": self.doc_invoice_relac[
                    0].type_document_id.pse_code if self.type_document_id.pse_code in ['3', '4'] else "",
                "documento_que_se_modifica_serie": self.doc_invoice_relac[0].nro_comprobante.split('-')[
                    0] if self.type_document_id.pse_code in ['3', '4'] else "",
                "documento_que_se_modifica_numero": self.doc_invoice_relac[0].nro_comprobante.split('-')[
                    1] if self.type_document_id.pse_code in ['3', '4'] else "",
                "tipo_de_nota_de_credito": int(
                    self.credit_note_type_id.code) if self.type == 'out_refund' and self.type_document_id.pse_code == '3' else "",
                "tipo_de_nota_de_debito": int(
                    self.debit_note_type_id.code) if self.type == 'out_invoice' and self.type_document_id.pse_code == '4' else "",
                "enviar_automaticamente_a_la_sunat": "true",
                "enviar_automaticamente_al_cliente": "true" if self.partner_id.email else "false",
                "codigo_unico": "",
                "condiciones_de_pago": self.invoice_payment_term_id.name if self.invoice_payment_term_id else "",
                "medio_de_pago": "",
                "placa_vehiculo": "",
                "orden_compra_servicio": sent_purchase_doc,
                "tabla_personalizada_codigo": "",
                "formato_de_pdf": ""
            }

            # agregando plazo de pagos
            plazos = self.invoice_payment_term_id.line_ids
            total_dias = 0
            for p in plazos:
                total_dias += p.days
            json_plazos = []

            if self.retencion_amount < 0:
                raise ValidationError('El campo "Retencion" no debe ser negativo')
            if total_dias > 0:

                #if  self.partner_id.is_partner_retencion and self.retencion_amount <= 0:
                #    raise ValidationError(' El campo "Retencion" tiene que ser mayor a cero.')
                index = 0
                amount_accumulated = 0
                fecha = datetime.strptime(str(self.invoice_date), '%Y-%m-%d')
                #fecha = self.invoice_date
                if parameters.send_multi_credits:
                    for p in plazos:
                        index += 1
                        if p.option == 'day_after_invoice_date':
                            fecha = fecha + timedelta(days=(p.days))
                            #fecha = fecha.strftime('%d-%m-%Y')
                            str_date = f'''{fecha.day}/{fecha.month}/{fecha.year}'''
                        if p.option in ['after_invoice_month', 'day_following_month']:
                            if not p.day_of_the_month > 0:
                                raise ValidationError('dia del mes invalido')
                            next_mes = int(fecha.month) + 1
                            str_date = f'''{p.day_of_the_month}/{next_mes}/{fecha.year}'''
                            #fecha = datetime.strptime(str_date, '%Y-%m-%d')
                        if p.option in ['day_current_month']:
                            if not p.day_of_the_month > 0:
                                raise ValidationError('dia del mes invalido')
                            str_date = f'''{p.day_of_the_month}/{fecha.month}/{fecha.year}'''
                            #fecha = datetime.strptime(str_date, '%Y-%m-%d')

                        importe = None
                        if p.value == 'balance':
                            importe = head_total - amount_accumulated
                        if p.value == 'percent':
                            importe = p.value_amount * head_total / 100
                        if p.value == 'fixed':
                            importe = p.value_amount

                        amount_accumulated += importe
                        if fecha and importe:
                            json_plazos.append({
                                "cuota": index,
                                # "cuota": 1,
                                "fecha_de_pago": str_date,
                                "importe": round(importe - self.retencion_amount, 10) if index == 1 else round(importe, 10)
                            })
                else:
                    fecha = fecha + timedelta(days=(total_dias))
                    str_date = f'''{fecha.day}/{fecha.month}/{fecha.year}'''
                    json_plazos.append({
                         "cuota": 1,
                         "fecha_de_pago": str_date,
                         "importe": round(head_total - self.retencion_amount , 10)
                    })

                #raise ValidationError(index)
                #raise ValidationError(str(json_plazos))
                if json_plazos:
                    ebill_json.update({"venta_al_credito": json_plazos})
                    ebill_json["medio_de_pago"] = 'credito'


        if self.billing_type == '1':
            # Creating json's header to send to OdooFacturacion
            datos_del_cliente = {
                "codigo_tipo_documento_identidad": self.partner_id.commercial_partner_id.l10n_latam_identification_type_id.code_sunat,
                "numero_documento": self.partner_izzzzzd.commercial_partner_id.vat,
                "apellidos_y_nombres_o_razon_social": self.partner_id.commercial_partner_id.name,
                "direccion": self.partner_id.street,
                "correo_electronico": self.partner_id.email or self.commercial_partner_id.email or "",
                "codigo_pais": "PE",
                "ubigeo": ""
            }
            m_totales = {
                "total_descuentos": "%.6f" % total_discount,
                "total_anticipos": "%.2f" % total_advance,
                "total_operaciones_gravadas": "%.2f" % abs(total_saved),
                "total_operaciones_inafectas": "%.2f" % abs(total_inafect),
                "total_operaciones_exoneradas": "%.2f" % abs(total_exonerate),
                "total_operaciones_gratuitas": "%.2f" % abs(total_free),
                "total_exportacion": 0.00,
                "total_icbper": "%.2f" % total_icbper,
                "total_igv": "%.2f" % abs(total_igv),
                "total_impuestos": "%.2f" % abs(total_igv + total_icbper),
                "total_valor": "%.2f" % total_saved,
                "total_venta": "%.2f" % head_total
            }
            m_acciones = {
                "formato_pdf": "a4"
            }
            o_observaciones = '<b>Forma de pago: </b>%s<br>' % self.invoice_payment_term_id.name if self.invoice_payment_term_id else ""
            o_observaciones += '<b>Pedido:</b> {0}\n{1}'.format(self.invoice_origin,
                                                                invoice_footer) if parameters.invoice_origin_check and self.invoice_origin else invoice_footer




            ebill_json = {
                "codigo_tipo_operacion": self.op_type_sunat_id.code,
                "codigo_tipo_documento": self.type_document_id.code,
                "serie_documento": self.ref.split('-')[0],
                "numero_documento": int(self.ref.split('-')[1]),
                "fecha_de_emision": datetime.strftime(self.invoice_date, '%Y-%m-%d'),
                "fecha_de_vencimiento": datetime.strftime(self.invoice_date_due, '%Y-%m-%d'),
                "hora_de_emision": str(fields.Datetime.now()),
                "codigo_tipo_moneda": self.currency_id.name,
                # "tipo_de_cambio": self.currency_rate if self.currency_id.name != 'PEN' else "",
                "informacion_adicional": o_observaciones,
                "enviar_automaticamente_al_cliente": "true" if self.partner_id.email else "false",
                "codigo_unico": "",
                "condiciones_de_pago": self.invoice_payment_term_id.name if self.invoice_payment_term_id else "",
                "medio_de_pago": "",
                # "placa_vehiculo": "",
                "numero_orden_de_compra": sent_purchase_doc
            }
            if self.type_document_id.code in ['07', '08']:
                ebill_json.update({
                    'motivo_o_sustento_de_nota': self.credit_note_type_id.name if self.type_document_id.code in [
                        '07'] else self.debit_note_type_id.name})
                tipo_nota = '01'
                for fac_relacionada in self.doc_invoice_relac:
                    fact = self.env['account.move'].search(
                        [('ref', '=', fac_relacionada.nro_comprobante), ('type', '=', 'out_invoice'),
                         ('type_document_id', '=', fac_relacionada.type_document_id.id)])
                    afecta_ext = ""
                    tipo_nota = fac_relacionada.type_document_id.code
                    if len(fact) > 0:
                        if fact[0].codigo_unico:
                            afecta_ext = fact[0].codigo_unico
                            m_documento_afectado = {
                                "external_id": str(afecta_ext)
                            }
                        else:
                            m_documento_afectado = {
                                "codigo_tipo_documento": fac_relacionada.type_document_id.code,
                                "serie_documento": fac_relacionada.nro_comprobante.split('-')[0],
                                "numero_documento": fac_relacionada.nro_comprobante.split('-')[1]
                            }
                    else:
                        m_documento_afectado = {
                            "codigo_tipo_documento": fac_relacionada.type_document_id.code,
                            "serie_documento": fac_relacionada.nro_comprobante.split('-')[0],
                            "numero_documento": fac_relacionada.nro_comprobante.split('-')[1]
                        }
                ebill_json.update({'codigo_tipo_nota': tipo_nota})
                ebill_json.update({'documento_afectado': m_documento_afectado})
            ebill_json.update({"datos_del_cliente_o_receptor": datos_del_cliente})
            ebill_json.update({"totales": m_totales})
            ebill_json.update({"acciones": m_acciones})
            if len(m_anticipos) > 0:
                ebill_json.update({"anticipos": m_anticipos})

        # Add guides info
        guide_lines = []

        if len(self.guide_line_ids) > 0 and self.type_document_id.code in ['01']:
            for guide in self.guide_line_ids:
                if not guide.numberg:
                    raise UserError(u'El # Guia de Remision no esta establecido en su albarán.')
                if self.billing_type == '0':
                    # Creating json's guias to send to Nubefact
                    guide_lines.append({
                        "guia_tipo": 1,
                        "guia_serie_numero": self.check_format_numberg(guide.numberg)
                    })
                if self.billing_type == '1':
                    # Creating json's guias to send to OdooFacturacion
                    guide_lines.append({
                        "codigo_tipo_documento": "09",
                        "numero": self.check_format_numberg(guide.numberg)
                    })

            ebill_json.update({"guias": guide_lines})



        ebill_json.update({"items": ebill_lines})
        # Creating alternative header just for informative reasons
        einvoice = {
            "move_id": self.id,
            "total_saved": total_saved,
            "total_inafect": total_inafect,
            "total_exonerate": total_exonerate,
            "total_free": total_free,
            "total_discount": total_discount,
            "total_advance": total_advance,
            "total_igv": total_igv,
            "total_icbper": total_icbper,
            "total_voucher": head_total
        }


        # raise UserError(str(ebill_json))
        self.json_sent = str(ebill_json)
        k = str(head_total)

        # Deleting Informative table in case exits one cause i don't want to have trash data
        #self.einvoice_id.unlink()
        #raise UserError(str(einvoice))
        if not self.einvoice_id:
            self.write({'einvoice_id': self.env['einvoice'].create(einvoice).id})
        else:
            self.einvoice_id.update(einvoice)
        k2 = str(self.einvoice_id.total_voucher)
        return  {
            'error': error,
            'ebill_json': ebill_json
        }

    def validate_ebill(self):
        parameters = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        error = ''
        res = self.body_function_ebill(parameters)
        ebill_json = res['ebill_json']
        if res['error'] != '':
            error += res['error']
        self._compute_amount_origin()
        total_amount  = self.amount_total if parameters.verify_amount_odoo else round(self.amount_total_origin,10)
        total_amount = round(total_amount,2)
        total_json = round(self.einvoice_id.total_voucher,self.currency_id.decimal_places) if parameters.verify_amount_odoo else round(self.einvoice_id.total_voucher,10)
        #total_json = round(self.einvoice_id.total_voucher, 10)
        total_json = total_json + self.einvoice_id.total_free

        total_json = round(total_json,2)


        if parameters.verify_amount_odoo:
            if total_json != total_amount:
                msg = "\n El monto Total de la Factura {}".format(
                    total_amount) + " y Monto de JSON + la grauita {} es diferente".format(total_json)
                error += msg

        return {
            'error': error,
            'ebill_json': ebill_json
        }


    def send_ebill(self):
        error = ''
        #funcion que valida la data a enviar en el ebill
        res =  self.validate_ebill()

        ebill_json = res['ebill_json']
        if res['error'] != '':
            error += res['error']



        if error != '':
            return self.env['popup.it'].get_message(error)

        #raise ValidationError(str(ebill_json))

        if not self.einvoice_id:
            return self.env['popup.it'].get_message("Por favor vuelva a Validar CPE para que se recalculen los datos a Facturar.")
        parameters = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)

        fact_line = next(filter(lambda s: s.serie_id == self.serie_id and s.billing_type == parameters.billing_type,
                                parameters.serial_nubefact_lines))
        #ebill_json = json.loads(self.json_sent)


        http = urllib3.PoolManager()
        try:
            if self.billing_type == '0':
                r = http.request('POST',
                                 fact_line.nubefact_path,
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': 'Token token = "%s"' % fact_line.nubefact_token},
                                 body=json.dumps(ebill_json))
            if self.billing_type == '1':
                r = http.request('POST',
                                 fact_line.nubefact_path + '/documents',
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': 'Bearer %s' % fact_line.nubefact_token},
                                 body=json.dumps(ebill_json))
        except urllib3.exceptions.HTTPError as e:
            raise UserError("Error al intentar conectarse: \n\t %s" % e.reason)
        response = json.loads(r.data.decode('utf-8'))
        if self.billing_type == '0':
            if 'errors' in response:
                raise UserError('Respuesta del Facturador: ' + response['errors'])
            if 'codigo_hash' in response:
                self.hash_code = response['codigo_hash']
            if 'enlace_del_pdf' in response:
                self.print_version = response['enlace_del_pdf']
                pdf = http.request('GET', response['enlace_del_pdf'])
            if 'enlace_del_xml' in response:
                self.xml_version = response['enlace_del_xml']
            if 'enlace_del_cdr' in response:
                self.cdr_version = response['enlace_del_cdr']
            if 'cadena_para_codigo_qr' in response:
                self.qr_code = response['cadena_para_codigo_qr']
            if 'aceptada_por_sunat' in response:
                self.sunat_state = '3'
            self.json_response = str(response)
        if self.billing_type == '1':
            if response['success']:
                self.hash_code = response['data']['hash']
                self.print_version = response['links']['pdf']
                pdf = http.request('GET', response['links']['pdf'])
                # self.binary_version = base64.encodestring(''.join(pdf.readlines()))
                self.xml_version = response['links']['xml']
                self.cdr_version = response['links']['cdr']
                self.qr_code = response['data']['qr_text']
                self.codigo_unico = response['data']['external_id']
                self.sunat_state = '3'
            else:
                raise UserError('Respuesta del Facturador: ' + response['message'])

        return self.env['popup.it'].get_message("SE ENVIO EL COMPROBANTE SATISFACTORIAMENTE")

    def query_ebill(self):
        parameters = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        fact_line = next(filter(lambda s: s.serie_id == self.serie_id and s.billing_type == parameters.billing_type,
                                parameters.serial_nubefact_lines))
        if not self.type_document_id.pse_code:
            raise UserError('El Tipo de Documento no tiene Codigo de Facturador')
        if not self.ref:
            raise UserError('No existe una referencia definida')
            if len(self.ref.split('-')) != 2:
                raise UserError('La referencia no tiene el formato adecuado "Ejem: F001-000002"')
        if self.billing_type == '0':
            ebill_json = {
                "operacion": "consultar_comprobante",
                "tipo_de_comprobante": self.type_document_id.pse_code,
                "serie": self.ref.split('-')[0],
                "numero": self.ref.split('-')[1],
            }
        if self.billing_type == '1':
            ebill_json = {
                "tipo_de_comprobante": self.type_document_id.pse_code,
                "serie": self.ref.split('-')[0],
                "numero": self.ref.split('-')[1],
            }
        http = urllib3.PoolManager()
        try:
            if self.billing_type == '0':
                r = http.request('POST',
                                 fact_line.nubefact_path,
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': 'Token token = "%s"' % fact_line.nubefact_token},
                                 body=json.dumps(ebill_json))
            if self.billing_type == '1':
                r = http.request('POST',
                                 fact_line.nubefact_path + 'documents/status',
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': 'Bearer %s' % fact_line.nubefact_token},
                                 body=json.dumps(ebill_json))
        except urllib3.exceptions.HTTPError as e:
            raise UserError("Error al intentar conectarse: \n\t %s" % e.reason)
        response = json.loads(r.data.decode('utf-8'))
        # raise UserError(str(response))
        self.json_response_consulta = str(response)
        if 'errors' in response:
            raise UserError(response['errors'])
        if 'codigo_hash' in response:
            self.hash_code = response['codigo_hash']
        if 'enlace_del_pdf' in response:
            self.print_version = response['enlace_del_pdf']
        if 'enlace_del_xml' in response:
            self.xml_version = response['enlace_del_xml']
        if 'enlace_del_cdr' in response:
            self.cdr_version = response['enlace_del_cdr']
        if 'cadena_para_codigo_qr' in response:
            self.qr_code = response['cadena_para_codigo_qr']
        if 'aceptada_por_sunat' in response:
            self.sunat_state = '1' if response['aceptada_por_sunat'] else '2'
        if 'sunat_description' in response and 'cadena_para_codigo_qr' in response:
            return self.env['popup.it'].get_message(
                'RESPUESTA DEL FACTURADOR: \n %s \n Con la siguiente data: \n %s' % (
                    response['sunat_description'],
                    '\n'.join(FACT_DATA_LABELS[c] + str(i) for c, i in
                              enumerate(response['cadena_para_codigo_qr'].split('|')))
                )
            )

    def send_delete(self):
        parameters = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        fact_line = next(filter(lambda s: s.serie_id == self.serie_id and s.billing_type == parameters.billing_type,
                                parameters.serial_nubefact_lines))
        if not self.delete_reason:
            raise UserError('Es necesario especificar una Razon de Baja')
        ebill_json = {
            "operacion": "generar_anulacion",
            "tipo_de_comprobante": self.type_document_id.pse_code,
            "serie": self.ref.split('-')[0],
            "numero": int(self.ref.split('-')[1]),
            "motivo": self.delete_reason,
            "codigo_unico": ""
        }
        http = urllib3.PoolManager()
        try:
            if self.billing_type == '0':
                r = http.request('POST',
                                 fact_line.nubefact_path,
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': 'Token token = "%s"' % fact_line.nubefact_token},
                                 body=json.dumps(ebill_json))
        except urllib3.exceptions.HTTPError as e:
            raise UserError("Error al intentar conectarse: \n\t %s" % e.reason)
        response = json.loads(r.data.decode('utf-8'))
        # raise UserError(str(response))
        if self.billing_type == '0':
            if 'errors' in response:
                raise UserError('Respuesta del Facturador: ' + response['errors'])
            if 'sunat_ticket_numero':
                self.sunat_ticket_number = response['sunat_ticket_numero']
            if 'enlace_del_pdf':
                self.print_version = response['enlace_del_pdf']
            if 'enlace_del_xml':
                self.xml_version = response['enlace_del_xml']

        return self.env['popup.it'].get_message("SE ENVIO EL COMUNICADO DE BAJA CORRECTAMENTE")

    # Function to be sure that the data is correct
    def verify_invoice_data(self, parameters):
        if self.hash_code:
            raise UserError('Este documento ya fue enviado')
        if not parameters.igv_tax_id:
            raise UserError(
                'No se ha configurado un Impuesto IGV en Parametros Generales de Contabilidad en la Pestaña de Facturacion Electronica')
        if not parameters.advance_product_ids:
            raise UserError(
                'No se ha configurado ningun Producto Anticipo en Parametros Generales de Contabilidad en la Pestaña de Facturacion Electronica')
        if not self.type_document_id.pse_code:
            raise UserError('El tipo de Documento no tiene Codigo de Facturador')
        if self.type_document_id.pse_code in ['3', '4']:
            if len(self.doc_invoice_relac) != 1:
                raise UserError(
                    'El numero de lineas de Documentos Relacionados debe tener un item para Notas de Credito o Debito')
            if not self.doc_invoice_relac[0].type_document_id.pse_code:
                raise UserError('El Tipo de Documento del Comprobante Relacionado no tiene codigo definido')
            if len(self.doc_invoice_relac[0].nro_comprobante.split('-')) != 2:
                raise UserError('El Nro del Comprobante Relacionado no tiene el formato adecuado Ejem: "F001-000002"')
        if not self.ref:
            raise UserError('La referencia es un campo obligatorio')
        else:
            if len(self.ref.split('-')) != 2:
                raise UserError('La referencia no tiene el formato adecuado "Ejem: F001-000002"')
        if not self.op_type_sunat_id.pse_code:
            raise UserError('El Tipo de Operacion SUNAT no tiene Codigo de Facturador')
        if not self.partner_id.l10n_latam_identification_type_id.code_sunat:
            raise UserError('El partner no tiene su Tipo de Documento o su Tipo de Documento no tiene codigo sunat')
        if not self.partner_id.vat:
            raise UserError('El partner no tiene Numero de Documento')
        if not self.partner_id.name:
            raise UserError('El partner no tiene Nombre')
        if self.ref.split('-')[0][0] != 'B':
            if not self.partner_id.street:
                raise UserError('La direccion del partner es un campo obligatorio para este Tipo de Documento')
        if not self.invoice_date:
            raise UserError('La Fecha de Emision es un campo obligatorio')
        if not self.currency_id.pse_code:
            raise UserError('La moneda seleccionada no tiene su Codigo de Facturador')
        if not parameters.igv_tax_id.amount:
            raise UserError(
                'No se ha configurado porcentaje en el impuesto seleccionado en Parametros Generales de Contabilidad')
        if self.currency_id.name != 'PEN' and not self.currency_rate:
            raise UserError('El Tipo de Cambio es obligatorio cuando se utiliza una moneda que no es Soles')
        if self.type == 'out_refund' and self.type_document_id.code == '07' and not self.credit_note_type_id.code:
            raise UserError('No se ha seleccionado Tipo de Nota de Credito o esta no tiene codigo')
        if self.type == 'out_invoice' and self.type_document_id.code == '08' and not self.debit_note_type_id.code:
            raise UserError('No se ha seleccionado Tipo de Nota de Debito o esta no tiene codigo')
        if not self.serie_id.manual:
            if not next(filter(lambda s: s.serie_id == self.serie_id and s.billing_type == parameters.billing_type,
                               parameters.serial_nubefact_lines), None):
                raise UserError('No se ha configurado una linea de Facturacion para la Serie de este Comprobante')

        advance_counter = 0
        for line in self.invoice_line_ids:
            advance_product = next(
                filter(lambda a_line: a_line.product_id == line.product_id, parameters.advance_product_ids), None)
            if advance_product:
                advance_counter += 1
            # if not advance_product and line.product_id.type in ['service',
            #                                                    'product'] and not line.product_id.onu_code.code:
            #    raise UserError('La linea con descripcion %s no tiene Codigo ONU asociado en su producto' % line.name)
            if not advance_product and line.product_id.type in ['service',
                                                                'product'] and parameters.required_onu and not line.product_id.onu_code.code:
                raise UserError('La linea con descripcion %s no tiene Codigo ONU asociado en su producto' % line.name)
            for tax in line.tax_ids:
                if tax.name != 'ICBPER' and not tax.eb_afect_igv_id.pse_code:
                    raise UserError(
                        'La linea con descripcion %s tiene algun impuesto distinto a ICBPER sin tipo de afectacion o sin codigo de facturador en dicho tipo de afectacion' % line.name)
                if not tax.eb_tributes_type_id:
                    raise UserError('La linea con descripcion %s tiene algun impuesto sin tipo de tributo' % line.name)
                if self.op_type_sunat_id.pse_code == '2':
                    if tax.eb_afect_igv_id.pse_code != '16':
                        raise UserError(
                            'Si el tipo de Operacion es Exportacion se debe utilizar el impuesto Exportacion en todas las lineas del Comprobante')
        if advance_counter > 0 and self.op_type_sunat_id.pse_code in parameters.catalog_51_advance_ids.mapped(
                'pse_code'):
            if advance_counter != len(self.advance_ids):
                raise UserError(
                    'El numero de Anticipos relacionados a este Comprobante es distinto a las lineas de anticipo existentes')

        # Detraction Conditionals
        if self.op_type_sunat_id.code in parameters.catalog_51_detraction_ids.mapped('code'):
            if not self.detraction_type_id or not self.detraction_payment_id:
                raise UserError('Los campos Tipo de Detraccion y Medio de Pago Detraccion son Obligatorios')
            if not self.detraction_type_id.pse_code:
                raise UserError('El Tipo de Detraccion no tiene un codigo de Facturador')
            if not self.detraction_payment_id.pse_code:
                raise UserError('El Medio de Pago Detraccion no tiene un codigo de Facturador')
            if self.detraction_amount <= 0:
                raise UserError('El Monto de Detraccion debe ser mayor a cero')
