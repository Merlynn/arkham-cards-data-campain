# Guia de traducao por PDFs oficiais

Este repositorio contem fluxo e utilitarios para traducao/revisao de arquivos `.po` de Arkham Horror LCG para PT-BR, usando os guias oficiais como fonte final de verdade.

## Estrutura do projeto

```text
arkham-cards-data-campain/
  guides/                     # PDFs e artefatos extraidos (ignorado no git, exceto .gitkeep)
  i18n/pt/campaigns/<sigla>/  # arquivos .po alvo
  tools/
    campaigns.json            # mapeamento sigla -> metadados de campanha
    extract_pdf_text.py       # extrai .raw/.llm/.search/.map/.txt de PDFs
    validate_po.py            # validacao automatica de .po
    runbooks/                 # prompts e handoffs operacionais
    references/               # material de apoio/historico
```

## Fonte de verdade

1. O PDF oficial PT-BR em `guides/<sigla>/` e a fonte final.
2. Arquivos auxiliares (`.llm.txt`, `.search.txt`, `.raw.txt`, `.map.json`) ajudam, mas nao superam o PDF.
3. Em conflito entre auxiliar e PDF, siga o PDF.

## Extracao de texto dos guias

Script: `tools/extract_pdf_text.py`

Processar um PDF:

```powershell
python arkham-cards-data-campain/tools/extract_pdf_text.py `
  "arkham-cards-data-campain/guides/tcu/05-Campanha O Círculo Desfeito PT-BR.pdf"
```

Processar todos os PDFs de uma campanha:

```powershell
python arkham-cards-data-campain/tools/extract_pdf_text.py `
  --input-dir "arkham-cards-data-campain/guides/tcu"
```

Processar todos os PDFs sob `guides/`:

```powershell
python arkham-cards-data-campain/tools/extract_pdf_text.py `
  --input-dir "arkham-cards-data-campain/guides" --recursive
```

Saidas por PDF:

- `.raw.txt`
- `.llm.txt`
- `.search.txt`
- `.map.json`
- `.txt` (alias do `.llm.txt`)

## Mapeamento de campanhas

Arquivo: `tools/campaigns.json`

Finalidade:

- centralizar metadados por sigla (`po_dir`, `guide_dir`, `guide_pdf_globs`);
- padronizar automacoes que precisam localizar `.po` e PDFs oficiais;
- evitar hardcode espalhado nos scripts.

## Validacao automatica de `.po`

Script: `tools/validate_po.py`

Checagens implementadas:

- arquivo em UTF-8;
- ausencia de BOM UTF-8;
- preservacao de tokens tecnicos de `msgid` em `msgstr`:
  - tags do app (`[cultist]`, `[auto_fail]`, etc.);
  - traits (`[[Madness]]`);
  - tags HTML (`<i>`, `<b>`, ...);
  - placeholders tipo `#X#`;
- coerencia de formato entre `msgid` e `msgstr` (single-line vs multiline).

Exemplos:

```powershell
python arkham-cards-data-campain/tools/validate_po.py `
  arkham-cards-data-campain/i18n/pt/campaigns/tcu/at_deaths_doorstep.po
```

```powershell
python arkham-cards-data-campain/tools/validate_po.py `
  arkham-cards-data-campain/i18n/pt/campaigns/tcu --recursive
```

## Fluxo recomendado por arquivo

1. Selecionar alvo em `i18n/pt/campaigns/<sigla>/<arquivo>.po`.
2. Se pedido, limpar `msgstr` (exceto cabecalho) e garantir UTF-8 sem BOM.
3. Garantir auxiliares em `guides/<sigla>/` (gerar com `extract_pdf_text.py` se faltar).
4. Revisar/traduzir com fidelidade ao guia PT-BR.
5. Rodar `validate_po.py` no arquivo alterado.
6. Reportar divergencias, expressoes fora do guia e pontos ambiguos.

## Documentacao operacional

- Prompt canônico: `tools/runbooks/prompt.md`
- Handoff para proximo chat: `tools/runbooks/HANDOFF_NEXT_CHAT.md`
- Referencias historicas: `tools/references/`

## Observacoes

- `guides/` e ignorada no versionamento para evitar subir PDFs e artefatos gerados.
- A estrutura e mantida no repositorio com `guides/.gitkeep`.
- Em Windows, mojibake no terminal nem sempre indica erro no arquivo; valide encoding quando houver duvida.

