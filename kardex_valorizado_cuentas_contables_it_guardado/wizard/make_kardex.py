# -*- coding: utf-8 -*-
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
import odoo.addons.decimal_precision as dp
from openerp.osv import osv
import base64
from odoo import models, fields, api
import codecs

values = {}





class make_kardex_valorado(models.TransientModel):
	_inherit = "make.kardex.valorado"


	def do_csvtoexcel(self):
		cad = ""

		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','inventory','transit','procurement','production'))] )
			lst_locations = locat_ids.ids
		else:
			lst_locations = self.location_ids.ids
		lst_products  = self.products_ids.ids
		productos='{'
		almacenes='{'
		date_ini=self.fini
		date_fin=self.ffin
		if self.allproducts:
			lst_products = self.env['product.product'].with_context(active_test=False).search([]).ids

		else:
			lst_products = self.products_ids.ids

		if len(lst_products) == 0:
			raise osv.except_osv('Alerta','No existen productos seleccionados')

		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)
		almacenes=almacenes[:-1]+'}'



		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook(direccion +'kardex_producto.xlsx')
		worksheet = workbook.add_worksheet("Kardex")
		bold = workbook.add_format({'bold': True})
		bold.set_font_size(8)
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(8)
		boldbord.set_bg_color('#DCE6F1')

		especial1 = workbook.add_format({'bold': True})
		especial1.set_align('center')
		especial1.set_align('vcenter')
		especial1.set_text_wrap()
		especial1.set_font_size(15)

		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		numberseis = workbook.add_format({'num_format':'0.000000'})
		numberseis.set_font_size(8)
		numberocho = workbook.add_format({'num_format':'0.00000000'})
		numberocho.set_font_size(8)
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_font_size(8)
		numberdos.set_border(style=1)
		numberdos.set_font_size(8)
		numbertres.set_border(style=1)
		numberseis.set_border(style=1)
		numberocho.set_border(style=1)
		numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})
		numberdosbold.set_font_size(8)

		formatdate = workbook.add_format({'num_format': 'dd-mm-yyyy'})
		formatdate.set_border(style=1)
		formattime = workbook.add_format({'num_format': 'HH:mm'})
		formattime.set_border(style=1)
		x= 10
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.2


		worksheet.merge_range(1,5,1,10, "KARDEX VALORADO", especial1)
		worksheet.write(2,1,'FECHA INICIO:',bold)
		worksheet.write(3,1,'FECHA FIN:',bold)

		worksheet.write(2,2,str(self.fini))
		worksheet.write(3,2,str(self.ffin))			
		import datetime		

		#worksheet.merge_range(8,0,9,0, u"Fecha Alm.",boldbord)
		worksheet.merge_range(8,1,9,1, u"Fecha",boldbord)
		worksheet.merge_range(8,2,9,2, u"Hora",boldbord)
		worksheet.merge_range(8,3,9,3, u"Tipo",boldbord)
		worksheet.merge_range(8,4,9,4, u"Serie",boldbord)
		worksheet.merge_range(8,5,9,5, u"Número",boldbord)
		worksheet.merge_range(8,6,9,6, u"Doc. Almacen",boldbord)
		worksheet.merge_range(8,7,9,7, u"RUC",boldbord)
		worksheet.merge_range(8,8,9,8, u"Empresa",boldbord)
		worksheet.merge_range(8,9,9,9, u"T. OP.",boldbord)
		worksheet.merge_range(8,10,9,10, u"Producto",boldbord)
		worksheet.merge_range(8,11,9,11, u"Codigo Producto",boldbord)				
		worksheet.merge_range(8,12,9,12, u"Unidad",boldbord)
		worksheet.merge_range(8,13,8,14, u"Ingreso",boldbord)
		worksheet.write(9,13, "Cantidad",boldbord)
		worksheet.write(9,14, "Costo",boldbord)
		worksheet.merge_range(8,15,8,16, u"Salida",boldbord)
		worksheet.write(9,15, "Cantidad",boldbord)
		worksheet.write(9,16, "Costo",boldbord)
		worksheet.merge_range(8,17,8,18, u"Saldo",boldbord)
		worksheet.write(9,17, "Cantidad",boldbord)
		worksheet.write(9,18, "Costo",boldbord)

		worksheet.merge_range(8,19,9,19, u"Costo Adquisición",boldbord)
		worksheet.merge_range(8,20,9,20, "Costo Promedio",boldbord)

		worksheet.merge_range(8,21,9,21, "Ubicacion Origen",boldbord)
		worksheet.merge_range(8,22,9,22, "Ubicacion Destino",boldbord)
		worksheet.merge_range(8,23,9,23, "Almacen",boldbord)

		if self.check_account:
			worksheet.merge_range(8,24,9,24, u"Cuenta Valuación",boldbord)
			worksheet.merge_range(8,25,9,25, u"Cuenta Salida",boldbord)
			worksheet.merge_range(8,26,9,26, u"Cuenta Analítica",boldbord)
			# worksheet.merge_range(8,26,9,26, u"Etiqueta Analítica",boldbord)

		elementos = self.env['kardex.save'].search([('company_id','=',self.env.company.id),('state','=','done'),('name.date_end','<',self.fini)]).sorted(lambda line: line.name.code)

		var_log = ""
		if len(elementos)>0:
			var_log = """
	select * from (
	select 
	"Almacén" as almacen, "Categoria" as categoria,"Producto" as producto, '"""+str(elementos[-1].name.date_end)+"""'::timestamp as fecha ,'' as  periodo , '' as ctanalitica,
	'' as serial, 'Saldo Inicial' as nro, '' as operation_type, 'Saldo Inicial' as name, CASE WHEN "Entrada" - "Salida" >0 then "Entrada" - "Salida" else 0 END as ingreso,
	CASE WHEN "Entrada" - "Salida" <0 then "Salida" - "Entrada" else 0 END as salida, 0 as saldof,
	CASE WHEN "Entrada" - "Salida" >0 then ("Entrada" - "Salida")*kardex_save_"""+str(elementos[-1].name.code)+"""_"""+str(self.env.company.id)+""".cprom else 0 END as debit,
	CASE WHEN "Entrada" - "Salida" <0 then ("Salida" - "Entrada")*kardex_save_"""+str(elementos[-1].name.code)+"""_"""+str(self.env.company.id)+""".cprom else 0 END as credit,
	kardex_save_"""+str(elementos[-1].name.code)+"""_"""+str(self.env.company.id)+""".cprom as cadquiere, 0 as saldov, kardex_save_"""+str(elementos[-1].name.code)+"""_"""+str(self.env.company.id)+""".cprom, '' as type, 'Ingreso' as esingreso, p_id as product_id, alm_id as location_id, '' as doc_type_ope,
	0 as stock_moveid, '' as product_account, "Codigo P." as default_code, kardex_save_"""+str(elementos[-1].name.code)+"""_"""+str(self.env.company.id)+""".unidad, '' as stock_doc, '' as origen, "Almacén" as destino,
	'' as type_doc, '' as numdoc_cuadre,'' as nro_documento, null::integer as invoicelineid, null::integer as id_origen, alm_id as id_destino
	from  kardex_save_"""+str(elementos[-1].name.code)+"""_"""+str(self.env.company.id)+"""
	) BX
	 union all 
			 """

		self._cr.execute("""


CREATE OR REPLACE FUNCTION get_kardex_v_save(IN date_ini integer, IN date_end integer, IN productos integer[], IN almacenes integer[], IN company integer,OUT almacen character varying, OUT categoria character varying, OUT name_template character varying, OUT fecha timestamp without time zone, OUT periodo character varying, OUT ctanalitica character varying, OUT serial character varying, OUT nro character varying, OUT operation_type character varying, OUT name character varying, OUT ingreso numeric, OUT salida numeric, OUT saldof numeric, OUT debit numeric, OUT credit numeric, OUT cadquiere numeric, OUT saldov numeric, OUT cprom numeric, OUT type character varying, OUT esingreso text, OUT product_id integer, OUT location_id integer, OUT doc_type_ope character varying, OUT ubicacion_origen integer, OUT ubicacion_destino integer, OUT stock_moveid integer, OUT account_invoice character varying, OUT product_account character varying, OUT default_code character varying, OUT unidad character varying, OUT mrpname character varying, OUT ruc character varying, OUT comapnyname character varying, OUT cod_sunat character varying, OUT tipoprod character varying, OUT coduni character varying, OUT metodo character varying, OUT cu_entrada numeric, OUT cu_salida numeric, OUT period_name character varying, OUT stock_doc character varying, OUT origen character varying, OUT destino character varying, OUT type_doc character varying, OUT numdoc_cuadre character varying, OUT doc_partner character varying, OUT fecha_albaran timestamp without time zone, OUT pedido_compra character varying, OUT licitacion character varying, OUT doc_almac character varying, OUT lote character varying, OUT correlativovisual integer)
	RETURNS SETOF record AS
$BODY$  
DECLARE 
	location integer;
	product integer;
	precprom numeric;
	h record;
	h1 record;
	hproduct record;
	h2 record;
	dr record;
	pt record;
	il record;
	loc_id integer;
	prod_id integer;
	contador integer;
	lote_idmp varchar;
	avanceop integer;
	
BEGIN

	select res_partner.name,res_partner.vat as nro_documento from res_company 
	inner join res_partner on res_company.partner_id = res_partner.id
	into h;

	-- foreach product in array $3 loop
		
						loc_id = -1;
						prod_id = -1;
						lote_idmp = -1;
--    foreach location in array $4  loop
--      for dr in cursor_final loop
			saldof =0;
			saldov =0;
			cprom =0;
			cadquiere =0;
			ingreso =0;
			salida =0;
			debit =0;
			credit =0;
			avanceop = 0;
			contador = 2;
			
			
			for dr in 
			select *,sp.name as doc_almac,sm.kardex_date as fecha_albaran, '' as pedido_compra, '' as licitacion,'' as lote,'1' as correlativovisual,
			''::character varying as ruc,''::character varying as comapnyname, ''::character varying as cod_sunat,''::character varying as default_code,ipx.value_text as ipxvalue,
			''::character varying as tipoprod ,''::character varying as coduni ,''::character varying as metodo, 0::numeric as cu_entrada , 0::numeric as cu_salida, ''::character varying as period_name  
			from 
(
""" +var_log+ """
 select * from
 (select * from vst_kardex_fisico_valorado as vst_kardex_sunat
     where vst_kardex_sunat.fecha between 

     """ + ( ( "('"+ str(elementos[-1].name.date_end)+ "' )::timestamp + interval '29' hour " )  if len(elementos)>0 else  "('2021-01-01' )::timestamp + interval '5' hour "  ) + """
     
     and 
			 (substring($2::varchar,1,4) || '-' || substring($2::varchar,5,2) || '-' || substring($2::varchar,7,2) )::timestamp + interval '29' hour  
 )AX

)
			as vst_kardex_sunat
left join stock_move sm on sm.id = vst_kardex_sunat.stock_moveid
left join stock_picking sp on sp.id = sm.picking_id
left join account_move_line ail on ail.id = vst_kardex_sunat.invoicelineid
left join product_product pp on pp.id = vst_kardex_sunat.product_id
left join product_template ptp on ptp.id = pp.product_tmpl_id
LEFT JOIN ir_property ipx ON ipx.res_id::text = ('product.template,'::text || ptp.id) AND ipx.name::text = 'cost_method'::text 					
			 where 
			 (sm.company_id = $5 or sm.id is null)
			order by vst_kardex_sunat.location_id,vst_kardex_sunat.product_id,vst_kardex_sunat.fecha,vst_kardex_sunat.esingreso,vst_kardex_sunat.stock_moveid,vst_kardex_sunat.nro
				loop
				if dr.location_id = ANY ($4) and dr.product_id = ANY ($3) then
					if dr.ipxvalue = 'specific' then
										if loc_id = dr.location_id then
							contador = 1;
							else
							
							loc_id = dr.location_id;
							prod_id = dr.product_id;
					--    foreach location in array $4  loop
							
					--      for dr in cursor_final loop
							saldof =0;
							saldov =0;
							cprom =0;
							cadquiere =0;
							ingreso =0;
							salida =0;
							debit =0;
							credit =0;
						end if;
							else
						

								if prod_id = dr.product_id and loc_id = dr.location_id then
								contador =1;
								else

							loc_id = dr.location_id;
							prod_id = dr.product_id;
					--    foreach location in array $4  loop
					--      for dr in cursor_final loop
								saldof =0;
								saldov =0;
								cprom =0;
								cadquiere =0;
								ingreso =0;
								salida =0;
								debit =0;
								credit =0;
								end if;
					 end if;

						select '' as category_sunat_code, '' as uom_sunat_code, product_product.default_code as codigoproducto
						from product_product
						inner join product_template on product_product.product_tmpl_id = product_template.id
						inner join product_category on product_template.categ_id = product_category.id
						inner join uom_uom on product_template.uom_id = uom_uom.id
						--left join category_product_sunat on product_category.cod_sunat = category_product_sunat.id
						--left join category_uom_sunat on uom_uom.cod_sunat = category_uom_sunat.id
						where product_product.id = dr.product_id into h1;


						select t_pp.id, 
            ((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
           FROM product_product t_pp
             JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
			 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
left join product_variant_combination pvc on pvc.product_product_id = t_pp.id
left join product_template_attribute_value ptav on ptav.id = pvc.product_template_attribute_value_id
left join product_attribute_value pav on pav.id = ptav.product_attribute_value_id
where t_pp.id = dr.product_id
group by t_pp.id   into hproduct;


															select * from stock_location where id = dr.location_id into h2;
				
					---- esto es para las variables que estan en el crusor y pasarlas a las variables output
					
					almacen=dr.almacen;
					categoria=dr.categoria;
					name_template=hproduct.new_name;
					fecha=dr.fecha - interval '5' hour;
					periodo=dr.periodo;
					ctanalitica=dr.ctanalitica;
					serial=dr.serial;
					nro=dr.nro;
					operation_type=dr.operation_type;
					name=dr.name;
					type=dr.type;
					esingreso=dr.esingreso;
					product_id=dr.product_id;
					correlativovisual = dr.correlativovisual;

					correlativovisual = avanceop;

					avanceop = avanceop +1;

					location_id=dr.location_id;
					doc_type_ope=dr.doc_type_ope;
					ubicacion_origen=dr.id_origen;
					ubicacion_destino=dr.id_destino;
					stock_moveid=dr.stock_moveid;
					account_invoice=0;
					product_account=dr.product_account;
					default_code=h1.codigoproducto;
					unidad=dr.unidad;
					mrpname='';
					stock_doc=dr.stock_doc;
					origen=dr.origen;
					destino=dr.destino;
					type_doc=dr.type_doc;
								numdoc_cuadre=dr.numdoc_cuadre;
								if dr.numdoc_cuadre::varchar = ''::varchar then
									numdoc_cuadre=dr.doc_almac;
								end if;
								doc_partner=dr.nro_documento;
								lote= dr.lote;


				

					 ruc = h.nro_documento;
					 comapnyname = h.name;
					 cod_sunat = ''; 
					 default_code = h1.codigoproducto;
					 tipoprod = h1.category_sunat_code; 
					 coduni = h1.uom_sunat_code;
					 metodo = 'Costo promedio';
					 
					 period_name = dr.period_name;
					
					 fecha_albaran = dr.fecha_albaran - interval '5' hour;
					 pedido_compra = dr.pedido_compra;
					 licitacion = dr.licitacion;
					 doc_almac = dr.doc_almac;


					--- final de proceso de variables output

				
					ingreso =coalesce(dr.ingreso,0);
					salida =coalesce(dr.salida,0);
					--if dr.serial is not null then 
						debit=coalesce(dr.debit,0);
					--else
						--if dr.ubicacion_origen=8 then
							--debit =0;
						--else
							---debit = coalesce(dr.debit,0);
						--end if;
					--end if;
					

					
						credit =coalesce(dr.credit,0);
					
					cadquiere =coalesce(dr.cadquiere,0);
					precprom = cprom;
					if cadquiere <=0::numeric then
						cadquiere=cprom;
					end if;
					if salida>0::numeric then
						credit = cadquiere * salida;
					end if;
					saldov = saldov + (debit - credit);
					saldof = saldof + (ingreso - salida);
					if saldof > 0::numeric then
						if esingreso= 'ingreso' or ingreso > 0::numeric then
							if saldof != 0 then
								cprom = saldov/saldof;
							else
											cprom = saldov;
								 end if;
							if ingreso = 0 then
											cadquiere = cprom;
							else
									cadquiere =debit/ingreso;
							end if;
							--cprom = saldov / saldof;
							--cadquiere = debit / ingreso;
						else
							if salida = 0::numeric then
								if debit + credit > 0::numeric then
									cprom = saldov / saldof;
									cadquiere=cprom;
								end if;
							else
								credit = salida * cprom;
							end if;
						end if;
					else
						cprom = 0;
					end if;
						

					if saldov <= 0::numeric and saldof <= 0::numeric then
						dr.cprom = 0;
						cprom = 0;
					end if;
					--if cadquiere=0 then
					--  if trim(dr.operation_type) != '05' and trim(dr.operation_type) != '' and dr.operation_type is not null then
					--    cadquiere=precprom;
					--    debit = ingreso*cadquiere;
					--    credit=salida*cadquiere;
					--  end if;
					--end if;
					dr.debit = round(debit,8);
					dr.credit = round(credit,8);
					dr.cprom = round(cprom,8);
					dr.cadquiere = round(cadquiere,8);
					dr.credit = round(credit,8);
					dr.saldof = round(saldof,8);
					dr.saldov = round(saldov,8);
					if ingreso>0 then
						cu_entrada =debit/ingreso;
					else
						cu_entrada =debit;
					end if;

					if salida>0 then
						cu_salida =credit/salida;
					else
					cu_salida =credit;
					end if;

					RETURN NEXT;
				end if;
	end loop;
	--return query select * from vst_kardex_sunat where fecha_num(vst_kardex_sunat.fecha) between $1 and $2 and vst_kardex_sunat.product_id = ANY($3) and vst_kardex_sunat.location_id = ANY($4) order by location_id,product_id,fecha;
END
$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;


			""")			

		self.env.cr.execute("""
				 select 

				fecha_albaran as "Fecha Alb.",	
				--fecha::date as "Fecha",
				--fecha::time as "Hora",

				fecha::date as "Fecha",
				fecha::time as "Hora",				
				type_doc as "T. Doc.",
				serial as "Serie",
				nro as "Nro. Documento",
				numdoc_cuadre as "Nro. Documento",
				doc_partner as "Nro Doc. Partner",
				name as "Proveedor",							
				operation_type as "Tipo de operacion",				 
				name_template as "Producto",
				default_code as "Cod Producto",
				unidad as "Unidad",				 
				ingreso as "Ingreso Fisico",
				round(debit,6) as "Ingreso Valorado.",
				salida as "Salida Fisico",
				round(credit,6) as "Salida Valorada",
				saldof as "Saldo Fisico",
				round(saldov,6) as "Saldo valorado",
				round(cadquiere,6) as "Costo adquisicion",
				round(cprom,6) as "Costo promedio",
					origen as "Origen",
					destino as "Destino",
				almacen AS "Almacen",
				stock_moveid as "id move",
				ctanalitica as "Cta Analitica"
				from get_kardex_v_save("""+ str(date_ini).replace('-','') + "," + str(date_fin).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[],"""+str(self.env.company.id)+""")
				
		""")

		ingreso1= 0
		ingreso2= 0
		salida1= 0
		salida2= 0

		for line in self.env.cr.fetchall():
			#worksheet.write(x,0,line[0] if line[0] else '' ,formatdate )
			worksheet.write(x,1,line[1] if line[1] else '' ,formatdate )
			worksheet.write(x,2,line[2] if line[2] else '' ,formattime )
			worksheet.write(x,3,line[3] if line[3] else '' ,bord )
			worksheet.write(x,4,line[4] if line[4] else '' ,bord )
			worksheet.write(x,5,line[5] if line[5] else '' ,bord )
			worksheet.write(x,6,line[6] if line[6] else '' ,bord )
			worksheet.write(x,7,line[7] if line[7] else '' ,bord )
			worksheet.write(x,8,line[8] if line[8] else '' ,bord )
			worksheet.write(x,9,line[9] if line[9] else '' ,bord )
			worksheet.write(x,10,line[10] if line[10] else '' ,bord )
			worksheet.write(x,11,line[11] if line[11] else '' ,bord )
			worksheet.write(x,12,line[12] if line[12] else '' ,bord )
			worksheet.write(x,13,line[13] if line[13] else 0 ,numberdos )
			worksheet.write(x,14,line[14] if line[14] else 0 ,numberdos )
			worksheet.write(x,15,line[15] if line[15] else 0 ,numberdos )
			worksheet.write(x,16,line[16] if line[16] else 0 ,numberdos )
			worksheet.write(x,17,line[17] if line[17] else 0 ,numberdos )
			worksheet.write(x,18,line[18] if line[18] else 0 ,numberseis )
			worksheet.write(x,19,line[19] if line[19] else 0 ,numberocho )
			worksheet.write(x,20,line[20] if line[20] else 0 ,numberocho )
			worksheet.write(x,21,line[21] if line[21] else '' ,bord )
			worksheet.write(x,22,line[22] if line[22] else '' ,bord )
			worksheet.write(x,23,line[23] if line[23] else '' ,bord )

			if self.check_account:
				move = self.env['stock.move'].browse(line[23])
				if move.id:
					worksheet.write(x,24, move.product_id.categ_id.property_stock_valuation_account_id.code ,bord )
					worksheet.write(x,25, move.product_id.categ_id.property_stock_account_output_categ_id.code ,bord )
					worksheet.write(x,26, line[25] if line[25] else '' ,bord )
					# worksheet.write(x,26, move.analytic_tag_id.name or '' ,bord )
			
			ingreso1 += line[13] if line[13] else 0
			ingreso2 +=line[14] if line[14] else 0
			salida1 +=line[15] if line[15] else 0
			salida2 += line[16] if line[16] else 0

			x = x +1

		tam_col = [11,11,5,5,7,5,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11]

		worksheet.write(x,12,'TOTALES:' ,bold )
		worksheet.write(x,13,ingreso1 ,numberdosbold )
		worksheet.write(x,14,ingreso2 ,numberdosbold )
		worksheet.write(x,15,salida1 ,numberdosbold )
		worksheet.write(x,16,salida2 ,numberdosbold )

		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])
		worksheet.set_column('I:I', tam_col[8])
		worksheet.set_column('J:J', tam_col[9])
		worksheet.set_column('K:K', tam_col[10])
		worksheet.set_column('L:L', tam_col[11])
		worksheet.set_column('M:M', tam_col[12])
		worksheet.set_column('N:N', tam_col[13])
		worksheet.set_column('O:O', tam_col[14])
		worksheet.set_column('P:P', tam_col[15])
		worksheet.set_column('Q:Q', tam_col[16])
		worksheet.set_column('R:R', tam_col[17])
		worksheet.set_column('S:S', tam_col[18])
		worksheet.set_column('T:Z', tam_col[19])

		workbook.close()


		f = open(direccion + 'kardex_producto.xlsx', 'rb')

		return self.env['popup.it'].get_file('Kardex_Valorado.xlsx',base64.encodestring(b''.join(f.readlines())))




