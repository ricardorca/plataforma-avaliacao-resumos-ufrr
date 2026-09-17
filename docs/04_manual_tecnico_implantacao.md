# 4. Manual técnico de implantação

## Objetivo

Orientar a responsável pela implantação na implantação, operação, atualização, backup e publicação da plataforma em ambiente Linux com Docker.

## Arquitetura de execução

A arquitetura prevista para produção é:

```text
Internet
   │
 HTTPS :443
   ▼
Nginx / reverse proxy
   │
 127.0.0.1:8501
   ▼
Docker container
   │
   ├── Streamlit / Python
   ├── /app/data
   ├── /app/resumos
   ├── /app/backups
   └── /app/assets/assinaturas
```

A porta 8501 não deve ser publicada diretamente para a Internet.

## Componentes entregues

- `app.py` - aplicação principal;
- `requirements.txt` - dependências Python;
- `Dockerfile` - construção da imagem;
- `docker-compose.yml` - execução do container;
- `assets/` - recursos visuais e modelos de certificado;
- `data/`, `resumos/`, `backups/` e `assets/assinaturas/` - armazenamento persistente;
- documentação técnica e manuais.

## Requisito do host

O host deve ser Linux compatível com Docker. Para Oracle Cloud Always Free, o pacote foi preparado para uso em VM ARM64/AArch64, como a família Ampere A1.

O host precisa ter, no mínimo:

- Docker Engine;
- Docker Compose Plugin;
- acesso à Internet para baixar a imagem base e instalar dependências durante o build;
- armazenamento persistente suficiente para banco, PDFs, backups e assinaturas;
- Nginx ou outro reverse proxy para HTTPS, quando houver publicação externa.

**Não é necessário instalar Python, Streamlit ou as bibliotecas do `requirements.txt` diretamente no host para a implantação Docker.**

## Instalação

Na pasta do projeto:

```bash
docker compose build --pull
docker compose up -d
docker compose ps
docker compose logs --tail=100 avaliacao-ufrr
```

Teste local na VM:

```bash
curl -I http://127.0.0.1:8501
```

## Banco e arquivos

A aplicação utiliza SQLite em:

```text
data/avaliacao.db
```

Os PDFs ficam em:

```text
resumos/
```

As assinaturas ficam em:

```text
assets/assinaturas/
```

Esses diretórios são montados como volumes bind no Docker Compose e devem permanecer no host durante atualizações ou recriação do container.

## Autenticação

A versão entregue utiliza autenticação local da aplicação. Não há SSO institucional implementado no pacote.

O responsável pela implantação deve definir, conforme a política institucional, se será mantida a autenticação local ou se será desenvolvida posteriormente uma integração com SSO/MFA.

## Atualização

Antes de atualizar:

1. fazer backup do banco e dos arquivos persistentes;
2. preservar `data/`, `resumos/`, `backups/` e `assets/assinaturas/`;
3. substituir os arquivos da aplicação;
4. reconstruir a imagem;
5. iniciar novamente o serviço.

Comandos:

```bash
docker compose build --pull
docker compose up -d
```

## Logs e operação

```bash
docker compose ps
docker compose logs -f avaliacao-ufrr
docker compose restart avaliacao-ufrr
docker compose stop
docker compose start
docker compose down
```

Não remover volumes ou diretórios persistentes sem confirmar previamente a existência de backup.

## Homologação mínima

Antes da publicação, testar:

1. login válido e inválido;
2. troca obrigatória de senha;
3. logout;
4. separação entre master, coordenação e avaliador;
5. isolamento dos trabalhos atribuídos aos avaliadores;
6. cadastro e importação de trabalhos;
7. upload e abertura dos PDFs;
8. avaliações, comentários e discrepâncias;
9. resultados, relatórios e certificados;
10. backup e restauração;
11. HTTPS;
12. acesso externo;
13. reinicialização da VM e recuperação automática do container.

## Segurança

A aplicação possui controles no nível da aplicação. O pacote Docker também utiliza execução com usuário não-root, `no-new-privileges` e remoção de capabilities.

Isso não substitui:

- segurança da OCI;
- atualização do Ubuntu;
- firewall/NSG/Security List;
- SSH restrito;
- HTTPS;
- gestão de credenciais;
- backups externos;
- monitoramento;
- avaliação de segurança institucional;
- pentest, quando exigido.
