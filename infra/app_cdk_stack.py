from constructs import Construct
from aws_cdk import (
    Stack,
    Duration,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_rds as rds,
    aws_ecs_patterns as ecs_patterns,
    aws_secretsmanager as secretsmanager
)

class AppCdkStack(Stack):

    @property
    def ecs_service_data(self):
        return self.service

    def __init__(self, scope: Construct, construct_id: str, ecr_repository, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(
            self, 'TrypSyncVPC'
        )

        ecs_cluster = ecs.Cluster(
            self, 'TrypSyncCluster',
            vpc = vpc
        )

        '''
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
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_15),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM
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
        db_instance.connections.allow_from(ecs_cluster, ec2.Port.tcp(5432), "Allow ECS to connect to DB")
        '''
        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "TrypSyncFargateService",
            cluster=ecs_cluster,
            cpu=256,
            desired_count=1,
            memory_limit_mib=512,
            public_load_balancer=True,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(ecr_repository),
                container_port=8081,
                container_name="trypsync-backend"
            )
        )
        
        service.target_group.configure_health_check(
            healthy_threshold_count = 2,
            unhealthy_threshold_count = 2,
            timeout = Duration.seconds(10),
            interval = Duration.seconds(11)
        )

        service.target_group.set_attribute('deregistration_delay.timeout_seconds', '5')

        self.service = service

