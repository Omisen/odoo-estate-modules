import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class OfferCountBadgeField extends Component {
    static template = "estate.OfferCountBadgeField";
    static props = { ...standardFieldProps };

    get count() {
        return this.props.record.data[this.props.name] || 0;
    }

    get label() {
        return this.count === 1 ? "Offer" : "Offers";
    }
}

registry.category("fields").add("estate_offer_count_badge", {
    component: OfferCountBadgeField,
    displayName: "Estate Offer Count Badge",
    supportedTypes: ["integer"],
    isEmpty: () => false,
});