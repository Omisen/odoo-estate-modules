import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

export class Hello extends Component {
    static template = "estate.Hello";
    static props = { ...standardActionServiceProps };

    setup() {
        this.state = useState({
            message: "Hello OWL, questo componente arriva dal modulo estate.",
        });
    }
}

registry.category("actions").add("estate.hello_action", Hello);