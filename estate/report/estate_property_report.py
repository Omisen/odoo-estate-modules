from odoo import models, api

class EstatePropertyReport(models.AbstractModel):
    _name = "report.estate.report_property_estate_template"
    _description = "Estate Property PDF Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["estate.property"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "estate.property",
            "docs": docs,
        }
