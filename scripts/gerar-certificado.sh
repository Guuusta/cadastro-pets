#!/usr/bin/env bash
# ============================================================
# Gera o certificado HTTPS do meuhost.local para o proxy.
#   - Com mkcert instalado: certificado CONFIÁVEL (cadeado sem aviso)
#   - Sem mkcert: certificado autoassinado com openssl (funciona, mas o navegador avisa)
# Uso:  ./scripts/gerar-certificado.sh
# ============================================================
set -euo pipefail

DOMINIO="meuhost.local"
PASTA="$(dirname "$0")/../proxy/certs"
mkdir -p "$PASTA"

if command -v mkcert >/dev/null 2>&1; then
  echo "mkcert encontrado: gerando certificado confiável para $DOMINIO"
  mkcert -cert-file "$PASTA/cert.pem" -key-file "$PASTA/key.pem" "$DOMINIO" localhost 127.0.0.1
else
  echo "mkcert não encontrado: gerando certificado AUTOASSINADO (o navegador vai mostrar um aviso)"
  openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
    -keyout "$PASTA/key.pem" -out "$PASTA/cert.pem" \
    -subj "/CN=$DOMINIO" -addext "subjectAltName=DNS:$DOMINIO,DNS:localhost,IP:127.0.0.1"
fi

# A chave privada é um SEGREDO: só o dono lê (600). O certificado é público (644).
# (o Nginx lê os dois como root, então funciona; e a pasta fica fora do Git)
chmod 644 "$PASTA/cert.pem"
chmod 600 "$PASTA/key.pem"
echo "Pronto: $PASTA/cert.pem e $PASTA/key.pem"
