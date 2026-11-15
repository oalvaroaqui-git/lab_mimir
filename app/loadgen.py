import os
import random
import time

import httpx

APP_URL = os.environ.get("APP_URL", "http://localhost:8000")


def main() -> None:
    client = httpx.Client(base_url=APP_URL, timeout=5)
    print(f"gerando carga contra {APP_URL}")
    while True:
        try:
            roll = random.random()
            if roll < 0.50:
                client.get("/products")
            elif roll < 0.85:
                # ids 1-6: o 6 não existe e gera 404s para o dashboard
                client.get(f"/products/{random.randint(1, 6)}")
            else:
                client.post(
                    "/orders",
                    json={
                        "product_id": random.randint(1, 5),
                        "quantity": random.randint(1, 3),
                    },
                )
        except httpx.HTTPError as exc:
            print(f"app indisponível, tentando de novo: {exc}")
            time.sleep(2)
        time.sleep(random.uniform(0.1, 0.5))


if __name__ == "__main__":
    main()
