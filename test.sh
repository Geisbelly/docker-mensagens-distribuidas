
#!/bin/bash

set -e

docker compose up --build -d

sleep 5

MENSAGEM="Teste de replicacao $(date +%s)"

echo "Enviando mensagem pela app1..."

curl -s -X POST http://localhost:5001/send \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"$MENSAGEM\"}"

echo ""
echo ""

for CONTAINER in app1 app2 app3
do
    echo "Verificando $CONTAINER..."

    if docker exec "$CONTAINER" grep -q "$MENSAGEM" "/data/$CONTAINER.json"; then
        echo "Mensagem encontrada em $CONTAINER.json"
    else
        echo "ERRO: mensagem nao encontrada em $CONTAINER.json"
        exit 1
    fi

    if docker exec "$CONTAINER" grep -q "$MENSAGEM" "/data/$CONTAINER.log"; then
        echo "Log encontrado em $CONTAINER.log"
    else
        echo "ERRO: log nao encontrado em $CONTAINER.log"
        exit 1
    fi

    echo ""
done

echo "Verificando GET /messages..."

for PORTA in 5001 5002 5003
do
    echo "Porta $PORTA:"
    curl -s "http://localhost:$PORTA/messages"
    echo ""
done

echo "Todos os testes foram concluidos."