"""Métricas para o Prometheus: NÚMEROS sobre a API, expostos em /metrics.

O Prometheus visita /metrics a cada 15s e guarda os valores ao longo do tempo.
Com isso, o Grafana desenha gráficos: pedidos por segundo, erros, tempo de resposta.
"""
from prometheus_client import Counter, Histogram

# Contador: só sobe. "Quantos pedidos já recebi", separado por método, rota e status
PEDIDOS = Counter(
    "http_requests_total",
    "Total de pedidos HTTP recebidos pela API",
    ["metodo", "rota", "status"],
)

# Histograma: distribui os tempos em "faixas" (até 5ms, até 10ms, ...).
# Serve para calcular, por exemplo, "95% dos pedidos levam menos de X ms" (p95)
DURACAO = Histogram(
    "http_request_duration_seconds",
    "Tempo para responder cada pedido",
    ["metodo", "rota"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5),
)

# Métrica de NEGÓCIO: quantos pets foram cadastrados, atualizados e excluídos
OPERACOES_PETS = Counter(
    "pets_operacoes_total",
    "Operações feitas no cadastro de pets",
    ["operacao"],
)
