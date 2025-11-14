CREATE OR REPLACE VIEW vst_mrp_kardex AS 
 SELECT sm.product_uom,
    sm.price_unit,
    sml.qty_done AS product_qty,
    sm.location_id,
    sm.location_dest_id,
    sm.picking_type_id,
    sm.product_id,
    0 AS picking_id,
    0 AS invoice_id,
    mp.kardex_date AS date,
    mp.name,
    1 AS partner_id,
        CASE
            WHEN tok.id IS NOT NULL THEN (tok.code::text || '-'::text) || tok.name::text
            ELSE '-'::text
        END AS guia,
    NULL::text AS analitic_id,
    sm.id,
    pp.default_code,
    mp.state AS estado
   FROM mrp_production mp
     JOIN stock_move sm ON sm.raw_material_production_id = mp.id
     JOIN stock_move_line sml ON sml.move_id = sm.id
     JOIN product_product pp ON sm.product_id = pp.id
     JOIN product_template pt ON pp.product_tmpl_id = pt.id
     LEFT JOIN type_operation_kardex tok ON mp.operation_type_sunat_consume = tok.id
  WHERE sm.state::text = 'done'::text AND pt.type::text = 'product'::text AND pt.active
UNION ALL
 SELECT sm.product_uom,
    sm.price_unit,
    sml.qty_done AS product_qty,
    sm.location_id,
    sm.location_dest_id,
    sm.picking_type_id,
    sm.product_id,
    0 AS picking_id,
    0 AS invoice_id,
    mp.kardex_date AS date,
    mp.name,
    1 AS partner_id,
        CASE
            WHEN tok.id IS NOT NULL THEN (tok.code::text || '-'::text) || tok.name::text
            ELSE '-'::text
        END AS guia,
    NULL::text AS analitic_id,
    sm.id,
    pp.default_code,
    mp.state AS estado
   FROM mrp_production mp
     JOIN stock_move sm ON sm.production_id = mp.id
     JOIN stock_move_line sml ON sml.move_id = sm.id
     JOIN product_product pp ON sm.product_id = pp.id
     JOIN product_template pt ON pp.product_tmpl_id = pt.id
     LEFT JOIN type_operation_kardex tok ON mp.operation_type_sunat_fp = tok.id
  WHERE sm.raw_material_production_id IS NULL AND sm.state::text = 'done'::text AND pt.type::text = 'product'::text AND pt.active;
