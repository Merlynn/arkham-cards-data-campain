preciso traduzor uma serie de arquivos .po referente as campanhas de Arkham Horror LCG

para isso vamos usar os guias das campanhas. 

preciso que a tradução corresponda a oficial (feita pela galapagos)

para isso pensei no seguinte fluxo:
- pegar as entradas msgid (em ingles) procurar por elas no guia em ingles]
- procurar o termo correspondente no guia em pt-br e depois atualizar o msgstr

pensei num script (extract_pdf_text.py) para extrair textos dos guias (pdf) para ficar mais leve o processamento, mas se tiver uma alternativa melhor pode sugerir

para cada campanha vou criar uma pasta em tmp, assim arquivos gerados durante o processo ficam na pasta de referencia da campanha, para manter a organização

o processo ja foi feito para 3 campanhas (notz, dwl e ptc).

comecei tambem a escrever um readme para documentar, mas esta desatualizado

os arquivos das campanhas (.po) estão em arkham-cards-data-campain\i18n\pt\campaigns

algumas coisas não podem ser alteradas como #TEXT# e [TEXT] que são tags usadas no app, esse texto deve ficar como está.
tags html também devem ser preservadas
Nomes Próprios: Siga o guia. Se o guia traduz um local (ex: "Graveyard" -> "Cemitério"), use a tradução. Se o guia mantém em inglês (ex: "Downtown"), mantenha em inglês.
Redundância: Evite colocar o nome em inglês entre parênteses se o guia oficial não o faz. O objetivo é espelhar o guia oficial.
Termos Proibidos: Se encontrar termos como "Este livro" me avise, pois o texto vai estar num app, ai vou analisar qual seria a melhor opçao.

poderia me ajudar nesse processo? depois de definir como será o processo, vou pegar os outros arquivos de campanha para continuar.

rpecisa de mais alguma informação?


notz, dwl, ptc, tfa, tcu, tdea, eoe, tskc, fhv, tdc

the Harbinger 

Translation Team:
André(andre_luis_monteiro1998@hotmail.com)
Chico (viniciuschiconato@hotmail.com)
Felipe (felipe.roc@hotmail.com)
Flash (jbmreis@gmail.com)
Henrique (henricosta@gmail.com)
Kröger (denerfilho@gmail.com)
Machado (eulermachado225@gmail.com)
Márcio Luis (mluiss.oliveira@gmail.com)
Meguer (meguer@gmail.com)
Mezzavilla (guga.medeiros@gmail.com)
Otávio Rocha (otavio.r.valente94@gmail.com)
Rafael P (rafaelfor8@gmail.com)