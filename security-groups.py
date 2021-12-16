#!/usr/bin/env python3
# Generate CloudFormation template to set up security groups for ACME.

from os.path import abspath
from troposphere import Ref, Join, Export
from troposphere import Parameter, Template, Tags, Output, Sub, ImportValue
from troposphere.ec2 import SecurityGroup, SecurityGroupRule

# Set filename for template.
template_file = "templates/security-groups.yaml"

jumpserver_ip_1 = "xx.xx.xx.xx/32"
jumpserver_ip_2 = "xx.xx.xx.xx/32"

# Get AWS pseudo parameter values.
ref_stack_name = Ref("AWS::StackName")

# Create object to generate the template.
template = Template()

template.set_version("2010-09-09")
template.set_description("EC2 Security groups for ACME.")

# Define template parameters.
vpc_stackname_param = template.add_parameter(
    Parameter(
        "VPCStackName",
        Description=("Name of an active CloudFormation stack that contains "
                     "the networking resources, such as the vpc, subnet and "
                     "security group, that will be used in this stack."),
        Type="String",
        MinLength="1",
        MaxLength="255",
        AllowedPattern=r"^[a-zA-Z][-a-zA-Z0-9]*$"
    )
)

# Create security groups.
alb_security_group = template.add_resource(
    SecurityGroup(
        "LoadBalancerSecurityGroup",
        GroupName=Join("-", [ref_stack_name, "alb-security-group"]),
        GroupDescription="Enable traffic to load balancer listeners.",
        SecurityGroupIngress=[
            SecurityGroupRule(
                Description="Enable HTTP access via port 80",
                IpProtocol="tcp",
                FromPort=80,
                ToPort=80,
                CidrIp="0.0.0.0/0"
            ),
            SecurityGroupRule(
                Description="Enable HTTPS access via port 443",
                IpProtocol="tcp",
                FromPort=443,
                ToPort=443,
                CidrIp="0.0.0.0/0"
            )
        ],
        VpcId=ImportValue(Join("-", [Ref(vpc_stackname_param), "id"])),
        Tags=Tags(
            Application=ref_stack_name,
            Name=Join("-", [ref_stack_name, "alb-security-group"]),
        )
    )
)

api_security_group = template.add_resource(
    SecurityGroup(
        "APIInstanceSecurityGroup",
        GroupName=Join("-", [ref_stack_name, "api-security-group"]),
        GroupDescription="Security group for API server.",
        SecurityGroupIngress=[
            SecurityGroupRule(
                Description="Enable SSH access via port 22",
                IpProtocol="tcp",
                FromPort=22,
                ToPort=22,
                CidrIp=jumpserver_ip_1
            ),
            SecurityGroupRule(
                Description="Enable SSH access via port 22",
                IpProtocol="tcp",
                FromPort=22,
                ToPort=22,
                CidrIp=jumpserver_ip_2
            ),
            SecurityGroupRule(
                Description="Enable HTTP port access from ALB.",
                IpProtocol="tcp",
                FromPort=80,
                ToPort=80,
                SourceSecurityGroupId=Ref(alb_security_group)
            )
        ],
        VpcId=ImportValue(Join("-", [Ref(vpc_stackname_param), "id"])),
        Tags=Tags(
            Application=ref_stack_name,
            Name=Join("-", [ref_stack_name, "api-security-group"]),
        )
    )
)

db_broker_security_group = template.add_resource(
    SecurityGroup(
        "DBBrokerInstanceSecurityGroup",
        GroupName=Join("-", [ref_stack_name, "db-broker-security-group"]),
        GroupDescription="Enable access to db/broker instance from API.",
        SecurityGroupIngress=[
            SecurityGroupRule(
                Description="Enable SSH access via port 22",
                IpProtocol="tcp",
                FromPort=22,
                ToPort=22,
                SourceSecurityGroupId=Ref(api_security_group)
            ),
            SecurityGroupRule(
                Description="Enable db access via port 27017",
                IpProtocol="tcp",
                FromPort=27017,
                ToPort=27017,
                SourceSecurityGroupId=Ref(api_security_group)
            ),
            SecurityGroupRule(
                Description="Enable broker access via port 5672",
                IpProtocol="tcp",
                FromPort=5672,
                ToPort=5672,
                CidrIp=ImportValue(Join(
                    "-", [Ref(vpc_stackname_param), "cidr"])
                )
            )
        ],
        VpcId=ImportValue(Join("-", [Ref(vpc_stackname_param), "id"])),
        Tags=Tags(
            Application=ref_stack_name,
            Name=Join("-", [ref_stack_name, "db-broker-security-group"]),
        )
    )
)

# Export Stack Output values.
alb_security_group_output = template.add_output(
    Output(
        "LoadBalancerSecurityGroupID",
        Value=Ref(alb_security_group),
        Description="ALB Security Group ID",
        Export=Export(Sub("${AWS::StackName}-loadbalancer"))
    )
)

api_security_group_output = template.add_output(
    Output(
        "APISecurityGroupID",
        Value=Ref(api_security_group),
        Description="API Security Group ID",
        Export=Export(Sub("${AWS::StackName}-api"))
    )
)

db_broker_security_group_output = template.add_output(
    Output(
        "DatabaseBrokerSecurityGroupID",
        Value=Ref(db_broker_security_group),
        Description="Database/Broker Security Group ID",
        Export=Export(Sub("${AWS::StackName}-database"))
    )
)

# Generate and write template to file.
try:
    print(template.to_yaml(), file=open(template_file, "w"))
    print("Template written to file %s" % abspath(template_file))
except IOError as e:
    print("Couldn't open or write to file (%s)." % e)
