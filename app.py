#!/usr/bin/env python3

from aws_cdk import core

from datalogger_awscdk.datalogger_awscdk_stack import DataloggerAwscdkStack


app = core.App()
DataloggerAwscdkStack(app, "datalogger-awscdk")

app.synth()
