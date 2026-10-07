# ---------- Imagem da Web do Cadastro de Pets ----------
# Nginx oficial na versão "unprivileged": já roda como usuário comum (não root).
# Versão FIXA (1.30.5 = linha estável do Nginx), para o build não mudar sozinho
FROM nginxinc/nginx-unprivileged:1.30.5-alpine

# Nossa configuração do servidor
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Os arquivos da página (HTML, JS, CSS)
COPY public/ /usr/share/nginx/html/

EXPOSE 8080
# Não precisa de CMD: a imagem do Nginx já sabe como iniciar
