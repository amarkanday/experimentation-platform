from aws_cdk import (
    Stack,
    aws_cognito as cognito,
    Duration,
    CfnOutput,
    RemovalPolicy,
)
from constructs import Construct


class AuthenticationStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, environment: str = "dev", **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define the Cognito User Pool
        self.user_pool = cognito.UserPool(
            self,
            "ExperimentationUserPool",
            user_pool_name=f"experimentation-platform-users-{environment}",
            # Self-signup configuration
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=True,
            ),
            # Password policy
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(7),
            ),
            # Advanced security features
            advanced_security_mode=cognito.AdvancedSecurityMode.OFF,
            # Account recovery settings
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            # Email settings
            email=cognito.UserPoolEmail.with_cognito(
                reply_to="support@experimentation-platform.com",
            ),
            # User attributes
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=True,
                ),
                given_name=cognito.StandardAttribute(
                    required=True,
                    mutable=True,
                ),
                family_name=cognito.StandardAttribute(
                    required=True,
                    mutable=True,
                ),
                phone_number=cognito.StandardAttribute(
                    required=False,
                    mutable=True,
                ),
            ),
            # Auto-verification settings are not directly configurable in aws_cognito.
            # MFA configuration
            mfa=cognito.Mfa.OPTIONAL,
            mfa_second_factor=cognito.MfaSecondFactor(
                sms=True,
                otp=True,
            ),
            # Deletion policy for the development environment
            removal_policy=(
                RemovalPolicy.DESTROY if environment == "dev" else RemovalPolicy.RETAIN
            ),
        )

        # Add custom attributes
        # Add custom attributes to the User Pool Client
        self.user_pool_client = self.user_pool.add_client(
            "ExperimentationUserPoolClient",
            user_pool_client_name=f"experimentation-platform-client-{environment}",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                admin_user_password=True,
                custom=True,
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ],
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                ),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.PROFILE,
                ],
                callback_urls=["https://example.com/callback"],
                logout_urls=["https://example.com/logout"],
            ),
        )

        # Output the User Pool ID and ARN for reference
        CfnOutput(
            self,
            "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID",
            export_name=f"{construct_id}-UserPoolId",
        )

        CfnOutput(
            self,
            "UserPoolArn",
            value=self.user_pool.user_pool_arn,
            description="Cognito User Pool ARN",
            export_name=f"{construct_id}-UserPoolArn",
        )
