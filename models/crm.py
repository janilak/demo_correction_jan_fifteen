from odoo import fields,models,api,_
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime


class CrmLead(models.Model):
    _inherit = 'crm.lead'


    def enquiry_purchase_single(self):
        my_check_wc_list = []
        vendors_len = len(
            self.enquiry_lines.filtered(lambda a: a.product_uom_qty > a.product_onhand_qty).mapped('supplier_name'))
        if vendors_len <= 1:
            for line in self.enquiry_lines:
                if not line.created_pq:
                    line.created_pq = True
                    if line.product_uom_qty > line.product_onhand_qty:
                        qty = line.product_uom_qty - line.product_onhand_qty
                        product_line = (0, 0, {
                            'product_id': line.product_id.id,
                            'name': line.description,
                            'product_qty': qty,
                            'part_number': line.part_number,
                            'price_unit': 0,
                            'c_mfr': line.c_mfr,
                            'c_pn': line.c_pn,
                            'categ_id': line.categ_id.id,
                            'part_number_mfr': line.part_number_mfr,
                            'enquiry_line_id': line.id,
                            # 'reference_number':line.reference_number,
                            # 'remarks':line.remarks,
                            'availability': line.availability,
                            'state': 'draft',
                            'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            'product_uom': line.product_uom.id,
                        })
                        my_check_wc_list.append(product_line)

            view_id = self.env.ref('purchase.purchase_order_form')
            return {
                'name': _('New Purchase Quotation'),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'view_id': view_id.id,
                'views': [(view_id.id, 'form')],
                'context': {
                    'default_state': 'draft',
                    'default_inquiry_id': [(6, 0, self.ids)],
                    'default_customer_reference': self.customer_reference,
                    'default_order_line': my_check_wc_list,
                    'default_partner_id': self.enquiry_lines.supplier_name.id,
                }
            }
        else:
            for supl in self.enquiry_lines.mapped('supplier_name'):
                my_check_wc_list = []
                sl_no = 1
                for line in self.enquiry_lines.search([('crm_id', '=', self.id), ('supplier_name', '=', supl.id)]):
                    if not line.created_pq :
                        if line.product_uom_qty > line.product_onhand_qty:
                            qty = line.product_uom_qty - line.product_onhand_qty
                            product_line = (0, 0, {
                            'serial_number':sl_no,
                            'product_id': line.product_id.id,
                            'iu_ref':line.product_id.product_tmpl_id.internal_unique_no,
                            'name': line.description,
                            'product_qty': qty,
                            'part_number': line.part_number,
                            'price_unit': 0,
                            'part_number_one': line.part_number_one,
                            'c_mfr': line.c_mfr,
                            'c_pn': line.c_pn,
                            'categ_id': line.categ_id.id,
                            'part_number_mfr': line.part_number_mfr,
                            'enquiry_line_id': line.id,
                            # 'reference_number':line.reference_number,
                            # 'remarks':line.remarks,
                            'availability': line.availability,
                            'state': 'draft',
                            'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            'product_uom': line.product_uom.id,
                            })
                            my_check_wc_list.append(product_line)
                            sl_no = sl_no + 1
                currency_id = self.company_id.currency_id.id
                if supl.property_purchase_currency_id:
                    currency_id = supl.property_purchase_currency_id.id

                if my_check_wc_list:
                    self.env['purchase.order'].create({
                        'partner_id': supl.id,
                        'state': 'draft',
                        'search_field': self.customer_reference,
                        'customer_reference': self.customer_reference,
                        'inquiry_id': [(6, 0, self.ids)],
                        'order_line': my_check_wc_list,
                        'currency_id':currency_id
                    })
            for enq in self.enquiry_lines:
                enq.created_pq = True


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    @api.onchange('incl_supplier_price')
    def include_supplier_price(self):
        approved_pos = self.opportunity_id.purchase_ids.filtered(lambda a: a.po_state == 'approve')
        if approved_pos:
            for line in self.order_line:
                line.supplier = approved_pos[0].partner_id
                line.supplier_price = approved_pos[0].order_line.filtered(
                    lambda a: a.product_id == line.product_id and a.name == line.name).price_unit