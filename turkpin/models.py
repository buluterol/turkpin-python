from dataclasses import dataclass, field
from decimal import Decimal
from enum import IntEnum
from typing import List, Optional


class OrderStatus(IntEnum):
    """Values of SIPARIS_DURUMU returned by siparisDurumu and siparisListesi."""

    PROCESSING = 1
    COMPLETED = 2
    CANCELLED = 3
    DELIVERING = 99
    PRE_ORDER_DELIVERING = 199


@dataclass(frozen=True)
class Game:
    id: int
    name: str


@dataclass(frozen=True)
class Product:
    id: int
    name: str
    stock: int
    min_order: int
    max_order: int  # 0 means no upper limit
    price: Decimal
    tax_type: str
    pre_order: bool
    # Tiered (barem) products: allowed amount range and step, otherwise None
    min_barem: Optional[Decimal] = None
    max_barem: Optional[Decimal] = None
    barem_step: Optional[Decimal] = None

    @property
    def is_tiered(self) -> bool:
        return self.min_barem is not None


@dataclass(frozen=True)
class Epin:
    code: str
    description: str
    id: str


@dataclass(frozen=True)
class Order:
    order_no: str
    result: str  # "Success" or "Pending"
    amount: Decimal
    epins: List[Epin] = field(default_factory=list)

    @property
    def pending(self) -> bool:
        """True for pre-order / tiered orders: poll get_order_status for the codes."""
        return self.result != "Success"


@dataclass(frozen=True)
class OrderInfo:
    order_no: str
    status: int  # an OrderStatus value
    description: str
    state_code: str  # "000" normally, "999" when the order has a problem being handled by Turkpin
    checked_at: str
    amount: Decimal
    extra: str  # cancellation reason or problem note
    epins: List[Epin] = field(default_factory=list)


@dataclass(frozen=True)
class Balance:
    balance: Decimal
    credit: Decimal
    bonus: Decimal
    spending: Decimal
