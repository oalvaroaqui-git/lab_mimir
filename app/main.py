import asyncio
import contextlib
import random
import time

from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

REQUESTS = Counter(
    "shop_http_requests_total",
    "Total de requisições HTTP",
    ["method", "endpoint", "status"],
)
LATENCY = Histogram(
    "shop_http_request_duration_seconds",
    "Duração das requisições HTTP",
    ["endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)
ORDERS = Counter("shop_orders_total", "Total de pedidos", ["status"])
ORDER_VALUE = Histogram(
    "shop_order_value_brl",
    "Valor dos pedidos em BRL",
    buckets=(10, 25, 50, 100, 250, 500, 1000, 2500),
)
STOCK = Gauge("shop_products_in_stock", "Unidades em estoque (todos os produtos)")

PRODUCTS = {
    1: {"name": "Teclado mecânico", "price": 349.90},
    2: {"name": "Mouse sem fio", "price": 129.90},
    3: {"name": "Monitor 27\"", "price": 1499.00},
    4: {"name": "Headset USB", "price": 259.90},
    5: {"name": "Webcam Full HD", "price": 199.90},
}
INITIAL_STOCK = 50
stock = {pid: INITIAL_STOCK for pid in PRODUCTS}


def update_stock_gauge() -> None:
    STOCK.set(sum(stock.values()))


async def restock_loop() -> None:
    while True:
        await asyncio.sleep(30)
        for pid in stock:
            stock[pid] = min(INITIAL_STOCK, stock[pid] + random.randint(1, 5))
        update_stock_gauge()


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI):
    update_stock_gauge()
    task = asyncio.create_task(restock_loop())
    yield
    task.cancel()


app = FastAPI(title="Shop App", lifespan=lifespan)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    endpoint = route.path if route else request.url.path
    if endpoint not in ("/metrics", "/health"):
        REQUESTS.labels(request.method, endpoint, str(response.status_code)).inc()
        LATENCY.labels(endpoint).observe(time.perf_counter() - start)
    return response


async def simulate_work(mean: float = 0.08, stddev: float = 0.04) -> None:
    await asyncio.sleep(max(0.001, random.gauss(mean, stddev)))
    if random.random() < 0.05:
        raise HTTPException(status_code=500, detail="erro interno simulado")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/products")
async def list_products():
    await simulate_work(mean=0.05)
    return [
        {"id": pid, **data, "in_stock": stock[pid]} for pid, data in PRODUCTS.items()
    ]


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    await simulate_work(mean=0.03)
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="produto não encontrado")
    return {"id": product_id, **PRODUCTS[product_id], "in_stock": stock[product_id]}


@app.post("/orders", status_code=201)
async def create_order(order: dict):
    await simulate_work(mean=0.15, stddev=0.08)
    product_id = order.get("product_id")
    quantity = int(order.get("quantity", 1))
    if product_id not in PRODUCTS or quantity < 1:
        ORDERS.labels("failed").inc()
        raise HTTPException(status_code=400, detail="pedido inválido")
    if stock[product_id] < quantity:
        ORDERS.labels("failed").inc()
        raise HTTPException(status_code=409, detail="sem estoque")
    stock[product_id] -= quantity
    update_stock_gauge()
    value = PRODUCTS[product_id]["price"] * quantity
    ORDERS.labels("created").inc()
    ORDER_VALUE.observe(value)
    return {"product_id": product_id, "quantity": quantity, "total_brl": round(value, 2)}
