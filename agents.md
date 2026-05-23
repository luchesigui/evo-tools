# Instruções para Agentes - EvoTools

Bem-vindo ao repositório **EvoTools**! Este documento fornece o contexto de negócio do ecossistema e as diretrizes arquiteturais para orientar agentes de IA no desenvolvimento deste projeto.

---

## 🏢 Contexto de Negócio: O que é o Evo?

O **Evo (Evo5)** é um sistema integrado completo voltado para a gestão de academias e centros de bem-estar. Ele engloba funcionalidades cruciais para o funcionamento diário de uma academia:
- **Financeiro & Faturamento**: Processamento de mensalidades, vendas de planos e recorrência.
- **Controle de Acesso**: Catracas, registros de presença e controle de quem pode ou não treinar.
- **CRM & Comunicação**: Cadastro de clientes, acompanhamento de oportunidades e canais de relacionamento.

### Por que o EvoTools existe?
O **EvoTools** é um ecossistema de ferramentas desenvolvidas para estender, automatizar e complementar a operação do sistema Evo. Ele atua nas lacunas operacionais onde processos manuais repetitivos podem ser otimizados, tais como:
1. **Comunicação Ativa**: Envio automatizado de mensagens e e-mails para públicos-alvo específicos.
2. **Processamento de Relatórios**: Triagem inteligente de dados brutos exportados do Evo para segmentação de clientes.

### Visão de Futuro do Projeto
Com o tempo, o EvoTools se expandirá para incluir:
- **API Customizada**: Para automatizar a extração direta de relatórios em segundo plano (evitando processos de exportação manuais).
- **Webhooks**: Um servidor para receber notificações de eventos em tempo real do sistema Evo e disparar ações imediatas.
- **Utilitários Auxiliares**: Novas ferramentas de inteligência de dados e integrações extras.

---

## 📦 Propósito dos Pacotes no Negócio

Cada pacote no repositório resolve uma dor de negócio específica:

### 1. `evo-playwright` (Núcleo de Interação)
- **O que faz**: É a biblioteca base de automação web com Playwright.
- **Objetivo de Negócio**: Centralizar o conhecimento técnico de navegação no portal do Evo5. Ele cuida do login e de buscas de clientes de forma genérica para que outros scripts não precisem reimplementar a lógica de scraping.

### 2. `evo-contacter` (Automação de Contatos)
- **O que faz**: Automatiza o envio de e-mails para membros específicos da academia através de seus IDs.
- **Objetivo de Negócio**: Escalar o relacionamento e a retenção com o cliente sem depender de operadores manuais digitando mensagens uma a uma no CRM.

### 3. `evo-frequency-sorter` (Triagem de Frequência)
- **O que faz**: Processa relatórios de frequência de acessos de alunos e divide o arquivo em dois grupos: alunos diretos e agregadores.
- **Objetivo de Negócio**: Permitir comunicações e estratégias de retenção personalizadas para cada perfil de membro com base no tipo de contrato e na sua frequência de treinos.

---

## 🛠️ Regras de Dependência e Desenvolvimento

Ao sugerir ou implementar alterações de código, respeite estas regras:
- **Não Duplicar Lógica de Navegação**: Qualquer nova funcionalidade que precise fazer login ou navegar no painel web do Evo deve estender o `evo-playwright` em vez de criar novas instâncias ou seletores de Playwright no `evo-contacter`.
- **Nx Monorepo**: O repositório utiliza o Nx. Ao testar ou rodar os pacotes, utilize comandos do Nx (`npx nx <target> <project>`) a partir da raiz.
