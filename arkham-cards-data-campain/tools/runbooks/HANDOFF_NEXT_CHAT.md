# Handoff para continuidade (chat seguinte)

## Objetivo

Continuar tradução/revisão/padronização de arquivos `.po` de Arkham Horror LCG para PT-BR, usando o guia oficial PT-BR como fonte final de verdade.

## Estrutura atual (oficial)

- Traduções: `arkham-cards-data-campain/i18n/pt/...`
- Guias (PDF + auxiliares): `arkham-cards-data-campain/guides/<sigla>/`
- Scripts e referências: `arkham-cards-data-campain/tools/`

## Regras principais

1. `msgstr` deve seguir o guia PT-BR.
2. Se houver conflito entre `.llm.txt`, `.raw.txt` e PDF, o PDF prevalece.
3. Preservar tags técnicas:
   - ícones do app (`[skull]`, `[cultist]`, `[auto_fail]`, `[per_investigator]`, etc.)
   - traits `[[...]]` em inglês
   - tags HTML e placeholders técnicos
4. Não usar `<<ICON_UNKNOWN:...>>` como texto final.
5. Informar explicitamente qualquer expressão usada fora do guia.

## Fluxo recomendado

1. Trabalhar no alvo em `arkham-cards-data-campain/i18n/pt/campaigns/<sigla>/<arquivo>.po`.
2. Se pedido, limpar `msgstr` (exceto cabeçalho) e garantir UTF-8 sem BOM.
3. Conferir auxiliares em `arkham-cards-data-campain/guides/<sigla>/`.
4. Se faltarem auxiliares, gerar com:
   - `python arkham-cards-data-campain/tools/extract_pdf_text.py --input-dir "arkham-cards-data-campain/guides/<sigla>"`
5. Revisar/corrigir o `.po` comparando com o guia oficial PT-BR.

## Formato de saída esperado

- Resumo curto do que foi revisado.
- Lista de divergências corrigidas.
- Lista de expressões fora do guia (se houver).
- Observações de OCR/ambiguidade/símbolos (se houver).
- Informar se ficou 100% igual ao guia.
- Informar tempo gasto e estimativa de tokens quando solicitado.

## Observações úteis

- Em Windows, mojibake no terminal não garante arquivo quebrado; valide o encoding do arquivo.
- O `extract_pdf_text.py` gera, por PDF:
  - `.raw.txt`
  - `.llm.txt`
  - `.search.txt`
  - `.map.json`
  - `.txt` (alias do `.llm.txt`)

