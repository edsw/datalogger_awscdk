import boto3
import pandas as pd
import matplotlib.pyplot as plt
#import seaborn as sns
from matplotlib.dates import DateFormatter
from io import StringIO
from pytz import timezone
import json, re, os

def lambda_handler(event, context):
    params = {
        'region': 'us-east-2',
        'athena_bucket': 'BUCKETNAME',
        'athena_prefix': 'athena-results',
        'output_bucket': 'home.example.com'
    }
    
    query_params_24hr = {
        'path': 'iot-pool-24-hours'
    }
    
    queryExecutionId = event['detail']['queryExecutionId']
    queryRegion = event['region']
    
    athena = boto3.client('athena', region_name=queryRegion)
    response = athena.get_query_execution(QueryExecutionId=queryExecutionId)
    
    s3_path = response['QueryExecution']['ResultConfiguration']['OutputLocation']
    filename = re.findall('.*\/(.*)', s3_path)[0]
    
    s3 = boto3.resource('s3')
    obj = s3.Object(
        params['athena_bucket'], f"{params['athena_prefix']}/{query_params_24hr['path']}/{filename}")
    csv = obj.get()['Body'].read().decode('utf-8')
    
    if query_params_24hr['path'] in s3_path:
    
        df = pd.read_table(StringIO(csv), sep=',', dtype={
            'fahrenheit': float,
            'time': object
        })
    
        df.time = pd.to_datetime(
            df.time, format='%Y-%m-%d %H:%M:%S.%f %Z', errors='coerce')
    
        plt.clf()
        plt.cla()
        plt.xkcd()
        
        ax = plt.gca()
    
        df.plot(kind='line', x='time', y='fahrenheit', ax=ax, legend=None)
    
        ax.xaxis.set_major_formatter(DateFormatter('%a %l%p', timezone('US/Eastern')))
        ax.set_xlabel('')
        ax.set_ylabel('')
    
        dflast = df.tail(1).index[0]
        ylast = df.fahrenheit[dflast].round(decimals=1)
        xlast = df.time[dflast]

        ax.annotate(ylast, xy=(xlast, ylast))
    
        plt.title('Last 24 Hours Pool Temperature')
        
        outfile = '/tmp/last-24-hours.png'
        if os.path.isfile(outfile):
            os.remove(outfile)
        
        plt.savefig(outfile)
        
        s3.Bucket(params['output_bucket']).upload_file(outfile, 'last-24-hours.png')
    return {
        'statusCode': 200
#        'body': json.dumps('Hello from Lambda!')
    }
