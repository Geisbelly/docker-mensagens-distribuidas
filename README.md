# Mensagens Distribuídas com Docker

Aplicação REST desenvolvida em Python com Flask, executada em três containers Docker. As instâncias compartilham um volume nomeado para armazenamento, mantendo arquivos JSON e logs individuais. Tentei seguir de forma bem literal ao que foi pedido, sem adicionar nada além (sem banco de dados, sem outro container além dos 3, sem outras rotas ...)


## Tecnologias

* Python
* Flask
* Requests
* Docker
* Docker Compose

## Estrutura do projeto

```text
docker-mensagens-distribuidas/
├── app/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── testar.sh
└── README.md
```

## Endpoints

| Método | Rota        | Descrição                                             |
| ------ | ----------- | ----------------------------------------------------- |
| POST   | `/send`     | Recebe e replica mensagens para as outras instâncias. |
| GET    | `/messages` | Retorna as mensagens armazenadas na instância.        |

## Containers

| Container | Porta |
| --------- | ----- |
| app1      | 5001  |
| app2      | 5002  |
| app3      | 5003  |

Cada container possui seus próprios arquivos no volume `mensagens_data`:

* `app1.json` e `app1.log`
* `app2.json` e `app2.log`
* `app3.json` e `app3.log`

## Execução

Iniciar os containers:

```bash
docker compose up --build -d
```

Verificar os containers:

```bash
docker compose ps
```

## Testes

Executar o script:

```bash
bash testar.sh
```

Enviar uma mensagem:

```bash
curl -X POST http://localhost:5001/send \
-H "Content-Type: application/json" \
-d '{"message":"Teste de mensagem"}'
```

Consultar as mensagens:

```bash
curl http://localhost:5001/messages
curl http://localhost:5002/messages
curl http://localhost:5003/messages
```

## Encerramento

Parar os containers sem excluir os dados:

```bash
docker compose down
```

Remover os containers e o volume:

```bash
docker compose down -v
```