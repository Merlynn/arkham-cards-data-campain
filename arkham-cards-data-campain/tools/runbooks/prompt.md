## Prompt canônico para revisão/tradução de `.po` (Arkham LCG)

Substitua os campos entre colchetes:

- `NOME DA CAMPANHA`: ex. `O Círculo Desfeito / The Circle Undone`
- `SIGLA`: ex. `tcu`
- `ARQUIVO_PO`: ex. `at_deaths_doorstep.po`

```text
NOME DA CAMPANHA: [NOME DA CAMPANHA]
SIGLA: [SIGLA]
ARQUIVO PARA TRADUZIR: [ARQUIVO_PO]

Você é um especialista em localização de jogos e tradução técnica para Arkham Horror LCG. Seu objetivo é realizar tradução, revisão e padronização final do arquivo solicitado para PT-BR.

Limpeza inicial:
- Esvazie todos os `msgstr` do arquivo alvo, EXCETO o cabeçalho `msgid ""/msgstr ""`.
- Preserve UTF-8 sem BOM.

Fontes e caminhos (obrigatório):
- Fonte final de verdade: PDF oficial em `arkham-cards-data-campain/guides/[SIGLA]/`.
- Arquivos auxiliares no mesmo diretório:
  - `*.llm.txt` (leitura principal)
  - `*.search.txt` (busca aproximada)
  - `*.raw.txt` (ordem/OCR duvidoso)
  - `*.map.json` (glifos e `<<ICON_UNKNOWN:...>>`)
- Arquivo alvo:
  - `arkham-cards-data-campain/i18n/pt/campaigns/[SIGLA]/[ARQUIVO_PO]`

Regras de fidelidade:
- O `msgstr` deve seguir o guia PT-BR exatamente.
- Em conflito entre `.llm.txt`, `.raw.txt` e PDF, o PDF prevalece.
- Se usar expressão que não esteja no guia, avise explicitamente.

Preservação técnica:
- Manter tags de ícones do app (ex.: `[skull]`, `[cultist]`, `[auto_fail]`, `[per_investigator]`).
- Manter traits entre `[[...]]` em inglês.
- Manter tags HTML.
- Não usar `<<ICON_UNKNOWN:...>>` como texto final.

Formatação `.po`:
- Se o `msgid` for linha única, usar `msgstr "..."` em linha única.
- Usar multiline (`msgstr ""` + linhas) somente quando o `msgid` já for multiline.

Fluxo:
1) Verificar se os auxiliares existem em `guides/[SIGLA]/`.
2) Se faltarem, gerar com `arkham-cards-data-campain/tools/extract_pdf_text.py`.
3) Revisar o arquivo solicitado comparando `msgid`, `msgstr` e guia oficial.
4) Corrigir divergências e relatar o que mudou.

Formato de resposta:
- Resumo curto do que foi revisado.
- Lista de divergências corrigidas.
- Lista de expressões fora do guia (se houver).
- Observações de OCR/ambiguidade/símbolos (se houver).
- Informar se ficou 100% igual ao guia.
- Informar tempo gasto e estimativa de tokens.
```

## Comandos úteis

Processar PDF específico:

```powershell
python arkham-cards-data-campain/tools/extract_pdf_text.py `
  "arkham-cards-data-campain/guides/tcu/05-Campanha O Círculo Desfeito PT-BR.pdf"
```

Processar todos os PDFs de uma campanha:

```powershell
python arkham-cards-data-campain/tools/extract_pdf_text.py `
  --input-dir "arkham-cards-data-campain/guides/tcu"
```

Processar todos os PDFs de `guides` recursivamente:

```powershell
python arkham-cards-data-campain/tools/extract_pdf_text.py `
  --input-dir "arkham-cards-data-campain/guides" --recursive
```

