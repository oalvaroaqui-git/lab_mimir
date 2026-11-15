# lab_mimir

Laboratório local de observabilidade com Prometheus, Grafana Mimir e Grafana.

## Arquitetura

```
Prometheus --remote_write--> Mimir --datasource--> Grafana
```

- **Prometheus**: coleta métricas (scrape de si mesmo e do Mimir) e as envia via `remote_write` para o Mimir.
- **Mimir**: armazena as métricas de longo prazo, em modo single-binary com storage em filesystem local.
- **Grafana**: consulta o Mimir (compatível com a API do Prometheus) como datasource já provisionado.

## Estrutura

```
docker-compose.yml
mimir/mimir.yaml                           # config do Mimir (single-binary, filesystem)
prometheus/prometheus.yml                  # scrape configs + remote_write para o Mimir
grafana/provisioning/datasources/mimir.yaml # datasource do Grafana apontando pro Mimir
```

## Como usar

Subir o ambiente:

```bash
docker compose up -d
```

Serviços expostos:

| Serviço    | URL                     |
|------------|-------------------------|
| Grafana    | http://localhost:3000   |
| Prometheus | http://localhost:9090   |
| Mimir      | http://localhost:9009   |

O Grafana está configurado com login anônimo habilitado (role Admin), sem necessidade de autenticação.

Para derrubar o ambiente:

```bash
docker compose down
```

Para remover também os dados persistidos pelo Mimir:

```bash
docker compose down -v
```
