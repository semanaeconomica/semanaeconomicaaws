DROP FUNCTION IF EXISTS public.update_main_parameter(integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.update_main_parameter(
    company_id integer,
	dir_file character varying,
    parameter_id integer
) RETURNS BOOLEAN LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
update main_parameter set 
surrender_nc=(select id from account_account where code='1413001' and account_account.company_id=$1),
surrender_fc=(select id from account_account where code='1413002' and account_account.company_id=$1),
supplier_advance_account_nc=(select id from account_account where code='4220001' and account_account.company_id=$1),
supplier_advance_account_fc=(select id from account_account where code='4220002' and account_account.company_id=$1),
customer_advance_account_nc=(select id from account_account where code='1220001' and account_account.company_id=$1),
customer_advance_account_fc=(select id from account_account where code='1220002' and account_account.company_id=$1),
detractions_account=(select id from account_account where code='4250000' and account_account.company_id=$1),
customer_account_detractions=(select id from account_account where code='1212500' and account_account.company_id=$1),
profit_account_ed=(select id from account_account where code='7760000' and account_account.company_id=$1),
loss_account_ed=(select id from account_account where code='6760000' and account_account.company_id=$1),
surrender_journal_nc=(select id from account_journal where code='RMN' and type='cash' and account_journal.company_id=$1),
surrender_journal_fc=(select id from account_journal where code='RME' and type='cash' and account_journal.company_id=$1),
destination_journal=(select id from account_journal where code='AUT' and type='general' and account_journal.company_id=$1),
detraction_journal=(select id from account_journal where code='PDET' and type='general' and account_journal.company_id=$1),
credit_journal=(select id from account_journal where code='ANC' and type='general' and account_journal.company_id=$1),
supplier_advance_sequence=(select id from ir_sequence where name='ANTICIPOS DE PROVEEDOR' and ir_sequence.company_id=$1),
dt_national_credit_note=(select id from einvoice_catalog_01 where einvoice_catalog_01.code='07'),
td_recibos_hon=(select id from einvoice_catalog_01 where einvoice_catalog_01.code='02'),
exportation_document=(select id from einvoice_catalog_01 where einvoice_catalog_01.code='50'),
proff_payment_wa=(select id from einvoice_catalog_01 where einvoice_catalog_01.code='91'),
debit_note_wa=(select id from einvoice_catalog_01 where einvoice_catalog_01.code='98'),
credit_note_wa=(select id from einvoice_catalog_01 where einvoice_catalog_01.code='97'),
dt_sunat_ruc=(select id from l10n_latam_identification_type where l10n_latam_identification_type.name='VAT'),
dt_sunat_dni=(select id from l10n_latam_identification_type where l10n_latam_identification_type.name='DNI'),
ruc_size = 11,
dni_size = 8,
account_plan_code=(select id from account_chart_template where account_chart_template.name='Peru - PCGE 2019'),
cash_account_prefix='101,102,103,105',
bank_account_prefix='104,106,107',
cancelation_partner=(select id from res_partner where name='DOCUMENTOS ANULADOS' and vat='00000000000' limit 1),
sale_ticket_partner=(select id from res_partner where name='BOLETAS DE VENTAS' and vat='00000000002' limit 1),
dir_create_file=$2,
dir_ple_create_file=$2,
dir_download=$2,
dir_download_url=$2,
fiscal_year=(select id from account_fiscal_year where account_fiscal_year.name='2021'),
--invoice_payment_term=(select id from account_payment_term where name='Pago inmediato'),
tax_account=(select id from account_account_tag where account_account_tag.name='PER-C'),
dt_perception=(select id from einvoice_catalog_01 where einvoice_catalog_01.code='00'),
customer_invoice_account_nc=(select id from account_account where code='1212001' and account_account.company_id=$1),
customer_invoice_account_fc=(select id from account_account where code='1212002' and account_account.company_id=$1),
customer_letter_account_nc=(select id from account_account where code='1232001' and account_account.company_id=$1),
customer_letter_account_fc=(select id from account_account where code='1232002' and account_account.company_id=$1),
rounding_gain_account=(select id from account_account where code='7599000' and account_account.company_id=$1),
rounding_loss_account=(select id from account_account where code='6592000' and account_account.company_id=$1),
supplier_invoice_account_nc=(select id from account_account where code='4212001' and account_account.company_id=$1),
supplier_invoice_account_fc=(select id from account_account where code='4212002' and account_account.company_id=$1),
supplier_letter_account_nc=(select id from account_account where code='4230001' and account_account.company_id=$1),
supplier_letter_account_fc=(select id from account_account where code='4230002' and account_account.company_id=$1),
exchange_difference = True,
balance_sheet_account=(select id from account_account where code='8910000' and account_account.company_id=$1),
lost_sheet_account=(select id from account_account where code='8920000' and account_account.company_id=$1),
profit_result_account=(select id from account_account where code='5911000' and account_account.company_id=$1),
lost_result_account=(select id from account_account where code='5921000' and account_account.company_id=$1)
--Etiqueta para Kardex
where main_parameter.id = $3;
RETURN FOUND;
END;
$$;