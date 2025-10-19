# Desafio DIO Lambda - Notas Fiscais

Este projeto demonstra como automatizar o processamento de notas fiscais usando AWS Lambda, S3, DynamoDB e API Gateway em ambiente local com Localstack.

## Estrutura

- `lambda/grava_db.py`: Função Lambda que processa uploads do S3 e requisições da API Gateway (POST/GET).
- `lambda/requirements.txt`: Dependências da Lambda.
- `configs/notification_roles.json`: Configuração para o bucket S3 disparar a Lambda.
- `configs/dynamodb_table.json`: Esquema da tabela DynamoDB.
- `configs/apigateway.yaml`: Exemplo de configuração da API Gateway.

## Passos para rodar localmente

### 1. Inicie o Localstack

```bash
docker run -d --name localstack -p 4566:4566 -p 4571:4571 -e SERVICES=ALL -e DEBUG=1 -v /var/run/docker.sock:/var/run/docker.sock localstack/localstack
```

### 2. Configure o AWS CLI

```bash
aws configure
# Use as credenciais:
# AWS Access Key ID: test
# AWS Secret Access Key: test
# Default region name: us-east-1
# Default output format: json
```

### 3. Crie recursos AWS

- **Bucket S3:**
  ```bash
  aws s3api create-bucket --bucket notas-fiscais-upload --endpoint-url=http://localhost:4566
  ```
- **Tabela DynamoDB:**
  ```bash
  aws dynamodb create-table --cli-input-json file://configs/dynamodb_table.json --endpoint-url=http://localhost:4566
  ```
- **Empacote e crie a Lambda:**
  ```bash
  cd lambda
  pip install -r requirements.txt -t .
  zip -r ../lambda_function.zip .
  cd ..
  aws lambda create-function --function-name ProcessarNotasFiscais --runtime python3.9 --role arn:aws:iam::000000000000:role/lambda-role --handler grava_db.lambda_handler --zip-file fileb://lambda_function.zip --endpoint-url=http://localhost:4566
  ```
- **Permissão S3 para Lambda:**
  ```bash
  aws lambda add-permission --function-name ProcessarNotasFiscais --statement-id s3-trigger-permission --action "lambda:InvokeFunction" --principal s3.amazonaws.com --source-arn "arn:aws:s3:::notas-fiscais-upload" --endpoint-url=http://localhost:4566
  aws s3api put-bucket-notification-configuration --bucket notas-fiscais-upload --notification-configuration file://configs/notification_roles.json --endpoint-url=http://localhost:4566
  ```
- **API Gateway:**
  ```bash
  aws apigateway create-rest-api --name "NotasFiscaisAPI" --endpoint-url=http://localhost:4566
  # Recupere o rest-api-id e o resource-id conforme instruções do HELP.txt
  # Configure métodos POST e GET conforme utils2.txt
  # Integre com a Lambda e faça o deployment
  ```

### 4. Teste

- **Envie arquivo para S3:**
  ```bash
  aws s3 cp notas_fiscais_2025.json s3://notas-fiscais-upload --endpoint-url=http://localhost:4566
  ```
- **Teste API Gateway:**
  ```bash
  curl -X POST http://localhost:4566/restapis/<rest-api-id>/dev/_user_request_/notas -H "Content-Type: application/json" -d '{"id": "NF-999", "cliente": "João Silva", "valor": 1000.0, "data_emissao": "2025-01-31"}'
  curl -X GET http://localhost:4566/restapis/<rest-api-id>/dev/_user_request_/notas
  ```

> **Nota:** Para obter o `rest-api-id` e o `resource-id`, utilize os comandos do AWS CLI ou siga as instruções dos arquivos HELP.txt e utils2.txt.

## Observações
- Para depuração, verifique os logs do Localstack:
  ```bash
  docker logs localstack
  ```
