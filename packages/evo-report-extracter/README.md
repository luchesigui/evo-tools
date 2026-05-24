# evo-report-extracter

Este pacote automatiza o login na plataforma Evo5, a navegação para diferentes tipos de relatórios, a aplicação de filtros temporais e a exportação do relatório resultante em planilha Excel.

## Estrutura do Pacote

O código é organizado em subpastas por tipo de relatório sob o diretório `reports/`:
* `reports/conversion/`: Relatório de Oportunidades (Conversão).

## Pré-requisitos

O pacote depende do `evo-playwright` para todas as ações e automações de navegador.

## Configuração

Configure as variáveis de ambiente em um arquivo `.env` (copiado da raiz ou definido localmente):
* `EVO_USER`: O nome de usuário para login no Evo5.
* `EVO_PASS`: A senha para login no Evo5.
* `HEADLESS`: `true` (padrão) ou `false` para visualizar a automação abrindo o navegador.
* `DEBUG`: `true` para salvar capturas de tela durante as transições de página e exibir logs verbosos.

## Comandos e Execução

Para rodar a extração, você deve passar o parâmetro indicando qual relatório deseja extrair (ex: `conversion`):

```bash
npx nx start evo-report-extracter --args="conversion"
```

Ou diretamente via Node se estiver no diretório do pacote:
```bash
node index.js conversion
```

Se o tipo de relatório não for fornecido ou for inválido, o comando listará os relatórios disponíveis.

### Testes

Para rodar os testes unitários do extrator:
```bash
npx nx test evo-report-extracter
```
