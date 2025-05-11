from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ecs_patterns as ecs_patterns,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

class TrypSyncFargateRDSStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Use default VPC
        vpc = ec2.Vpc.from_lookup(self, "DefaultVPC", is_default=True)

        # ECS Cluster
        cluster = ecs.Cluster(self, "TrypSyncCluster", vpc=vpc)

        # ECR Repository (reference existing one)
        repo = ecr.Repository.from_repository_name(
            self, "TrypSyncRepo", repository_name="trypsync-backend"
        )

        # Secret for RDS credentials
        db_secret = secretsmanager.Secret(self, "DBCredentialsSecret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username":"dbadmin"}',
                generate_string_key="password",
                exclude_punctuation=True
            )
        )

        # RDS PostgreSQL Instance
        db_instance = rds.DatabaseInstance(
            self, "TrypSyncPostgres",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_14_8),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            credentials=rds.Credentials.from_secret(db_secret),
            multi_az=False,
            allocated_storage=20,
            max_allocated_storage=100,
            publicly_accessible=True,
            deletion_protection=False,
            database_name="trypsyncdb"
        )

        # Allow ECS service to connect to DB
        db_instance.connections.allow_default_port_from_any_ipv4("Allow from anywhere")  # or restrict to VPC later

        # ECS Fargate + ALB
        ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "TrypSyncFargateService",
            cluster=cluster,
            cpu=256,
            desired_count=1,
            memory_limit_mib=512,
            public_load_balancer=True,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(repo),
                container_port=5000,
                environment={
                    "PORT": "5000",
                    "DB_HOST": db_instance.db_instance_endpoint_address,
                    "DB_PORT": db_instance.db_instance_endpoint_port,
                    "DB_NAME": "trypsyncdb",
                    "DB_USER": db_secret.secret_value_from_json("username").unsafe_unwrap(),
                    "DB_PASSWORD": db_secret.secret_value_from_json("password").unsafe_unwrap()
                }
            )
        )
