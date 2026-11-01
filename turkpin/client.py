import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Callable, Dict, List, Optional, Union
from xml.sax.saxutils import escape

from .errors import TurkpinError
from .models import Balance, Epin, Game, Order, OrderInfo, Product

LIVE_URL = "https://www.turkpin.com/api.php"
TEST_URL = "https://www.turkpin.net/api.php"

# (url, form body, timeout seconds) -> response text
Transport = Callable[[str, bytes, float], str]


class TurkpinClient:
    """Turkpin dealer API client.

    Every call is an HTTP POST to api.php with one form field, DATA, holding
    <APIRequest><params>...</params></APIRequest>. Responses are XML.
    """

    def __init__(self, username: str, password: str, test: bool = False, timeout: float = 30,
                 base_url: Optional[str] = None, transport: Optional[Transport] = None):
        if not username or not password:
            raise ValueError("username and password are required")
        self.username = username
        self.password = password
        self.url = base_url or (TEST_URL if test else LIVE_URL)
        self.timeout = timeout
        self._transport = transport or _urllib_transport

    def get_games(self) -> List[Game]:
        p = self.call("epinOyunListesi")
        return [Game(int(_t(g, "id")), _t(g, "name")) for g in p.findall("oyunListesi/oyun")]

    def get_products(self, game_id: int, product_id: Optional[int] = None) -> List[Product]:
        params: Dict[str, object] = {"oyunKodu": game_id}
        if product_id is not None:
            params["urunKodu"] = product_id
        p = self.call("epinUrunleri", params)
        return [
            Product(
                id=int(_t(u, "id")),
                name=_t(u, "name"),
                stock=_int(_t(u, "stock")),
                min_order=max(1, _int(_t(u, "min_order"))),
                max_order=_int(_t(u, "max_order")),
                price=_dec(_t(u, "price")),
                tax_type=_t(u, "tax_type"),
                pre_order=_t(u, "pre_order").lower() == "true",
                min_barem=_dec_opt(_t(u, "min_barem")),
                max_barem=_dec_opt(_t(u, "max_barem")),
                barem_step=_dec_opt(_t(u, "barem_step")),
            )
            for u in p.findall("epinUrunListesi/urun")
        ]

    def create_order(self, game_id: int, product_id: int, quantity: int = 1, character: Optional[str] = None,
                     pre_order: bool = False, barem: Union[Decimal, str, None] = None) -> Order:
        """Places an e-pin order.

        pre_order must be True for products listed with pre_order=True. barem is the amount for tiered
        products (between min_barem and max_barem, in barem_step steps).
        """
        params: Dict[str, object] = {"oyunKodu": game_id, "urunKodu": product_id, "adet": quantity}
        if character is not None:
            params["character"] = character
        if pre_order:
            params["pre_order"] = "true"
        if barem is not None:
            params["barem"] = barem
        p = self.call("epinSiparisYarat", params)
        return Order(order_no=_t(p, "siparisNo"), result=_t(p, "siparisSonuc"),
                     amount=_dec(_t(p, "siparisTutari")), epins=_epins(p))

    def get_order_status(self, order_no: str) -> OrderInfo:
        return _order_info(self.call("siparisDurumu", {"siparisNo": order_no}))

    def list_orders(self, start: Union[date, str], end: Union[date, str]) -> List[OrderInfo]:
        """Orders between two dates (inclusive, at most 30 days apart)."""
        ymd = lambda d: d.strftime("%Y-%m-%d") if isinstance(d, date) else d  # noqa: E731
        p = self.call("siparisListesi", {"baslangicTarihi": ymd(start), "bitisTarihi": ymd(end)})
        return [_order_info(s) for s in p.findall("SIPARISLER/SIPARIS")]

    def get_balance(self) -> Balance:
        b = self.call("balance").find("balanceInformation")
        return Balance(*(_dec(_t(b, k)) for k in ("balance", "credit", "bonus", "spending")))

    def call(self, cmd: str, params: Optional[Dict[str, object]] = None) -> ET.Element:
        """Sends one command and returns the <params> element of the response."""
        fields = {"cmd": cmd, "username": self.username, "password": self.password, **(params or {})}
        xml = "<APIRequest><params>" + "".join(
            f"<{k}>{escape(str(v))}</{k}>" for k, v in fields.items()) + "</params></APIRequest>"
        body = urllib.parse.urlencode({"DATA": xml}).encode()
        raw = self._transport(self.url, body, self.timeout)
        try:
            p = ET.fromstring(raw.strip().encode()).find("params")
        except ET.ParseError:
            p = None
        if p is None:
            raise TurkpinError("Invalid response from Turkpin API: " + raw[:200])
        code = _t(p, "error") or _t(p, "HATA_NO")
        if code and code != "000":
            raise TurkpinError(_t(p, "error_desc") or _t(p, "HATA_ACIKLAMA") or "Turkpin API error", code)
        return p


def _urllib_transport(url: str, body: bytes, timeout: float) -> str:
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code == 401:  # the API still sends an XML error body
            return e.read().decode("utf-8", "replace")
        raise TurkpinError(f"HTTP {e.code} from Turkpin API") from e
    except (urllib.error.URLError, OSError) as e:
        raise TurkpinError(f"HTTP request failed: {e}") from e


def _t(el: Optional[ET.Element], name: str) -> str:
    c = el.find(name) if el is not None else None
    return (c.text or "").strip() if c is not None else ""


def _int(s: str) -> int:
    try:
        return int(s)
    except ValueError:
        return 0


def _dec(s: str) -> Decimal:
    try:
        return Decimal(s)
    except InvalidOperation:
        return Decimal(0)


def _dec_opt(s: str) -> Optional[Decimal]:
    return _dec(s) if s else None


def _epins(el: ET.Element) -> List[Epin]:
    return [Epin(_t(e, "code"), _t(e, "desc"), _t(e, "id")) for e in el.findall("epin_list/epin")]


def _order_info(s: ET.Element) -> OrderInfo:
    return OrderInfo(
        order_no=_t(s, "SIPARIS_NO"),
        status=_int(_t(s, "SIPARIS_DURUMU")),
        description=_t(s, "SIPARIS_DURUMU_ACIKLAMA"),
        state_code=_t(s, "DURUM_KODU"),
        checked_at=_t(s, "KONTROL_TARIHI"),
        amount=_dec(_t(s, "SIPARIS_TUTARI")),
        extra=_t(s, "EKSTRA") or _t(s, "EXTRA"),
        epins=_epins(s),
    )
