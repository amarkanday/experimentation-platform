from aws_cdk import (
    Stack,
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets,
)
from constructs import Construct


class ApiStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, vpc, compute, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a Cognito User Pool for authentication - simplified to minimum required params
        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            self_sign_up_enabled=True,
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            user_pool_name="experimentation-user-pool",
        )

        # Create a User Pool Client
        self.user_pool_client = cognito.UserPoolClient(
            self, "UserPoolClient", user_pool=self.user_pool, generate_secret=True
        )

        # Create an authorizer for API Gateway
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, "ApiAuthorizer", cognito_user_pools=[self.user_pool]
        )

        # Create API Gateway
        self.api = apigateway.RestApi(
            self,
            "ExperimentationApi",
            rest_api_name="Experimentation Platform API",
            description="API for the experimentation platform",
        )

        # Integration with Lambda functions
        # 1. Assignment Lambda Integration
        assignment_integration = apigateway.LambdaIntegration(
            compute.assignment_lambda, proxy=True
        )

        # 2. Feature Flag Lambda Integration
        feature_flag_integration = apigateway.LambdaIntegration(
            compute.feature_flag_lambda, proxy=True
        )

        # 3. Event Processor Lambda Integration
        event_processor_integration = apigateway.LambdaIntegration(
            compute.event_processor_lambda, proxy=True
        )

        # Create API resources and methods
        # Assignments API
        assignments = self.api.root.add_resource("assignments")
        assignments.add_method("GET", assignment_integration, authorizer=authorizer)

        # Feature Flags API
        feature_flags = self.api.root.add_resource("feature-flags")
        evaluate = feature_flags.add_resource("evaluate")
        evaluate.add_method("GET", feature_flag_integration)

        # Events API
        events = self.api.root.add_resource("events")
        events.add_method("POST", event_processor_integration)

        # Add a batch endpoint for events
        batch = events.add_resource("batch")
        batch.add_method("POST", event_processor_integration)

        # Health check endpoint (no authorization required)
        health = self.api.root.add_resource("health")
        health.add_method(
            "GET",
            apigateway.MockIntegration(
                integration_responses=[
                    {
                        "statusCode": "200",
                        "responseTemplates": {
                            "application/json": '{"status": "healthy"}'
                        },
                    }
                ],
                passthrough_behavior=apigateway.PassthroughBehavior.NEVER,
                request_templates={"application/json": '{"statusCode": 200}'},
            ),
        )
