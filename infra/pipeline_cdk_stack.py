import os
from constructs import Construct
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_codecommit as codecommit,
    aws_codepipeline as codepipeline,
    aws_codebuild as codebuild,
    aws_codepipeline_actions as codepipeline_actions,
    aws_iam as iam,
)

class PipelineCdkStack(Stack):

    def __init__(self, scope: Construct, id: str, ecr_repository, test_app_fargate, prod_app_fargate, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)


        connection_arn = "arn:aws:codestar-connections:us-east-1:058264196609:connection/cba985e5-5b1f-411d-9ada-22c74e7c9680"
        github_owner = "akhil-arularasu"
        github_repo = "trypsync-backend-aws"
        github_branch = "main"

        # Artifact for pipeline output
        source_output = codepipeline.Artifact()

        # GitHub source action
        source_action = codepipeline_actions.CodeStarConnectionsSourceAction(
            action_name="GitHub_Source",
            owner=github_owner,
            repo=github_repo,
            branch=github_branch,
            connection_arn=connection_arn,
            output=source_output
        )

        pipeline = codepipeline.Pipeline(self, "Trypsync-Pipeline",)
        pipeline.add_stage(stage_name="Source", actions=[source_action])


        docker_build_project = codebuild.PipelineProject(
            self, 'Docker Build',
            build_spec = codebuild.BuildSpec.from_source_filename('./buildspec.yml'),
            environment = codebuild.BuildEnvironment(
                build_image = codebuild.LinuxBuildImage.STANDARD_5_0,
                privileged = True,
                compute_type = codebuild.ComputeType.LARGE,
                environment_variables = {
                    'IMAGE_TAG': codebuild.BuildEnvironmentVariable(
                        type = codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                        value = 'latest'
                    ),
                    'IMAGE_REPO_URI': codebuild.BuildEnvironmentVariable(
                        type = codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                        value = ecr_repository.repository_uri
                    ),
                    'AWS_DEFAULT_REGION': codebuild.BuildEnvironmentVariable(
                        type = codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                        value = os.environ['CDK_DEFAULT_REGION']
                    )
                }
            ),
        )

        docker_build_project.add_to_role_policy(iam.PolicyStatement(
            effect = iam.Effect.ALLOW,
            actions = [
                'ecr:GetAuthorizationToken',
                'ecr:BatchCheckLayerAvailability',
                'ecr:GetDownloadUrlForLayer',
                'ecr:GetRepositoryPolicy',
                'ecr:DescribeRepositories',
                'ecr:ListImages',
                'ecr:DescribeImages',
                'ecr:BatchGetImage',
                'ecr:InitiateLayerUpload',
                'ecr:UploadLayerPart',
                'ecr:CompleteLayerUpload',
                'ecr:PutImage'
            ],
            resources = ['*'],
        ))

        source_output = codepipeline.Artifact()
        docker_build_output = codepipeline.Artifact()

        docker_build_action = codepipeline_actions.CodeBuildAction(
            action_name = 'Docker-Build',
            project = docker_build_project,
            input = source_output,
            outputs = [docker_build_output]
        )

        pipeline.add_stage(
            stage_name = 'Docker-Build',
            actions = [docker_build_action]
        )

        pipeline.add_stage(
            stage_name = 'Deploy-Test',
            actions = [
                codepipeline_actions.EcsDeployAction(
                    action_name = 'Deploy-Test',
                    service = test_app_fargate.service,
                    input = docker_build_output
                )
            ]
        )

        pipeline.add_stage(
            stage_name = 'Deploy-Production',
            actions = [
                codepipeline_actions.ManualApprovalAction(
                    action_name = 'Approve-Prod-Deploy',
                    run_order = 1
                ),
                codepipeline_actions.EcsDeployAction(
                    action_name = 'Deploy-Production',
                    service = prod_app_fargate.service,
                    input = docker_build_output,
                    run_order = 2
                )
            ]
        )

        CfnOutput(
            self, 'GitHubRepoUrl',
            value=f"https://github.com/akhil-arularasu/trypsync-backend-aws"
        )