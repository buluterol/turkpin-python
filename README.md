# turkpin-python

[![test](https://github.com/buluterol/turkpin-python/actions/workflows/test.yml/badge.svg)](https://github.com/buluterol/turkpin-python/actions/workflows/test.yml)

Turkpin bayi API'si için Python istemcisi; Django, Flask ve FastAPI entegrasyonu dahil: e-pin oyun ve ürün listesi, sipariş verme, sipariş durumu, sipariş listesi ve bakiye.

> Bu paket topluluk tarafından yazılmıştır; Turkpin'in resmi paketi değildir. API'nin güncel ve bağlayıcı tanımı için [dev.turkpin.com](https://dev.turkpin.com) dokümanına bakın.

Diğer diller / Other languages: [PHP](https://github.com/buluterol/turkpin-php) · [Node.js](https://github.com/buluterol/turkpin-node) · [Python](https://github.com/buluterol/turkpin-python) · [Go](https://github.com/buluterol/turkpin-go) · [Java](https://github.com/buluterol/turkpin-java) · [.NET](https://github.com/buluterol/turkpin-dotnet) · [Ruby](https://github.com/buluterol/turkpin-ruby)

## Gereksinimler

Python 3.8+, yalnız standart kütüphane

## Kurulum

```sh
pip install git+https://github.com/buluterol/turkpin-python
```

Paket PyPI'da yayınlı değil; GitHub'dan kurulur.

## Kullanım

```python
import os
from turkpin import TurkpinClient, TurkpinError, OrderStatus

tp = TurkpinClient(os.environ["TURKPIN_USER"], os.environ["TURKPIN_PASS"], test=True)

games = tp.get_games()
products = tp.get_products(games[0].id)

try:
    order = tp.create_order(games[0].id, products[0].id, quantity=1)
    if order.pending:
        info = tp.get_order_status(order.order_no)  # info.status == OrderStatus.COMPLETED olunca kodlar gelir
    for epin in order.epins:
        print(epin.code)
except TurkpinError as e:
    print(f"Hata {e.code}: {e}")

print(tp.get_balance().balance)  # Decimal
```

## Ortam değişkenleri

```python
tp = TurkpinClient.from_env()  # TURKPIN_USERNAME, TURKPIN_PASSWORD, TURKPIN_TEST, TURKPIN_TIMEOUT
```

## Django

`settings.py`:

```python
TURKPIN = {
    "USERNAME": os.environ["TURKPIN_USERNAME"],
    "PASSWORD": os.environ["TURKPIN_PASSWORD"],
    "TEST": False,
    "TIMEOUT": 30,
}
```

```python
from turkpin.contrib.django import get_client

def games(request):
    return JsonResponse({"games": [g.name for g in get_client().get_games()]})
```

## Flask

```python
from turkpin.contrib.flask import Turkpin

app.config.update(TURKPIN_USERNAME="...", TURKPIN_PASSWORD="...", TURKPIN_TEST=True)
turkpin = Turkpin(app)

@app.get("/balance")
def balance():
    return {"balance": str(turkpin.client.get_balance().balance)}
```

## FastAPI

İstemci senkron çalışır; `async def` yerine düz `def` uç kullanın (FastAPI bunları iş parçacığı havuzunda çalıştırır). Ayarlar ortam değişkenlerinden okunur.

```python
from fastapi import Depends
from turkpin import TurkpinClient
from turkpin.contrib.fastapi import get_turkpin

@app.get("/balance")
def balance(turkpin: TurkpinClient = Depends(get_turkpin)):
    return {"balance": str(turkpin.get_balance().balance)}
```

## Desteklenen komutlar

| API komutu | Açıklama |
|---|---|
| `epinOyunListesi` | Oyun listesi |
| `epinUrunleri` | Bir oyunun e-pin ürünleri (stok, fiyat, min/max adet, ön sipariş, barem) |
| `epinSiparisYarat` | Sipariş verme (karakter adı, ön sipariş ve barem tutarı isteğe bağlı) |
| `siparisDurumu` | Sipariş durumu ve teslim edilen kodlar |
| `siparisListesi` | İki tarih arasındaki siparişler (en çok 30 gün) |
| `balance` | Bakiye, kredi, bonus ve harcama |

Listede olmayan komutlar için istemcideki genel `call` metodu kullanılabilir.

**Sipariş durumları (`SIPARIS_DURUMU`):** 1 işleniyor, 2 tamamlandı, 3 iptal, 99 teslimatta, 199 ön sipariş teslimatta. `DURUM_KODU` 999 ise Turkpin siparişle ilgili bir sorunu inceliyor demektir; iptal sebebi ya da not `EKSTRA` alanında gelir.

**Ön sipariş ve barem:** Ürünün `pre_order` alanı `true` ise sipariş ön sipariş olarak verilmelidir. Barem tutarlı ürünlerde tutar `min_barem` ile `max_barem` arasında, `barem_step` adımlarıyla seçilir. Bu siparişlerin sonucu `Pending` döner; kodlar için sipariş durumunu sorgulayın.

**Hatalar:** API `000` dışında bir hata kodu döndürdüğünde istemci, kodu ve açıklamayı taşıyan bir hata fırlatır. HTTP ya da XML hatalarında kod boştur.

## Test ortamı

- Test: `https://www.turkpin.net/api.php`, canlı: `https://www.turkpin.com/api.php`.
- Test ortamına erişmek için sunucu IP adresinizin Turkpin'e tanıtılması gerekir; tanıtılmamış IP'den gelen isteklere API `002` hata koduyla cevap verir. Test hesabı ve IP tanımı için [dev.turkpin.com](https://dev.turkpin.com) adresindeki iletişim bilgilerini kullanın.
- Kullanıcı adı ve şifreyi koda yazmayın; ortam değişkeni ya da gizli anahtar deposundan okuyun.

## Geliştirme

Testler gerçek API'ye bağlanmaz; örnek XML cevaplarıyla çalışır.

```sh
pip install django flask fastapi httpx  # isteğe bağlı: entegrasyon testleri
python -m unittest discover -s tests -t .
```

## English

Python client for the Turkpin dealer API with Django, Flask and FastAPI integration (e-pin games, products, orders, order status, order history, balance). Community-maintained, not an official Turkpin package; see [dev.turkpin.com](https://dev.turkpin.com) for the authoritative API reference. The sandbox (`turkpin.net`) only accepts requests from server IP addresses registered with Turkpin (otherwise error `002`). Install and usage are shown above; method names are in English, while API command and field names follow the original Turkish API.

## Lisans

MIT
