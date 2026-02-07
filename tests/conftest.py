import pytest
import boto3
import os
from services.config import AWS_ENDPOINT_URL, AWS_REGION, SHIPPING_QUEUE

os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = AWS_REGION

@pytest.fixture(scope="session", autouse=True)
def setup_localstack_resources():
    db = boto3.resource('dynamodb', endpoint_url=AWS_ENDPOINT_URL, region_name=AWS_REGION)

    tables_to_create = [
        {
            'TableName': 'Orders',
            'KeySchema': [{'AttributeName': 'order_id', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'order_id', 'AttributeType': 'S'}]
        },
        {
            'TableName': 'ShippingTable',
            'KeySchema': [{'AttributeName': 'shipping_id', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'shipping_id', 'AttributeType': 'S'}]
        }
    ]

    for table_cfg in tables_to_create:
        try:
            t = db.Table(table_cfg['TableName'])
            t.delete()
            t.wait_until_not_exists()
        except Exception:
            pass

        db.create_table(
            TableName=table_cfg['TableName'],
            KeySchema=table_cfg['KeySchema'],
            AttributeDefinitions=table_cfg['AttributeDefinitions'],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        ).wait_until_exists()

    # Створення черги SQS
    sqs = boto3.client('sqs', endpoint_url=AWS_ENDPOINT_URL, region_name=AWS_REGION)
    try:
        sqs.create_queue(QueueName=SHIPPING_QUEUE)
    except Exception:
        pass

    return True


@pytest.fixture
def dynamo_resource():
    return boto3.resource('dynamodb', endpoint_url=AWS_ENDPOINT_URL, region_name=AWS_REGION)