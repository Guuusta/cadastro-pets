"""Logs ORGANIZADOS: uma linha JSON por evento, sempre com horário e request_id.

Por que JSON? Ferramentas (jq, Loki, Grafana) conseguem filtrar por campo:
"me mostre só status=500" ou "tudo do request_id=abc123".
"""
import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

# Guarda o "número de protocolo" do pedido EM ANDAMENTO.
# Assim, QUALQUER log escrito durante aquele pedido (ex.: "pet cadastrado") leva o mesmo request_id
request_id_atual: ContextVar[str | None] = ContextVar("request_id_atual", default=None)


class FormatoJson(logging.Formatter):
    """Transforma cada log numa linha JSON."""

    def format(self, record: logging.LogRecord) -> str:
        dados = {
            "hora": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds"),
            "nivel": record.levelname,          # INFO, WARNING, ERROR
            "servico": "api",
            "mensagem": record.getMessage(),
        }
        if request_id_atual.get():
            dados["request_id"] = request_id_atual.get()
        # Campos extras (request_id, metodo, status...) passados com logger.info(..., extra={"campos": {...}})
        dados.update(getattr(record, "campos", {}))
        if record.exc_info:
            dados["erro"] = self.formatException(record.exc_info)
        return json.dumps(dados, ensure_ascii=False)


def configurar_logs() -> logging.Logger:
    """Todos os logs vão para a SAÍDA PADRÃO (stdout), em JSON.

    Em container, o certo é escrever no stdout: o Docker recolhe e guarda
    (é o que aparece no "docker compose logs"). Nada de arquivo de log dentro do container.
    """
    saida = logging.StreamHandler(sys.stdout)
    saida.setFormatter(FormatoJson())
    raiz = logging.getLogger()
    raiz.handlers = [saida]
    raiz.setLevel(logging.INFO)
    # O log de acesso do uvicorn fica desligado: nós registramos cada pedido do nosso jeito (abaixo)
    logging.getLogger("uvicorn.access").disabled = True
    for nome in ("uvicorn", "uvicorn.error"):
        logging.getLogger(nome).handlers = []
        logging.getLogger(nome).propagate = True
    return logging.getLogger("api")
