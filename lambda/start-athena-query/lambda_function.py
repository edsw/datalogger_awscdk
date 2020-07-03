import boto3

def lambda_handler(event, context):

    print('## EVENT')
    print(event)

    athena_params = {
        'region': 'us-east-2',
        'database': 'iot-s3-data',
        'bucket': 'BUCKETNAME'
    }
    
    query_params_24hr = {
        'path': 'athena-results/iot-pool-24-hours',
        'query': """
SELECT   fahrenheit,
         from_unixtime(timestamp) AT TIME ZONE 'US/Eastern' AS time
FROM     pool
WHERE    cast(partition_0 AS bigint) >= IF(
           (
             extract(year FROM (current_timestamp AT TIME ZONE 'US/Eastern')) =
             extract(year FROM (current_timestamp AT TIME ZONE 'US/Eastern') - INTERVAL '1' DAY)
           ),
           extract(year FROM (current_timestamp AT TIME ZONE 'US/Eastern')),
           extract(year FROM (current_timestamp AT TIME ZONE 'US/Eastern') - INTERVAL '1' DAY)
         ) AND
         cast(partition_1 AS bigint) >= IF(
           (
             extract(month FROM (current_timestamp AT TIME ZONE 'US/Eastern')) =
             extract(month FROM (current_timestamp AT TIME ZONE 'US/Eastern') - INTERVAL '1' DAY)
           ),
           extract(month FROM (current_timestamp AT TIME ZONE 'US/Eastern')),
           extract(month FROM (current_timestamp AT TIME ZONE 'US/Eastern') - INTERVAL '1' DAY)
         ) AND
         cast(partition_2 AS bigint) IN (
           extract(day FROM (current_timestamp AT TIME ZONE 'US/Eastern') - INTERVAL '1' DAY),
           extract(day FROM (current_timestamp AT TIME ZONE 'US/Eastern'))
         ) AND
         date_diff('minute', from_unixtime(timestamp), current_timestamp) < 1440
ORDER BY time ASC
        """
    }
    
    client = boto3.client('athena', region_name=athena_params["region"])
    
    response = client.start_query_execution(
        QueryString=query_params_24hr["query"],
        QueryExecutionContext={
            'Database': athena_params['database']
        },
        ResultConfiguration={
            'OutputLocation': 's3://' + athena_params['bucket'] + '/' + query_params_24hr['path']
        }
    )
    
    execution_id = response['QueryExecutionId']
    print(f'Execution ID: {execution_id}')

    return {
        'statusCode': 200
#        'body': json.dumps('Hello from Lambda!')
    }
