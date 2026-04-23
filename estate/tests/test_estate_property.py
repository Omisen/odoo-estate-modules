from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError

class TestEstateProperty(TransactionCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # property type (richiesto dal modello)
        cls.property_type = cls.env["estate.property.type"].create({
            "name": "Test Type",
            "category": "residential",
        })
        
        # partner acquirente
        cls.partner = cls.env["res.partner"].create({
            "name": "Test Buyer",
        })

        # property base riusabile nei test
        cls.property = cls.env["estate.property"].create({
            "name": "Test Property",
            "expected_price": 100000,
            "property_type_id": cls.property_type.id,
        })
        
        def test_cannot_sell_cancelled_property(self):
            prop = self.env["estate.property"].create({
                "name": "Cancelled Property",
                "expected_price": 100000,
                "property_type_id": self.property_type.id,
            })
            prop.with_context(bypass_reset=True).write({"status": "cancelled"})
        
            with self.assertRaises(UserError):
                prop.set_status_to_sold()
                

        def test_cannot_cancel_sold_property(self):
            prop = self.env["estate.property"].create({
                "name": "Sold Property",
                "expected_price": 100000,
                "property_type_id": self.property_type.id,
            })
            prop.with_context(bypass_reset=True).write({"status": "sold"})
        
            with self.assertRaises(UserError):
                prop.set_status_to_cancel()
                
                
        def test_offer_creation_sets_status(self):
            prop = self.env["estate.property"].create({
                "name": "Offer Property",
                "expected_price": 100000,
                "property_type_id": self.property_type.id,
            })
            self.env["estate.property.offer"].create({
                "price": 90000,
                "partner_id": self.partner.id,
                "property_id": prop.id,
            })
            self.assertEqual(prop.status, "offer_recieved")
            

        def test_accept_offer_sets_buyer_and_price(self):
            prop = self.env["estate.property"].create({
                "name": "Accept Property",
                "expected_price": 100000,
                "property_type_id": self.property_type.id,
            })
            offer = self.env["estate.property.offer"].create({
                "price": 95000,
                "partner_id": self.partner.id,
                "property_id": prop.id,
            })
            offer.set_offer_to_accept()
            self.assertEqual(prop.status, "offer_accepted")
            self.assertEqual(prop.buyer, self.partner)
            self.assertEqual(prop.selling_price, 95000)

        def test_accept_refuses_other_offers(self):
            prop = self.env["estate.property"].create({
                "name": "Multi Offer Property",
                "expected_price": 100000,
                "property_type_id": self.property_type.id,
            })
            partner2 = self.env["res.partner"].create({"name": "Other Buyer"})
            offer1 = self.env["estate.property.offer"].create({
                "price": 90000,
                "partner_id": self.partner.id,
                "property_id": prop.id,
            })
            
            offer2 = self.env["estate.property.offer"].create({
                "price": 95000,
                "partner_id": partner2.id,
                "property_id": prop.id,
            })
            
            offer2.set_offer_to_accept()
            self.assertEqual(offer1.status, "refuse")
            self.assertEqual(offer2.status, "accept")

        def test_offer_lower_than_best_raises(self):
            prop = self.env["estate.property"].create({
                "name": "Best Offer Property",
                "expected_price": 100000,
                "property_type_id": self.property_type.id,
            })
            partner2 = self.env["res.partner"].create({"name": "Outbid Buyer"})
            
            self.env["estate.property.offer"].create({
                "price": 95000,
                "partner_id": self.partner.id,
                "property_id": prop.id,
            })
            
            with self.assertRaises(ValidationError):
                self.env["estate.property.offer"].create({
                    "price": 80000,
                    "partner_id": partner2.id,
                    "property_id": prop.id,
                })