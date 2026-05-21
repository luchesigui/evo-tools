# Instruções do Agente - evo-frequency-sorter

Este pacote Python é responsável por processar e segmentar relatórios de acessos e frequência de membros da academia.

---

## 🎯 Objetivo de Negócio & Lógica de Segmentação

O principal objetivo de negócio deste módulo é separar os dados de acesso em dois grandes grupos para possibilitar **comunicação personalizada de acordo com o tipo de contrato e frequência de treinos**.

### 👥 Alunos Regulares (Diretos)
- **Quem são**: Alunos que possuem um contrato direto com a academia (mensalidades recorrentes, planos anuais, etc.).
- **Motivação de Negócio**: Estes alunos pagam diretamente à academia. Manter a frequência deles alta reduz a taxa de cancelamento (*churn*). A comunicação para este grupo foca em engajamento, metas pessoais e renovação de planos.

### 🏢 Agregadores (Wellhub / Totalpass) e VIPs
- **Quem são**: Clientes corporativos que acessam a academia por meio de plataformas de benefícios como Gympass/Wellhub ou Totalpass, além de membros cortesia (VIP).
- **Motivação de Negócio**: O faturamento destes clientes é baseado em check-ins diários efetivos (repasses dos agregadores). Além disso:
  - Eles possuem dinâmicas de uso e canais de suporte diferentes.
  - A comunicação com eles é desenhada para incentivá-los a continuar realizando o check-in diário no aplicativo do agregador correspondente antes de entrar.
  - Separar estes dados evita enviar mensagens de renovação de plano direto da academia para quem utiliza benefícios corporativos.

---

## 📈 Lógica de Funcionamento e Regras de Negócio

1. **Triagem por Palavra-Chave**:
   - A coluna `CONTRATO` (ou sinônimos normalizados) é verificada para identificar as palavras-chave `WELLHUB`, `TOTALPASS` e `VIP`.
2. **Separação de Arquivos**:
   - **`alunos` (não agregadores)**: Linhas onde o contrato **não** contém nenhuma das palavras-chave acima e não está vazio.
   - **`agregadores`**: Linhas onde o contrato contém `WELLHUB` ou `TOTALPASS`.
3. **Nomenclatura Dinâmica**:
   - Os arquivos de saída utilizam o formato `{ano}-{mês}-{período}-acessos-{tipo}.xlsx`.
   - O `período` indica se o processamento é da primeira quinzena/início do mês (`1-3`) ou do fim do mês (`4-7`), auxiliando nas campanhas de engajamento cíclicas.
