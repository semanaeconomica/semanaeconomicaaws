
DROP VIEW IF EXISTS vst_kardex_fisico1 CASCADE;

CREATE OR REPLACE VIEW vst_kardex_fisico1 AS 
 SELECT stock_move.product_uom, 
        CASE
            WHEN sl.usage::text = 'supplier'::text THEN 0::double precision
            ELSE 
            CASE
                WHEN original.id <> uomt.id THEN round((stock_move.price_unit * original.factor::double precision / uomt.factor::double precision)::numeric, 6)::double precision
                ELSE stock_move.price_unit
            END
        END AS price_unit, 
        CASE
            WHEN uom_uom.id <> uomt.id THEN round((stock_move.product_uom_qty::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
            ELSE stock_move.product_uom_qty
        END AS product_qty, 
    stock_move.location_id, stock_move.location_dest_id, 
    stock_move.picking_type_id, stock_move.product_id, stock_move.picking_id, 
    stock_picking.invoice_id AS invoice_id, 
        CASE
            WHEN stock_picking.use_kardex_date THEN stock_picking.kardex_date::timestamp without time zone
            ELSE 
            coalesce( invoice.invoice_date::timestamp without time zone,stock_picking.kardex_date::timestamp without time zone)
        END AS date, 
    stock_picking.name, stock_picking.partner_id, 
    case when tok.id is not null then tok.code || '-' || tok.name else '' end AS guia, null::text as analitic_id, stock_move.id, 
    product_product.default_code, stock_move.state AS estado,



l_o.complete_name AS u_origen,
l_o.usage as usage_origen,
l_d.complete_name AS u_destino,
l_d.usage as usage_destino,
pc.name as categoria,
pc.id as categoria_id,
coalesce(it.value,product_template.name)::varchar  as producto,
product_product.default_code as cod_pro,
uomt.name as unidad



   FROM stock_move
   join uom_uom ON stock_move.product_uom = uom_uom.id
   join stock_location l_o on l_o.id = stock_move.location_id
   join stock_location l_d on l_d.id = stock_move.location_dest_id
   JOIN stock_picking ON stock_move.picking_id = stock_picking.id
    left join account_move as invoice on invoice.id = stock_picking.invoice_id
   JOIN stock_picking_type ON stock_picking.picking_type_id = stock_picking_type.id
   JOIN stock_location sl ON sl.id = stock_move.location_dest_id
   JOIN product_product ON stock_move.product_id = product_product.id
   JOIN product_template ON product_product.product_tmpl_id = product_template.id
left join ir_translation it ON product_template.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
  inner join product_category pc on pc.id = product_template.categ_id
   join uom_uom uomt ON uomt.id = product_template.uom_id
   join uom_uom original ON original.id = product_template.uom_id
   LEFT JOIN type_operation_kardex tok ON stock_picking.type_operation_sunat_id = tok.id
  WHERE (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL;

CREATE OR REPLACE FUNCTION vst_kardex_fisico () 
	RETURNS TABLE (
		product_uom integer, 
		price_unit double precision, 
		product_qty numeric, 
		location_id integer, 
		location_dest_id integer, 
		picking_type_id integer, 
		product_id integer, 
		picking_id integer, 
		invoice_id integer, 
		date timestamp without time zone, 
		name character varying, 
		partner_id integer, 
		guia text, 
		analitic_id text, 
		id integer, 
		default_code character varying, 
		estado character varying,
    u_origen varchar,
    usage_origen varchar,
    u_destino varchar,
    usage_destino varchar,
    categoria varchar,
    categoria_id integer,
    producto varchar,
    cod_pro varchar,
    unidad varchar
) 
AS $$
BEGIN
		IF EXISTS(SELECT *
                   FROM information_schema.tables
                   WHERE table_schema = current_schema()
                         AND table_name = 'vst_mrp_kardex') THEN
                        RETURN QUERY 
			SELECT * FROM vst_kardex_fisico1
			UNION ALL
			SELECT * FROM vst_mrp_kardex;
		ELSE
			RETURN QUERY 
			SELECT * FROM vst_kardex_fisico1;
		END IF;
END; $$ 

LANGUAGE 'plpgsql';







CREATE OR REPLACE FUNCTION vst_kardex_fisico () 
  RETURNS TABLE (
    product_uom integer, 
    price_unit double precision, 
    product_qty numeric, 
    location_id integer, 
    location_dest_id integer, 
    picking_type_id integer, 
    product_id integer, 
    picking_id integer, 
    invoice_id integer, 
    date timestamp without time zone, 
    name character varying, 
    partner_id integer, 
    guia text, 
    analitic_id text, 
    id integer, 
    default_code character varying, 
    estado character varying,
    u_origen varchar,
    usage_origen varchar,
    u_destino varchar,
    usage_destino varchar,
    categoria varchar,
    categoria_id integer,
    producto varchar,
    cod_pro varchar,
    unidad varchar
) 
AS $$
BEGIN
    IF EXISTS(SELECT *
                   FROM information_schema.tables
                   WHERE table_schema = current_schema()
                         AND table_name = 'vst_mrp_kardex') THEN
                        RETURN QUERY 
      SELECT 
      vst_kardex_fisico1.product_uom , 
    vst_kardex_fisico1.price_unit , 
    vst_kardex_fisico1.product_qty , 
    vst_kardex_fisico1.location_id , 
    vst_kardex_fisico1.location_dest_id , 
    vst_kardex_fisico1.picking_type_id , 
    vst_kardex_fisico1.product_id , 
    vst_kardex_fisico1.picking_id , 
    vst_kardex_fisico1.invoice_id , 
    vst_kardex_fisico1.date , 
    vst_kardex_fisico1.name , 
    vst_kardex_fisico1.partner_id , 
    vst_kardex_fisico1.guia , 
    vst_kardex_fisico1.analitic_id , 
    vst_kardex_fisico1.id , 
    vst_kardex_fisico1.default_code , 
    vst_kardex_fisico1.estado ,
    vst_kardex_fisico1.u_origen ,
    vst_kardex_fisico1.usage_origen ,
    vst_kardex_fisico1.u_destino ,
    vst_kardex_fisico1.usage_destino ,
    vst_kardex_fisico1.categoria ,
    vst_kardex_fisico1.categoria_id ,
    vst_kardex_fisico1.producto ,
    vst_kardex_fisico1.cod_pro ,
    vst_kardex_fisico1.unidad  FROM vst_kardex_fisico1;
    ELSE
      RETURN QUERY 
      SELECT 
      vst_kardex_fisico1.product_uom , 
    vst_kardex_fisico1.price_unit , 
    vst_kardex_fisico1.product_qty , 
    vst_kardex_fisico1.location_id , 
    vst_kardex_fisico1.location_dest_id , 
    vst_kardex_fisico1.picking_type_id , 
    vst_kardex_fisico1.product_id , 
    vst_kardex_fisico1.picking_id , 
    vst_kardex_fisico1.invoice_id , 
    vst_kardex_fisico1.date , 
    vst_kardex_fisico1.name , 
    vst_kardex_fisico1.partner_id , 
    vst_kardex_fisico1.guia , 
    vst_kardex_fisico1.analitic_id , 
    vst_kardex_fisico1.id , 
    vst_kardex_fisico1.default_code , 
    vst_kardex_fisico1.estado ,
    vst_kardex_fisico1.u_origen ,
    vst_kardex_fisico1.usage_origen ,
    vst_kardex_fisico1.u_destino ,
    vst_kardex_fisico1.usage_destino ,
    vst_kardex_fisico1.categoria ,
    vst_kardex_fisico1.categoria_id ,
    vst_kardex_fisico1.producto ,
    vst_kardex_fisico1.cod_pro ,
    vst_kardex_fisico1.unidad  FROM vst_kardex_fisico1;
    END IF;
END; $$ 

LANGUAGE 'plpgsql';

