#!/usr/bin/env python3
import aws_cdk as cdk
from ecs_fargate_rds_stack import TrypSyncFargateRDSStack

app = cdk.App()
TrypSyncFargateRDSStack(app, "TrypSyncFargateRDSStack")
app.synth()