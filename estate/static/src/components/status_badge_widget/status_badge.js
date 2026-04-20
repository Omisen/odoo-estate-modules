import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class EstateStatusBadgeField extends Component {
    static template = "estate.StatusBadgeField";
    static props = { ...standardFieldProps };

    
    get value() {
        return this.props.record.data[this.props.name] || "";
    }

    // `label` trasforma il valore tecnico della selection in etichetta leggibile.
    // Odoo espone la definizione del campo in `record.fields[name]`, e per i campi
    // selection contiene un array di coppie `[valore, etichetta]`.
    // Qui cerchiamo la coppia con chiave uguale al valore corrente e restituiamo
    // la label da mostrare nel badge, ad esempio `Offer Received` invece di
    // `offer_recieved`. Se il valore non viene trovato, facciamo fallback sul
    // valore grezzo cosi' il widget continua comunque a renderizzare qualcosa.
    get label() {
        const selection = this.props.record.fields[this.props.name]?.selection || [];
        return selection.find(([value]) => value === this.value)?.[1] || this.value;
    }

    // `badgeClass` mappa lo stato corrente a una classe CSS specifica.
    // Il template usa questa classe per applicare il colore corretto del badge:
    // grigio per `new`, arancione per `offer_recieved`, verde per `sold`
    // e rosso per `cancelled`.
    // Se arriva un valore non previsto, usiamo la classe di default `new`
    // cosi' il widget resta stabile anche in presenza di dati inattesi.
    get badgeClass() {
        return {
            new: "o_estate_status_badge--new",
            offer_recieved: "o_estate_status_badge--offer-recieved",
            offer_accepted: "o_estate_status_badge--offer-accepted",
            sold: "o_estate_status_badge--sold",
            cancelled: "o_estate_status_badge--cancelled",
        }[this.value] || "o_estate_status_badge--new";
    }
}

// Qui registriamo il componente nel registry dei field widget di Odoo.
// Il nome `estate_status_badge` e' quello che poi viene richiamato nelle view XML
// con `widget="estate_status_badge"`.
// `supportedTypes: ["selection"]` limita l'uso del widget ai campi selection,
// mentre `isEmpty: () => false` dice a Odoo di considerare sempre il widget come
// renderizzabile, anche quando il campo non ha ancora un valore impostato.
registry.category("fields").add("estate_status_badge", {
    component: EstateStatusBadgeField,
    displayName: "Estate Status Badge",
    supportedTypes: ["selection"],
    isEmpty: () => false,
});