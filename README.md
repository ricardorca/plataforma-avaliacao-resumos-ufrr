# Plataforma de Avaliação de Resumos Científicos - UFRR

Plataforma web independente para apoiar a avaliação, distribuição, consolidação e documentação de resumos científicos em eventos acadêmicos.

> **Aviso:** este repositório disponibiliza o código-fonte para análise e execução. Não contém dados reais de autores, avaliadores, avaliações, trabalhos submetidos ou backups operacionais.
>
> Esta não é uma página oficial nem é gerenciada pela UFRR. O conteúdo é de responsabilidade de seus idealizadores.

## Funcionalidades

- autenticação local e perfis de acesso;
- gestão de avaliadores;
- cadastro e importação de trabalhos;
- associação de PDFs aos trabalhos;
- distribuição de trabalhos para avaliadores;
- avaliações independentes;
- identificação de discrepâncias;
- terceiro avaliador;
- consolidação e classificação por área;
- relatórios e exportação;
- geração de certificados;
- auditoria administrativa;
- backup e restauração;
- reinicialização de ciclo protegida por conta master.

## Critérios de avaliação

| Critério | Peso |
|---|---:|
| Relevância do tema | 20% |
| Clareza e adequação dos objetivos | 15% |
| Adequação e clareza da metodologia | 20% |
| Relevância dos resultados alcançados | 30% |
| Uso da norma culta e adequação ao template | 15% |

As notas variam de 0,0 a 10,0, em incrementos de 0,1.

## Tecnologias

- Python 3.12
- Streamlit
- SQLite
- pandas
- openpyxl
- Pillow
- pypdf
- ReportLab
- Docker / Docker Compose

## Executar localmente com Docker

### 1. Pré-requisito

Instale o Docker Desktop no Windows/macOS ou Docker Engine + Docker Compose em Linux.

### 2. Configuração local

Copie `.env.example` para `.env` e defina uma senha local de teste para `MASTER_INITIAL_PASSWORD`.

No PowerShell:

```powershell
Copy-Item .env.example .env
```

Edite `.env` e troque a senha de exemplo.

**O arquivo `.env` não deve ser enviado ao GitHub.**

### 3. Construir e executar

Na raiz do projeto:

```bash
docker compose up --build
```

Abra no navegador:

```text
http://localhost:8501
```

Para executar em segundo plano:

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

## Persistência local

Os dados criados durante a execução ficam fora do container:

```text
data/                 banco SQLite
resumos/              PDFs dos trabalhos
backups/              backups
assets/assinaturas/   assinaturas adicionadas pelo usuário
```

Esses diretórios são ignorados pelo Git, exceto pelos arquivos `.gitkeep` usados para preservar a estrutura.

## Arquitetura Docker

```text
Navegador
   │
   ▼
localhost:8501
   │
   ▼
Docker Compose
   │
   ▼
Container Streamlit
   ├── SQLite
   ├── PDFs
   └── arquivos persistentes
```

Para uma implantação pública, recomenda-se colocar um reverse proxy com HTTPS na frente do Streamlit e não expor diretamente a porta 8501 à Internet.

## Estrutura do repositório

```text
.
├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── SECURITY.md
├── assets/
├── data/
├── resumos/
├── backups/
└── docs/
```

## Documentação

- `docs/01_visao_geral.md` - visão geral e fluxo da plataforma;
- `docs/02_manual_coordenacao.md` - recursos da coordenação;
- `docs/03_manual_avaliador.md` - recursos do avaliador;
- `docs/04_manual_tecnico_implantacao.md` - implantação e operação técnica;
- `docs/05_requisitos_para_implantacao.md` - requisitos de infraestrutura;
- `docs/06_checklist_entrega.md` - checklist de implantação;
- `docs/07_funcionalidades_v29.md` - funcionalidades da versão;
- `docs/BACKUP_RESTAURACAO_DOCKER.md` - backup e restauração;
- `docs/SEGURANCA_IMPLANTACAO.md` - controles e responsabilidades de segurança.

## Domínio e DNS

O código não fixa domínio, endereço IP ou hostname de produção. Em uma implantação pública, o domínio/subdomínio deve ser definido pelo responsável pelo domínio e configurado externamente, por DNS e reverse proxy/HTTPS.

## Segurança

Consulte `SECURITY.md` e `docs/SEGURANCA_IMPLANTACAO.md`.

O código utiliza autenticação local, controle de acesso por perfil, hashing PBKDF2-HMAC-SHA256 para novas senhas, consultas parametrizadas, auditoria administrativa e controles adicionais no container. Esses mecanismos não equivalem a uma auditoria de segurança, pentest ou homologação institucional.

## Dados e privacidade

Este repositório é preparado para código e documentação. Dados reais de eventos devem permanecer fora do Git e de repositórios públicos.

## Licença

Nenhuma licença de código aberto é declarada neste repositório neste momento. A publicação pública do código não deve ser interpretada automaticamente como autorização para reutilização, redistribuição ou incorporação em outros projetos.

## Contribuições

Sugestões, correções e análises podem ser apresentadas por meio de issues ou pull requests, conforme as regras definidas pelo responsável pelo repositório.
