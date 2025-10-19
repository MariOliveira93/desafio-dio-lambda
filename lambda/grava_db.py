import json
import boto3
import os
from datetime import datetime
import uuid

# Configuração para Localstack
LOCALSTACK_ENDPOINT = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'NotasFiscais')

# Clientes AWS
dynamodb = boto3.resource('dynamodb', endpoint_url=LOCALSTACK_ENDPOINT)
s3_client = boto3.client('s3', endpoint_url=LOCALSTACK_ENDPOINT)
table = dynamodb.Table(DYNAMODB_TABLE)


def lambda_handler(event, context):
    """
    Handler principal da Lambda.
    Processa eventos do S3 (upload de arquivos) e API Gateway (POST/GET).
    """
    print(f"Evento recebido: {json.dumps(event)}")

    # Verifica se é evento do S3
    if 'Records' in event and event['Records'][0]['eventSource'] == 'aws:s3':
        return processar_evento_s3(event)

    # Verifica se é evento do API Gateway
    if 'httpMethod' in event:
        if event['httpMethod'] == 'POST':
            return processar_post(event)
        elif event['httpMethod'] == 'GET':
            return processar_get(event)

    return {
        'statusCode': 400,
        'body': json.dumps({'erro': 'Tipo de evento não suportado'})
    }


def processar_evento_s3(event):
    """
    Processa arquivos enviados ao S3.
    Extrai informações do arquivo e grava no DynamoDB.
    """
    try:
        # Extrai informações do evento S3
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        print(f"Processando arquivo: {bucket}/{key}")

        # Baixa o arquivo do S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        conteudo = response['Body'].read().decode('utf-8')

        # Gera ID único
        nota_id = str(uuid.uuid4())

        # Prepara item para DynamoDB
        item = {
            'id': nota_id,
            'arquivo': key,
            'bucket': bucket,
            'conteudo': conteudo,
            'data_upload': datetime.now().isoformat(),
            'tamanho': record['s3']['object']['size']
        }

        # Grava no DynamoDB
        table.put_item(Item=item)

        print(f"Nota fiscal {nota_id} gravada com sucesso")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'mensagem': 'Arquivo processado com sucesso',
                'id': nota_id
            })
        }

    except Exception as e:
        print(f"Erro ao processar arquivo S3: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'erro': str(e)})
        }


def processar_post(event):
    """
    Processa requisições POST do API Gateway.
    Cria uma nova nota fiscal no DynamoDB.
    """
    try:
        # Parse do body
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']

        # Gera ID único
        nota_id = str(uuid.uuid4())

        # Prepara item
        item = {
            'id': nota_id,
            'data_criacao': datetime.now().isoformat(),
            **body
        }

        # Grava no DynamoDB
        table.put_item(Item=item)

        print(f"Nota fiscal {nota_id} criada via API")

        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'mensagem': 'Nota fiscal criada com sucesso',
                'id': nota_id,
                'dados': item
            })
        }

    except Exception as e:
        print(f"Erro ao processar POST: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'erro': str(e)})
        }


def processar_get(event):
    """
    Processa requisições GET do API Gateway.
    Retorna todas as notas fiscais ou uma específica se ID fornecido.
    """
    try:
        # Verifica se há queryStringParameters
        params = event.get('queryStringParameters', {}) or {}
        nota_id = params.get('id')

        if nota_id:
            # Busca nota específica
            response = table.get_item(Key={'id': nota_id})

            if 'Item' not in response:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'erro': 'Nota fiscal não encontrada'})
                }

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(response['Item'])
            }

        # Retorna todas as notas
        response = table.scan()

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'total': len(response['Items']),
                'notas': response['Items']
            })
        }

    except Exception as e:
        print(f"Erro ao processar GET: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'erro': str(e)})
        }
