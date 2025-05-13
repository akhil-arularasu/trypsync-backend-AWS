#!/usr/bin/env python3
import aws_cdk as cdk
from ecs_fargate_rds_stack import TrypSyncFargateRDSStack
from pipeline_stack import TrypSyncPipelineStack

app = cdk.App()

# Add your AWS account ID and region below
env = cdk.Environment(account="058264196609", region="us-east-1")

TrypSyncFargateRDSStack(app, "TrypSyncFargateRDSStack", env=env)
TrypSyncPipelineStack(app, "TrypSyncPipelineStack", env=env)

app.synth()
