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

## Validação

### 1. Prometheus coletando métricas

Em http://localhost:9090/targets, os dois jobs (`prometheus` e `mimir`) devem aparecer com estado **UP**:

![Targets do Prometheus](docs/images/prometheus-targets.png)

### 2. Datasource do Mimir provisionado no Grafana

Em http://localhost:3000/connections/datasources, o datasource **Mimir** aparece já provisionado como default, apontando para `http://mimir:9009/prometheus`:

![Datasource Mimir no Grafana](docs/images/grafana-datasource.png)

### 3. Métricas chegando no Mimir via remote_write

No Explore do Grafana, consultando `up` pelo datasource Mimir, as duas séries aparecem com valor `1` — ou seja, as métricas coletadas pelo Prometheus estão sendo gravadas no Mimir e consultadas de lá:

![Consulta up no Explore](docs/images/grafana-explore.png)

Também dá pra validar direto pela API do Mimir:

```bash
curl -s 'http://localhost:9009/prometheus/api/v1/query?query=count(up)'
# {"status":"success","data":{"resultType":"vector","result":[{"metric":{},"value":[...,"2"]}]}}
```
