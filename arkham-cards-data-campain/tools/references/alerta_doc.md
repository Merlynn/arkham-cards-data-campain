Do jeito que o bot está configurado, ele sobe uma API REST local embutida (graças ao FastAPI e Uvicorn) que roda na porta 8000.

Qualquer outra aplicação (ou até mesmo comandos de terminal, como o curl) só precisa fazer uma requisição HTTP do tipo POST para a rota /enviar-alerta contendo um JSON com o ID do usuário (ou grupo) e a mensagem.

A Estrutura da Requisição
URL: http://localhost:8000/enviar-alerta
Método: POST
Content-Type: application/json
Corpo (Payload):
json
{
  "chat_id": 956618839,
  "texto": "⚠️ Alerta! Ocorreu uma instabilidade no servidor X."
}
Exemplos na Prática
Se a sua outra aplicação for um script no terminal (via curl):

bash
curl -X POST "http://localhost:8000/enviar-alerta" \
     -H "Content-Type: application/json" \
     -d "{\"chat_id\": 956618839, \"texto\": \"⚠️ Processo finalizado com sucesso!\"}"
Se a sua outra aplicação for escrita em Python (usando a biblioteca requests):

python
import requests
url = "http://localhost:8000/enviar-alerta"
payload = {
    "chat_id": 956618839,
    "texto": "Olá! Vim de outra aplicação."
}
resposta = requests.post(url, json=payload)
print(resposta.json())
Se for escrita em JavaScript/Node.js (usando fetch):

javascript
fetch('http://localhost:8000/enviar-alerta', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    chat_id: 956618839,
    texto: "Aviso do sistema em Node!"
  })
})
Para Ver a Documentação Interativa
Se quiser testar manualmente sem precisar escrever código ou montar o JSON, com o bot ligado você pode acessar no seu navegador:

👉 http://localhost:8000/docs

Lá vai abrir uma interface gerada magicamente pelo FastAPI (Swagger UI) onde você pode clicar na rota /enviar-alerta, depois em "Try it out", preencher os valores ali na tela e clicar em "Execute" para enviar.