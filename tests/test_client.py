import unittest
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal
from pathlib import Path

from turkpin import LIVE_URL, TEST_URL, OrderStatus, TurkpinClient, TurkpinError

FIX = Path(__file__).parent / "fixtures"


class ClientTest(unittest.TestCase):
    def client(self, fixture, test=True):
        body = fixture if fixture.startswith("<") else (FIX / fixture).read_text(encoding="utf-8")
        self.sent = []

        def transport(url, data, timeout):
            self.sent.append((url, data))
            return body

        return TurkpinClient("dealer@example.com", "s3cr<et", test=test, transport=transport)

    def params(self):
        form = urllib.parse.parse_qs(self.sent[-1][1].decode())
        return ET.fromstring(form["DATA"][0]).find("params")

    def test_request_format(self):
        self.client("games.xml").get_games()
        self.assertEqual(self.sent[0][0], TEST_URL)
        p = self.params()
        self.assertEqual(p.findtext("cmd"), "epinOyunListesi")
        self.assertEqual(p.findtext("password"), "s3cr<et")

    def test_live_by_default(self):
        self.client("balance.xml", test=False).get_balance()
        self.assertEqual(self.sent[0][0], LIVE_URL)

    def test_games(self):
        games = self.client("games.xml").get_games()
        self.assertEqual([(g.id, g.name) for g in games], [(1, "Game 1"), (2, "Game 2")])

    def test_products(self):
        a, b = self.client("products.xml").get_products(1)
        self.assertEqual(self.params().findtext("oyunKodu"), "1")
        self.assertEqual((a.stock, a.max_order, a.price, a.pre_order), (26278, 0, Decimal("0.001"), False))
        self.assertFalse(a.is_tiered)
        self.assertTrue(b.pre_order and b.is_tiered)
        self.assertEqual((b.min_barem, b.max_barem, b.barem_step), (Decimal(25), Decimal(1250), Decimal("0.01")))
        self.assertEqual(b.max_order, 5)

    def test_create_order(self):
        o = self.client("order_success.xml").create_order(1, 4, 2, character="Player1")
        p = self.params()
        self.assertEqual((p.findtext("adet"), p.findtext("character")), ("2", "Player1"))
        self.assertIsNone(p.find("pre_order"))
        self.assertEqual(o.order_no, "25031013105101")
        self.assertFalse(o.pending)
        self.assertEqual(o.epins[0].code, "S3XS-EEDY-APAE-62EM")
        self.assertEqual(o.epins[0].description, "Test Ürün")

    def test_pre_order_with_barem(self):
        o = self.client("order_pending.xml").create_order(1, 4, pre_order=True, barem="30.50")
        p = self.params()
        self.assertEqual((p.findtext("pre_order"), p.findtext("barem")), ("true", "30.50"))
        self.assertTrue(o.pending)
        self.assertEqual(o.epins, [])

    def test_api_errors(self):
        with self.assertRaises(TurkpinError) as cm:
            self.client("order_out_of_stock.xml").create_order(1, 2)
        self.assertEqual((cm.exception.code, str(cm.exception)), ("012", "Urun stok yetersiz."))
        with self.assertRaises(TurkpinError) as cm:
            self.client("error_auth.xml").get_games()
        self.assertEqual(cm.exception.code, "001")

    def test_invalid_response(self):
        with self.assertRaises(TurkpinError):
            self.client("<html>blocked</html").get_balance()

    def test_order_status(self):
        s = self.client("status_completed.xml").get_order_status("25031013105101")
        self.assertEqual(s.status, OrderStatus.COMPLETED)
        self.assertEqual(s.amount, Decimal("0.0010"))
        self.assertEqual(s.epins[0].code, "S3XS-EEDY-APAE-62EM")
        c = self.client("status_cancelled.xml").get_order_status("25030620073001")
        self.assertEqual((c.status, c.extra), (OrderStatus.CANCELLED, "Stok yok"))

    def test_list_orders(self):
        orders = self.client("orders.xml").list_orders(date(2026, 1, 1), "2026-01-30")
        p = self.params()
        self.assertEqual((p.findtext("baslangicTarihi"), p.findtext("bitisTarihi")), ("2026-01-01", "2026-01-30"))
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0].status, OrderStatus.PROCESSING)
        self.assertEqual((orders[1].state_code, orders[1].extra), ("999", "CANCELLATION REASON"))

    def test_balance(self):
        b = self.client("balance.xml").get_balance()
        self.assertEqual((b.balance, b.spending), (Decimal("98689.0000"), Decimal("1311.0000")))


if __name__ == "__main__":
    unittest.main()
