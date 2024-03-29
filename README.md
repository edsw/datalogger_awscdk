# AWS Data Logger

## Rough implementation guide:

### Raspberry Pi

1. Raspbian Lite installed headless to Pi Zero W via instructions: https://thedatafrog.com/en/articles/raspberry-pi-zero-headless-install/ 

2. Set secure root password and apply updates

```
sudo raspi-config
sudo apt update && sudo apt upgrade
```

3. Install your SSH keys

```
> ssh-copy-id -i ~/.ssh/id_rsa pi@rpi1
```

4. Pi is minimally configured with just the AWS CLI

```
curl "https://s3.amazonaws.com/aws-cli/awscli-bundle.zip" -o "awscli-bundle.zip"
unzip awscli-bundle.zip
sudo ./awscli-bundle/install -i /usr/local/aws -b /usr/local/bin/aws
/usr/local/bin/aws --version
aws-cli/1.18.61 Python/2.7.16 Linux/4.19.97+ botocore/1.16.11
```

5. Cron is configured to send the temperature to AWS every 5 minutes.

```
$ crontab -l
*/5 * * * * /home/pi/temp-to-aws.sh > /home/pi/temp-to-aws.log 2>&1
```

## AWS

* Lots TODO here, but see the `lambda` subdirectory for the functions. 
* Search files for "BUCKETNAME" and "example.com" to see areas for swapping in your own configuration.

At a high level...

* The Pi sends a data point to an S3 bucket, under a prefix/folder, every 5 minutes. The data is in JSON format, containing a timestamp and a temperature reading in both C/F.
* A Lambda, `lambda/start-athena-query/lambda_function.py`, is configured to run on S3 PUT events under this prefix/suffix. This Lambda starts an Athena query which scans all of the data and collects the latest 24 hours.
```
Event type: ObjectCreatedByPut
Prefix: pool/
Suffix: .json
```
* A second Lambda, `lambda/render-pool-plots/lambda_function.py`, is configured to run after the completion of the Athena query. This is triggered by an EventBridge (CloudWatch Events) event pattern:
```
{
  "detail-type": [
    "Athena Query State Change"
  ],
  "source": [
    "aws.athena"
  ],
  "detail": {
    "currentState": [
      "SUCCEEDED"
    ]
  }
}
```
* That second Lambda function receives the event information from EventBridge, which includes the path to the Athena query results. These results are loaded into a pandas data frame, with some light data manipulation applied. matplotlib is then used to generate a plot from the pandas data frame, in XKCD visual format. This plot is then copied to another S3 bucket.
* The second S3 bucket is configured as a static public web site (https://docs.aws.amazon.com/AmazonS3/latest/dev/WebsiteHosting.html). In order to do so, the bucket name must exactly match the DNS name of your public web site (home.example.com). This also only supports HTTP. I'll eventually leverage CloudFront to enable HTTPS in front of this (TODO). This S3 bucket contains only two files: the png generated by the second Lambda function, and `index.html` to display that png in a mobile friendly viewport window size.
* AWS Glue is configured to crawl and catalog the S3 data bucket, once a day after midnight local time, 4:30AM GMT. The crawler updates the Glue Data Catalog that defines the S3 metadata, in order to enable the Athena queries to work. It runs once a day after midnight in order to update the Data Catalog partitions. The Pi outputs data to S3 under a prefix that matches the pattern {year}/{month}/{day}/{timestamp}.json. Each of the prefixes is considered a partition by Glue. You'll notice in the Athena query (inside the Lambda function) that I use `WHERE` clauses against each of these partitions. This is in order to limit the amount of data searched at any given time. This lowers execution time and data scanned (and thus cost) because only two days' worth of data are ever being queried.

I'm currently writing an AWS CDK module to implement all of the AWS components for you. This is in progress as `datalogger_awscdk/datalogger_awscdk_stack.py`. Don't try to run that yet, it won't work.

# AWS CDK default text below (this is all super TODO)

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the .env
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .env
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .env/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .env\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation