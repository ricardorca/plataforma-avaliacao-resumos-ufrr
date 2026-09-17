# Execução rápida com Docker

Na raiz do projeto, crie o arquivo `.env` a partir de `.env.example` e defina uma senha local para a conta master.

```bash
docker compose up --build
```

Acesse:

```text
http://localhost:8501
```

Para execução em segundo plano:

```bash
docker compose up --build -d
```

Para acompanhar os logs:

```bash
docker compose logs -f avaliacao-ufrr
```

Para parar:

```bash
docker compose down
```

Os dados persistentes ficam em `data/`, `resumos/`, `backups/` e `assets/assinaturas/`. Esses diretórios são ignorados pelo Git para evitar publicação de dados operacionais.
