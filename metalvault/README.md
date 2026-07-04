# MetalVault — Django

Sistema de gestão de acervo de metais preciosos e cédulas, recriado em Python/Django a partir do projeto original em TypeScript/React/Supabase.

## Funcionalidades

- **Autenticação** — Cadastro, login e logout de usuários
- **Dashboard** — Visão geral com estatísticas, gráficos e cotações de mercado ao vivo (ouro, prata, dólar via AwesomeAPI)
- **Inventário de Metais** — CRUD completo com tipo (barra, moeda, medalha), material (ouro, prata, platina), pureza, peso em gramas/oz troy, valor de aquisição, upload de fotos, certificados e notas fiscais
- **Cédulas** — Cadastro de papel-moeda em diversas moedas (USD, EUR, GBP, BRL)
- **Locais de Armazenamento** — Gerenciamento de cofres, bancos e locais
- **Relatório IRPF** — Geração automática de Bens e Direitos para declaração de imposto de renda, com discriminação formatada, exportação CSV e filtros por ano/valor
- **Valorização ao Vivo** — Cálculo do valor atualizado do inventário baseado em cotações de mercado em tempo real

## Instalação

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse em `http://localhost:8000`

## Usuário de teste

- Email: `admin@metalvault.com`
- Senha: `admin123`

## Stack

- Python 3.12+ / Django 5+
- SQLite (desenvolvimento) — troque para PostgreSQL em produção
- Bootstrap 5 + CSS customizado (tema escuro com ouro)
- Chart.js para gráficos
- AwesomeAPI para cotações de mercado
