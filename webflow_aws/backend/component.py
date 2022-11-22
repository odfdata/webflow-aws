from constructs import Construct
from aws_cdk import (
    Stack
)

from backend.compute.infrastructure import Compute
from backend.networking.infrastructure import Networking


class Backend(Stack):

    def __init__(self, scope: Construct, construct_id: str, configuration: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        networking = Networking(self, "WebflowAwsNetworking", configuration=configuration)
        compute = Compute(self, "WebflowAwsCompute", configuration=configuration)
