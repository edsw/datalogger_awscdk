from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    aws_glue as glue,
    aws_athena as athena,
    aws_lambda as awslambda,
    aws_lambda_event_sources as lambda_events,
    core
)

PROJECT_NAME = "DataLogger"
PROJECT_PREFIX = "pool"

class DataloggerAwscdkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        s3_logs_bucket = s3.Bucket(self, "LogsBucket",
            encryption=s3.BucketEncryption.KMS_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    abort_incomplete_multipart_upload_after=core.Duration.days(7),
                    expiration=core.Duration.days(30)
                )
            ])

        s3_data_bucket = s3.Bucket(self, "DataBucket",
            encryption=s3.BucketEncryption.KMS_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            server_access_logs_bucket=s3_logs_bucket,
            server_access_logs_prefix=f"s3accesslogs/{PROJECT_NAME}/")

        glue_database = glue.Database(self, "GlueDatabase", database_name=PROJECT_NAME)

        glue_table = glue.Table(self, "GlueTable",
            columns=[
                glue.Column(name="timestamp", type=glue.Type(input_string="int", is_primitive=True)),
                glue.Column(name="celcius", type=glue.Type(input_string="double", is_primitive=True)),
                glue.Column(name="fahrenheit", type=glue.Type(input_string="double", is_primitive=True))
            ],
            database=glue_database,
            data_format=glue.DataFormat(
                input_format=glue.InputFormat("org.apache.hadoop.mapred.TextInputFormat"),
                output_format=glue.OutputFormat("org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"),
                serialization_library=glue.SerializationLibrary("org.openx.data.jsonserde.JsonSerDe")
            ),
            table_name=PROJECT_NAME,
            encryption=glue.TableEncryption.S3_MANAGED,
            partition_keys=[
                glue.Column(name="year", type=glue.Type(input_string="int", is_primitive=True)),
                glue.Column(name="month", type=glue.Type(input_string="int", is_primitive=True)),
                glue.Column(name="day", type=glue.Type(input_string="int", is_primitive=True))
            ]
        )

        glue_crawler_role = iam.Role(self, "GlueCrawlerRole", 
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSGlueServiceRole")
            ]
        )

        s3_data_bucket.grant_read(glue_crawler_role, objects_key_pattern=f"{PROJECT_PREFIX}/")
        s3_data_bucket.grant_put(glue_crawler_role, objects_key_pattern=f"{PROJECT_PREFIX}/")
        
        glue_crawler = glue.CfnCrawler(self, "GlueCrawler",
            role=glue_crawler_role.role_arn,
            database_name=glue_database.database_name,
            targets={
                "s3Targets": [{"path": f"{s3_data_bucket.bucket_name}/{PROJECT_PREFIX}/"}]
            },
            schedule={
                "scheduleExpression": "cron(30 04 * * ? *)"
            }
        )

        #athena_workgroup = athena.CfnWorkGroup(self, "AthenaWorkGroup", name=PROJECT_NAME)

