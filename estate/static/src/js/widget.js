/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class Widget extends Component {
    static template = "estate.Widget";
    static props = { 
        ...standardFieldProps, 
        postcode : { type: String, optional: true},
    };

    get fieldValue() {
        return this.props.record.data[this.props.name] || "";
    }
    get postcodeValue() {
        return this.props.record.data[this.props.postcode] || "";
    }
}

registry.category("fields").add("estate_hello_widget", {
    component: Widget,
    supportedTypes: ["char"],
    extractProps: ({attrs}) => ({
        postcode : attrs.postcode,
    }),
});