# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp import models,fields ,api


datos = []
llaves = {}

class valor_unitario_kardex(models.TransientModel):
	_name='valor.unitario.kardex'
	
	fecha_inicio = fields.Date('Fecha Inicio')
	fecha_final = fields.Date('Fecha Final')


	@api.model
	def _action_actualizar_automatica(self):
		nuevo = self.env['valor.unitario.kardex'].create({'fecha_inicio': str(fields.Date.today())[0:4]+ '-01-01', 'fecha_final': str(fields.Date.today())[0:4]+'-12-31' })
		nuevo.do_valor()


	def do_valor(self):
		self.env['sql.kardex']._execute_all()
		mrp_flag = self.env['sql.kardex']._have_mrp()
		prods = self.env['product.product'].with_context({'active_test':False}).search([])
		locat = self.env['stock.location'].with_context({'active_test':False}).search([('usage','in',['internal','inventory','transit','procurement','production'])])

		lst_products  = prods.ids
		lst_locations = locat.ids
		productos='{'
		almacenes='{'
		date_ini= self.fecha_inicio.strftime('%Y-%m-%d').split('-')[0] + '-01-01'
		date_fin= self.fecha_final
		fecha_arr = self.fecha_inicio
		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'

		cprom_data = {}
		self.env.cr.execute("""
			select

				product_id,
				location_id,
				debit,
				credit,
				fecha,
				type_doc,
				serial,
				nro,
				numdoc_cuadre,
				nro_documento,
				name,
				operation_type,
				default_code,
				unidad,
				ingreso,
				salida,
				cadquiere,
				origen,
				destino,
				almacen,
				stock_moveid
			from (
select vst_kardex_sunat.*
from vst_kardex_fisico_valorado as vst_kardex_sunat
					
	   where (fecha_num((vst_kardex_sunat.fecha- interval '5')::date) between """+str(date_ini).replace('-','')+""" and """+str(self.fecha_final).replace('-','')+""")    
			 and vst_kardex_sunat.company_id = """ +str(self.env.company.id)+ """
			order by vst_kardex_sunat.fecha, vst_kardex_sunat.stock_moveid , vst_kardex_sunat.salida desc,vst_kardex_sunat.nro
			)Todo
		""")
		total_all = self.env.cr.fetchall()
		self.send_message("Valorización de Transferencias Internas, Ventas y Devoluciones de Venta.<br/><center>Total lineas a valorizar: "+str(len(total_all)) + "</center>")
		cont_report = 0
		import datetime
		tiempo_inicial = datetime.datetime.now()
		tiempo_pasado = [0,0]
		for xl in total_all:

			l = {
				'product_id':xl[0],
				'location_id':xl[1],
				'debit':xl[2],
				'credit':xl[3],
				'fecha':xl[4],
				'type_doc':xl[5],
				'serial':xl[6],
				'nro':xl[7],
				'numdoc_cuadre':xl[8],
				'nro_documento':xl[9],
				'name':xl[10],
				'operation_type':xl[11],
				'default_code':xl[12],
				'unidad':xl[13],
				'ingreso':xl[14],
				'salida':xl[15],
				'cadquiere':xl[16],
				'origen':xl[17],
				'destino':xl[18],
				'almacen':xl[19],
				'stock_moveid':xl[20],
			}
			cont_report += 1
			if cont_report%300 == 0:
				tiempo_pasado = divmod((datetime.datetime.now()-tiempo_inicial).seconds,60)
				text_report = "<b>Valorización de Transferencias Internas, Ventas y Devoluciones de Venta.</b><br/><center>Total lineas a procesar: "+str(len(total_all)) + "</center><br/><center>Procesado:"+str(cont_report)+"/"+str(len(total_all))+"</center><br/> Tiempo Procesado: "+ str(tiempo_pasado[0])+" minutos " +str(tiempo_pasado[1]) + " segundos" 
				text_report += """<div id="myProgress" style="position: relative; width: 100%;  height: 30px;   background-color: white;">
				  <div id="myBar" style="position: absolute;  width: """+"%.2f"%(cont_report*100/len(total_all))+"""%;  height: 100%; background-color: #875A7B;">
				    <div id="label" style="text-align: center; line-height: 30px; color: white;">""" +"%.2f"%(cont_report*100/len(total_all))+ """%</div>
				  </div>
				</div>"""
				self.send_message(text_report)
				
			llave = (l['product_id'],l['location_id'])
			cprom_acum = [0,0]
			if llave in cprom_data:
				cprom_acum = cprom_data[llave]
			else:
				cprom_data[llave] = cprom_acum

			cprom_act_antes = cprom_data[llave][1] / cprom_data[llave][0] if cprom_data[llave][0] != 0 else 0

			data_temp = {}


			if l['stock_moveid']:
				if mrp_flag:
					self.env.cr.execute(""" 

						select sm.production_id,sm.id,sl_o.usage as origen , sl_d.usage as destino, sp.name,sm.origin, coalesce(sm.price_unit_it,0) as price_unit_it, sp2.name as name2, sp3.name as name3 from
						stock_move sm
						left join stock_picking sp on sp.id = sm.picking_id
						left join stock_picking sp2 on sp2.id = sp.backorder_id
						left join stock_picking sp3 on sp3.id = sp2.backorder_id 
						inner join stock_location sl_o on sl_o.id = sm.location_id
						inner join stock_location sl_d on sl_d.id = sm.location_dest_id
						where sm.id = """ +str(l['stock_moveid'])+ """					
					 """)
					data_temp = self.env.cr.dictfetchall()[0]
					if data_temp['production_id']:
						oml = self.env['mrp.production'].browse(data_temp['production_id'])
						oml.calcular_costos()

						self.env.cr.execute(""" 

							select sm.production_id,sm.id,sl_o.usage as origen , sl_d.usage as destino, sp.name,sm.origin, coalesce(sm.price_unit_it,0) as price_unit_it, sp2.name as name2, sp3.name as name3 from
							stock_move sm
							left join stock_picking sp on sp.id = sm.picking_id
							left join stock_picking sp2 on sp2.id = sp.backorder_id
							left join stock_picking sp3 on sp3.id = sp2.backorder_id 
							inner join stock_location sl_o on sl_o.id = sm.location_id
							inner join stock_location sl_d on sl_d.id = sm.location_dest_id
							where sm.id = """ +str(l['stock_moveid'])+ """					
						 """)
						data_temp = self.env.cr.dictfetchall()[0]
				else:
					self.env.cr.execute(""" 

						select sm.id,sl_o.usage as origen , sl_d.usage as destino, sp.name,sm.origin, coalesce(sm.price_unit_it,0) as price_unit_it, sp2.name as name2, sp3.name as name3 from
						stock_move sm
						left join stock_picking sp on sp.id = sm.picking_id
						left join stock_picking sp2 on sp2.id = sp.backorder_id
						left join stock_picking sp3 on sp3.id = sp2.backorder_id 
						inner join stock_location sl_o on sl_o.id = sm.location_id
						inner join stock_location sl_d on sl_d.id = sm.location_dest_id
						where sm.id = """ +str(l['stock_moveid'])+ """					
					 """)
					data_temp = self.env.cr.dictfetchall()[0]

			#data_temp = {'origen':l['origen_usage'] or '','destino':l['destino_usage'] or ''}
			if l['ingreso'] or l['debit']:
				if (data_temp['origen'] == 'internal' and data_temp['destino'] == 'internal') or (data_temp['origen'] == 'transit' and data_temp['destino'] == 'internal') or (data_temp['origen'] == 'production' and data_temp['destino'] == 'internal'):
					cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
					cprom_acum[1] = cprom_acum[1] + (l['ingreso'] if l['ingreso'] else 0)*data_temp['price_unit_it']
				else:	
					cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
					cprom_acum[1] = cprom_acum[1] + (l['debit'] if l['debit'] else 0) -  (l['credit'] if l['credit'] else 0)
			else:
				if (data_temp['origen'] == 'internal' and data_temp['destino'] == 'supplier'):
					cprom_acum[0] = cprom_acum[0] -  (l['salida'] if l['salida'] else 0)
					cprom_acum[1] = cprom_acum[1] - (l['salida'] if l['salida'] else 0)*data_temp['price_unit_it']
				else:
					if l['salida']:
						cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
						cprom_acum[1] = cprom_acum[1] - (l['salida'] if l['salida'] else 0)*(cprom_act_antes if cprom_act_antes else 0)
					else:
						cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
						cprom_acum[1] = cprom_acum[1] - (l['credit'] if l['credit'] else 0)

			cprom_act = cprom_acum[1] / cprom_acum[0] if cprom_acum[0] != 0 else 0

			cprom_data[llave] = cprom_acum

			if l['stock_moveid'] and str(l['fecha'])[0:10]>= str(self.fecha_inicio)[0:10]:
				if data_temp['origen'] == 'internal' and data_temp['destino'] == 'internal' and l['salida']:
					self.env.cr.execute(""" UPDATE stock_move set price_unit_it = """ +str( cprom_act_antes )+ """  where id = """ +str( l['stock_moveid'] )+ """; """)


				if (data_temp['origen'] == 'internal' and data_temp['destino'] == 'transit') or (data_temp['origen'] == 'internal' and data_temp['destino'] == 'production') or (data_temp['origen'] == 'internal' and data_temp['destino'] == 'customer'):
					self.env.cr.execute(""" UPDATE stock_move set price_unit_it = """ +str( cprom_act_antes )+ """  where id = """ +str( l['stock_moveid'] )+ """; """)
					self.env.cr.execute(""" UPDATE stock_move set price_unit_it = """ +str( cprom_act_antes )+ """  where (origin like '%""" +str( data_temp['name'] )+ """%' or origin = 'Retorno de """ +str( data_temp['name'] )+ """' ) and product_id = """ +str(l['product_id'])+ """; """)
					self.env.cr.execute(""" UPDATE stock_move set price_unit_it = """ +str( cprom_act_antes )+ """  where picking_id in (select id from stock_picking where origin like '%""" +str( data_temp['name'] )+ """%' or origin = 'Retorno de """ +str( data_temp['name'] )+ """' ) and product_id = """ +str(l['product_id'])+ """; """)
					if data_temp['name2']:						
						self.env.cr.execute(""" UPDATE stock_move set price_unit_it = """ +str( cprom_act_antes )+ """  where (origin like '%""" +str( data_temp['name2'] )+ """%' or origin = 'Retorno de """ +str( data_temp['name2'] )+ """' ) and product_id = """ +str(l['product_id'])+ """; """)
						self.env.cr.execute(""" UPDATE stock_move set price_unit_it = """ +str( cprom_act_antes )+ """  where picking_id in (select id from stock_picking where origin like '%""" +str( data_temp['name2'] )+ """%' or origin = 'Retorno de """ +str( data_temp['name2'] )+ """' ) and product_id = """ +str(l['product_id'])+ """; """)
					if data_temp['name3']:						
						self.env.cr.execute(""" UPDATE stock_move set price_unit_it = """ +str( cprom_act_antes )+ """  where (origin like '%""" +str( data_temp['name3'] )+ """%' or origin = 'Retorno de """ +str( data_temp['name3'] )+ """' ) and product_id = """ +str(l['product_id'])+ """; """)
						self.env.cr.execute(""" UPDATE stock_move set price_unit_it = """ +str( cprom_act_antes )+ """  where picking_id in (select id from stock_picking where origin like '%""" +str( data_temp['name3'] )+ """%' or origin = 'Retorno de """ +str( data_temp['name3'] )+ """' ) and product_id = """ +str(l['product_id'])+ """; """)
					self.env.cr.execute(""" UPDATE stock_move set price_unit_it = """ +str( cprom_act_antes )+ """  where (origin_returned_move_id = """ +str( l['stock_moveid'] )+ """ ) and product_id = """ +str(l['product_id'])+ """; """)
		return {
			'notif_button':{'auto_close':False,'with_menssage':1,'title':'Actualización de Transferencias','message':'Se proceso de '+str(self.fecha_inicio)+' al ' + str(self.fecha_final)+ '.<br/>Lineas procesadas: '+ str(len(total_all)) +'<br/>Tiempo: ' + str(tiempo_pasado[0])+" minutos " +str(tiempo_pasado[1]) + " segundos",'eventID':self.id,'model_notify':'valor.unitario.kardex','method_notify':'get_kardex_valorado','name_button':'Kardex Valorado'}
		}
	



	def do_valor_dolar(self):
		prods = self.env['product.product'].with_context({'active_test':False}).search([])
		locat = self.env['stock.location'].with_context({'active_test':False}).search([('usage','in',['internal','inventory','transit','procurement','production'])])

		lst_products  = prods.ids
		lst_locations = locat.ids
		productos='{'
		almacenes='{'
		date_ini= self.fecha_inicio.strftime('%Y-%m-%d').split('-')[0] + '-01-01'
		date_fin= self.fecha_final
		fecha_arr = self.fecha_inicio
		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'

		cprom_data = {}
		self.env.cr.execute("""
			select

				product_id,
				location_id,
				debit,
				credit,
				fecha,
				type_doc,
				serial,
				nro,
				numdoc_cuadre,
				nro_documento,
				name,
				operation_type,
				default_code,
				unidad,
				ingreso,
				salida,
				cadquiere,
				origen,
				destino,
				almacen,
				stock_moveid
			from (
select vst_kardex_sunat.*
from vst_kardex_fisico_valorado_dolar as vst_kardex_sunat
					
	   where (fecha_num((vst_kardex_sunat.fecha- interval '5')::date) between """+str(date_ini).replace('-','')+""" and """+str(self.fecha_final).replace('-','')+""")    
			 and vst_kardex_sunat.company_id = """ +str(self.env.company.id)+ """
			order by vst_kardex_sunat.fecha, vst_kardex_sunat.stock_moveid , vst_kardex_sunat.salida desc,vst_kardex_sunat.nro
			)Todo
		""")
		total_all = self.env.cr.dictfetchall()
		self.send_message("Valorización de Transferencias Internas, Ventas y Devoluciones de Venta (USD).<br/><center>Total lineas a valorizar: "+str(len(total_all)) + "</center>")
		cont_report = 0
		import datetime
		tiempo_inicial = datetime.datetime.now()
		tiempo_pasado = [0,0]
		for xl in total_all:

			l = {
				'product_id':xl[0],
				'location_id':xl[1],
				'debit':xl[2],
				'credit':xl[3],
				'fecha':xl[4],
				'type_doc':xl[5],
				'serial':xl[6],
				'nro':xl[7],
				'numdoc_cuadre':xl[8],
				'nro_documento':xl[9],
				'name':xl[10],
				'operation_type':xl[11],
				'default_code':xl[12],
				'unidad':xl[13],
				'ingreso':xl[14],
				'salida':xl[15],
				'cadquiere':xl[16],
				'origen':xl[17],
				'destino':xl[18],
				'almacen':xl[19],
				'stock_moveid':xl[20],
			}
			cont_report += 1
			if cont_report%300 == 0:
				tiempo_pasado = divmod((datetime.datetime.now()-tiempo_inicial).seconds,60)
				text_report = "<b>Valorización de Transferencias Internas, Ventas y Devoluciones de Venta (USD).</b><br/><center>Total lineas a procesar: "+str(len(total_all)) + "</center><br/><center>Procesado:"+str(cont_report)+"/"+str(len(total_all))+"</center><br/> Tiempo Procesado: "+ str(tiempo_pasado[0])+" minutos " +str(tiempo_pasado[1]) + " segundos" 
				text_report += """<div id="myProgress" style="position: relative; width: 100%;  height: 30px;   background-color: white;">
				  <div id="myBar" style="position: absolute;  width: """+"%.2f"%(cont_report*100/len(total_all))+"""%;  height: 100%; background-color: #875A7B;">
				    <div id="label" style="text-align: center; line-height: 30px; color: white;">""" +"%.2f"%(cont_report*100/len(total_all))+ """%</div>
				  </div>
				</div>"""
				self.send_message(text_report)
				
			llave = (l['product_id'],l['location_id'])
			cprom_acum = [0,0]
			if llave in cprom_data:
				cprom_acum = cprom_data[llave]
			else:
				cprom_data[llave] = cprom_acum

			cprom_act_antes = cprom_data[llave][1] / cprom_data[llave][0] if cprom_data[llave][0] != 0 else 0

			data_temp = {}

			if l['stock_moveid']:
				self.env.cr.execute(""" 

					select sm.id,sl_o.usage as origen , sl_d.usage as destino, sp.name,sm.origin, coalesce(sm.price_unit_it_dolar,0) as price_unit_it, sp2.name as name2, sp3.name as name3 from
					stock_move sm
					left join stock_picking sp on sp.id = sm.picking_id
					left join stock_picking sp2 on sp2.id = sp.backorder_id
					left join stock_picking sp3 on sp3.id = sp2.backorder_id 
					inner join stock_location sl_o on sl_o.id = sm.location_id
					inner join stock_location sl_d on sl_d.id = sm.location_dest_id
					where sm.id = """ +str(l['stock_moveid'])+ """					
				 """)
				data_temp = self.env.cr.dictfetchall()[0]

			#data_temp = {'origen':l['origen_usage'] or '','destino':l['destino_usage'] or ''}
			if l['ingreso'] or l['debit']:
				if (data_temp['origen'] == 'internal' and data_temp['destino'] == 'internal') or (data_temp['origen'] == 'transit' and data_temp['destino'] == 'internal'):
					cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
					cprom_acum[1] = cprom_acum[1] + (l['ingreso'] if l['ingreso'] else 0)*data_temp['price_unit_it']
				else:	
					cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
					cprom_acum[1] = cprom_acum[1] + (l['debit'] if l['debit'] else 0) -  (l['credit'] if l['credit'] else 0)
			else:
				if (data_temp['origen'] == 'internal' and data_temp['destino'] == 'supplier'):
					cprom_acum[0] = cprom_acum[0] -  (l['salida'] if l['salida'] else 0)
					cprom_acum[1] = cprom_acum[1] - (l['salida'] if l['salida'] else 0)*data_temp['price_unit_it']
				else:
					if l['salida']:
						cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
						cprom_acum[1] = cprom_acum[1] - (l['salida'] if l['salida'] else 0)*(cprom_act_antes if cprom_act_antes else 0)
					else:
						cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
						cprom_acum[1] = cprom_acum[1] - (l['credit'] if l['credit'] else 0)

			cprom_act = cprom_acum[1] / cprom_acum[0] if cprom_acum[0] != 0 else 0

			cprom_data[llave] = cprom_acum

			if l['stock_moveid'] and str(l['fecha'])[0:10]>= str(self.fecha_inicio)[0:10]:
				if data_temp['origen'] == 'internal' and data_temp['destino'] == 'internal' and l['salida']:
					self.env.cr.execute(""" UPDATE stock_move set price_unit_it_dolar = """ +str( cprom_act_antes )+ """  where id = """ +str( l['stock_moveid'] )+ """; """)


				if (data_temp['origen'] == 'internal' and data_temp['destino'] == 'transit') or (data_temp['origen'] == 'internal' and data_temp['destino'] == 'production') or (data_temp['origen'] == 'internal' and data_temp['destino'] == 'customer'):
					self.env.cr.execute(""" UPDATE stock_move set price_unit_it_dolar = """ +str( cprom_act_antes )+ """  where id = """ +str( l['stock_moveid'] )+ """; """)
					self.env.cr.execute(""" UPDATE stock_move set price_unit_it_dolar = """ +str( cprom_act_antes )+ """  where (origin like '%""" +str( data_temp['name'] )+ """%' or origin = 'Retorno de """ +str( data_temp['name'] )+ """' ) and product_id = """ +str(l['product_id'])+ """; """)
					self.env.cr.execute(""" UPDATE stock_move set price_unit_it_dolar = """ +str( cprom_act_antes )+ """  where picking_id in (select id from stock_picking where origin like '%""" +str( data_temp['name'] )+ """%' or origin = 'Retorno de """ +str( data_temp['name'] )+ """' ) and product_id = """ +str(l['product_id'])+ """; """)
					if data_temp['name2']:						
						self.env.cr.execute(""" UPDATE stock_move set price_unit_it_dolar = """ +str( cprom_act_antes )+ """  where (origin like '%""" +str( data_temp['name2'] )+ """%' or origin = 'Retorno de """ +str( data_temp['name2'] )+ """' ) and product_id = """ +str(l['product_id'])+ """; """)
						self.env.cr.execute(""" UPDATE stock_move set price_unit_it_dolar = """ +str( cprom_act_antes )+ """  where picking_id in (select id from stock_picking where origin like '%""" +str( data_temp['name2'] )+ """%' or origin = 'Retorno de """ +str( data_temp['name2'] )+ """' ) and product_id = """ +str(l['product_id'])+ """; """)
					if data_temp['name3']:						
						self.env.cr.execute(""" UPDATE stock_move set price_unit_it_dolar = """ +str( cprom_act_antes )+ """  where (origin like '%""" +str( data_temp['name3'] )+ """%' or origin = 'Retorno de """ +str( data_temp['name3'] )+ """' ) and product_id = """ +str(l['product_id'])+ """; """)
						self.env.cr.execute(""" UPDATE stock_move set price_unit_it_dolar = """ +str( cprom_act_antes )+ """  where picking_id in (select id from stock_picking where origin like '%""" +str( data_temp['name3'] )+ """%' or origin = 'Retorno de """ +str( data_temp['name3'] )+ """' ) and product_id = """ +str(l['product_id'])+ """; """)
					self.env.cr.execute(""" UPDATE stock_move set price_unit_it_dolar = """ +str( cprom_act_antes )+ """  where (origin_returned_move_id = """ +str( l['stock_moveid'] )+ """ ) and product_id = """ +str(l['product_id'])+ """; """)
		return {
			'notif_button':{'auto_close':False,'with_menssage':1,'title':'Actualización de Transferencias(USD)','message':'Se proceso de '+str(self.fecha_inicio)+' al ' + str(self.fecha_final)+ '.<br/>Lineas procesadas: '+ str(len(total_all)) +'<br/>Tiempo: ' + str(tiempo_pasado[0])+" minutos " +str(tiempo_pasado[1]) + " segundos",'eventID':self.id,'model_notify':'valor.unitario.kardex','method_notify':'get_kardex_valorado','name_button':'Kardex Valorado'}
		}
	

	def get_kardex_valorado(self):
		return {			
			'name': 'Kardex Valorado',
			'type': 'ir.actions.act_window',
			'res_model': 'make.kardex.valorado',
			'view_mode': 'form',
			'target': 'new',			
			'views': [(False, 'form')],
		}

		"""	select * from stock_location where id = dr.id_origen into loc_1;
			select * from stock_location where id = dr.id_destino into loc_2;
 
			select put.factor as f1 , pu.factor as f2 from stock_move sm 
			inner join product_product pp on pp.id = sm.product_id
			inner join product_template pt2 on pt2.id = pp.product_tmpl_id
			inner join uom_uom pu on pu.id = pt2.uom_id
			inner join uom_uom put on put.id = sm.product_uom           
			where sm.id = dr.stock_moveid  into pp_1;

		   select sp.name,sm.product_id from
		   stock_picking sp
		   inner join stock_move sm on sm.picking_id = sp.id
		   where sm.id = dr.stock_moveid into datos_con;

		  ---- esto es para las variables que estan en el crusor y pasarlas a las variables output
		  select * from stock_move where id = dr.stock_moveid into rf;
		  if loc_1.usage = 'internal' and loc_2.usage='internal' and fecha_num(dr.fecha) >= $5 and dr.stock_moveid = $6 and dr.id_origen = dr.location_id then
			UPDATE stock_move set price_unit_it = (cprom/ pp_1.f2) * pp_1.f1  where id = dr.stock_moveid;
		  end if;
		  if loc_1.usage = 'internal' and loc_2.usage='transit' and fecha_num(dr.fecha) >= $5 and dr.stock_moveid = $6 and dr.id_origen = dr.location_id then
			UPDATE stock_move set price_unit_it = (cprom/ pp_1.f2) * pp_1.f1  where (stock_move.origin = datos_con.name or stock_move.origin = 'Retorno de '|| stock_move.origin ) and stock_move.product_id = datos_con.product_id;
		  end if;

			"""	