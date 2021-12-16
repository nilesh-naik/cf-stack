#!/usr/bin/env python3
# Generate CloudFormation template to set up load balancers for ACME.

from os.path import abspath
from troposphere import Ref, Join, Export, GetAtt
from troposphere import Parameter, Template, Tags, Output, Sub, ImportValue
from troposphere.elasticloadbalancingv2 import LoadBalancer, Listener, \
    LoadBalancerAttributes, ListenerRule, Action, Matcher, TargetGroup, \
    FixedResponseConfig, Certificate, Condition, RedirectConfig, \
    TargetDescription

# Set filename for template.
template_file = "templates/load-balancers.yaml"

office_ip_1 = "192.xxx.xxx.xxx/32"
office_ip_2 = "192.xxx.xxx.xxx/32"

# Get AWS pseudo parameter values.
ref_stack_name = Ref("AWS::StackName")

# Create object to generate the template.
template = Template()

template.set_version("2010-09-09")
template.set_description("Load balancers for ACME.")

# Define template parameters.
vpc_stackname_param = template.add_parameter(
    Parameter(
        "VPCStackName",
        Description=("Name of an active CloudFormation stack that contains "
                     "the networking resources, such as the vpc and "
                     "network subnet and that will be used in this stack."),
        Type="String",
        MinLength="1",
        MaxLength="255",
        AllowedPattern=r"^[a-zA-Z][-a-zA-Z0-9]*$"
    )
)

sg_name_param = template.add_parameter(
    Parameter(
        "SecurityGroupName",
        Description=("Name of security group that will be attached to "
                     "the Application Load Balancer."),
        Type="List<AWS::EC2::SecurityGroup::Id>"
    )
)

# Parameter for Load balancer stack name.
db_broker_stackname_param = template.add_parameter(
    Parameter(
        "DBBrokerStackName",
        Description=("Name of an active CloudFormation stack that contains "
                     "DB-Broker instances, that will be used in this stack."),
        Type="String",
        MinLength="1",
        MaxLength="255",
        AllowedPattern=r"^[a-zA-Z][-a-zA-Z0-9]*$"
    )
)

api_listener_cert_arn = template.add_parameter(
    Parameter(
        "APIListenerCert",
        Description=("ARN of the certificate to be used in API listener."),
        Type="String",
        MinLength="1",
        MaxLength="255"
    )
)

# Create Application load balancer for API.
api_load_balancer = template.add_resource(
    LoadBalancer(
        "APILoadBalancer",
        Name=Join("-", [ref_stack_name, "api"]),
        IpAddressType="ipv4",
        LoadBalancerAttributes=[
            LoadBalancerAttributes(
                Key="deletion_protection.enabled", Value="true"
            )
        ],
        Scheme="internet-facing",
        SecurityGroups=Ref(sg_name_param),
        Subnets=[
            ImportValue(Join(
                "-", [Ref(vpc_stackname_param), "publicsubnet1"]
            )),
            ImportValue(Join(
                "-", [Ref(vpc_stackname_param), "publicsubnet2"]
            )),
            ImportValue(Join(
                "-", [Ref(vpc_stackname_param), "publicsubnet3"]
            )),
        ],
        Type="application",
        Tags=Tags(Application=ref_stack_name)
    )
)

# Create Network load balancer for RabbitMQ.
mq_load_balancer = template.add_resource(
    LoadBalancer(
        "MQLoadBalancer",
        Name=Join("-", [ref_stack_name, "mq"]),
        IpAddressType="ipv4",
        LoadBalancerAttributes=[
            LoadBalancerAttributes(
                Key="deletion_protection.enabled", Value="true"
            ),
            LoadBalancerAttributes(
                Key="load_balancing.cross_zone.enabled", Value="true"
            )
        ],
        Scheme="internal",
        Subnets=[
            ImportValue(Join(
                "-", [Ref(vpc_stackname_param), "publicsubnet1"]
            )),
            ImportValue(Join(
                "-", [Ref(vpc_stackname_param), "publicsubnet2"]
            )),
            ImportValue(Join(
                "-", [Ref(vpc_stackname_param), "publicsubnet3"]
            )),
        ],
        Type="network",
        Tags=Tags(Application=ref_stack_name)
    )
)

# Create target group for API.
api_target_group = template.add_resource(
    TargetGroup(
        "APITargetGroup",
        Name=Join("-", [ref_stack_name, "api-tg"]),
        Port=80,
        Protocol="HTTP",
        HealthCheckEnabled=True,
        HealthCheckProtocol="HTTP",
        HealthCheckPath="/greetings",
        HealthCheckPort="traffic-port",
        HealthyThresholdCount=2,
        UnhealthyThresholdCount=2,
        HealthCheckTimeoutSeconds=2,
        HealthCheckIntervalSeconds=5,
        Matcher=Matcher(HttpCode="200"),
        TargetType="instance",
        VpcId=ImportValue(Join("-", [Ref(vpc_stackname_param), "id"])),
        Tags=Tags(Application=ref_stack_name)
    )
)

# Create target group for MQ.
mq_target_group = template.add_resource(
    TargetGroup(
        "MQTargetGroup",
        Name=Join("-", [ref_stack_name, "mq-tg"]),
        Port=5672,
        Protocol="TCP",
        HealthCheckEnabled=True,
        HealthCheckProtocol="TCP",
        HealthCheckPort="traffic-port",
        HealthyThresholdCount=3,
        UnhealthyThresholdCount=3,
        HealthCheckTimeoutSeconds=10,
        HealthCheckIntervalSeconds=30,
        Targets=[
            TargetDescription(
                Id=ImportValue(Join(
                    "-", [Ref(db_broker_stackname_param), "instance-1"])
                ),
                Port=5672
            ),
            TargetDescription(
                Id=ImportValue(Join(
                    "-", [Ref(db_broker_stackname_param), "instance-2"])
                ),
                Port=5672
            ),
            TargetDescription(
                Id=ImportValue(Join(
                    "-", [Ref(db_broker_stackname_param), "instance-3"])
                ),
                Port=5672
            )
        ],
        TargetType="instance",
        VpcId=ImportValue(Join("-", [Ref(vpc_stackname_param), "id"])),
        Tags=Tags(Application=ref_stack_name)
    )
)

# Create target group for RabbitMQ Management plugin.
mq_ui_target_group = template.add_resource(
    TargetGroup(
        "MQUITargetGroup",
        Name=Join("-", [ref_stack_name, "mq-ui-tg"]),
        Port=80,
        Protocol="HTTP",
        HealthCheckEnabled=True,
        HealthCheckProtocol="HTTP",
        HealthCheckPort="traffic-port",
        HealthyThresholdCount=3,
        UnhealthyThresholdCount=3,
        HealthCheckTimeoutSeconds=10,
        HealthCheckIntervalSeconds=30,
        Targets=[
            TargetDescription(
                Id=ImportValue(Join(
                    "-", [Ref(db_broker_stackname_param), "instance-1"])
                ),
                Port=80
            ),
            TargetDescription(
                Id=ImportValue(Join(
                    "-", [Ref(db_broker_stackname_param), "instance-2"])
                ),
                Port=80
            ),
            TargetDescription(
                Id=ImportValue(Join(
                    "-", [Ref(db_broker_stackname_param), "instance-3"])
                ),
                Port=80
            )
        ],
        TargetType="instance",
        VpcId=ImportValue(Join("-", [Ref(vpc_stackname_param), "id"])),
        Tags=Tags(Application=ref_stack_name)
    )
)

# Create API HTTP listener.
api_http_listener = template.add_resource(
    Listener(
        "APIHTTPListner",
        Port=80,
        Protocol="HTTP",
        LoadBalancerArn=Ref(api_load_balancer),
        DefaultActions=[Action(
            Type="fixed-response",
            FixedResponseConfig=FixedResponseConfig(
                ContentType="text/plain",
                MessageBody="Page Not Found",
                StatusCode="404"
            )
        )]
    )
)

# Create API HTTPS listener.
api_https_listener = template.add_resource(
    Listener(
        "APIHTTPSListner",
        Port=443,
        Protocol="HTTPS",
        Certificates=[Certificate(
            CertificateArn=Ref(api_listener_cert_arn)
        )],
        SslPolicy="ELBSecurityPolicy-TLS-1-1-2017-01",
        LoadBalancerArn=Ref(api_load_balancer),
        DefaultActions=[Action(
            Type="fixed-response",
            FixedResponseConfig=FixedResponseConfig(
                ContentType="text/plain",
                MessageBody="Page Not Found",
                StatusCode="404"
            )
        )]
    )
)

# Create MQ listener.
mq_listener = template.add_resource(
    Listener(
        "MQListner",
        Port=5672,
        Protocol="TCP",
        LoadBalancerArn=Ref(mq_load_balancer),
        DefaultActions=[Action(
            Type="forward",
            TargetGroupArn=Ref(mq_target_group)
        )]
    )
)

# Create API Listener rules.
api_http_listener_rule = template.add_resource(
    ListenerRule(
        "APIHTTPListenerRule",
        ListenerArn=Ref(api_http_listener),
        Conditions=[
            Condition(
                Field="host-header",
                Values=["app.acme.com",
                        "api.acme.com"]
            )
        ],
        Actions=[
            Action(
                Type="redirect",
                RedirectConfig=RedirectConfig(
                    StatusCode="HTTP_301",
                    Protocol="HTTPS",
                    Port="443"
                )
            )
        ],
        Priority=1
    )
)

api_https_listener_rule = template.add_resource(
    ListenerRule(
        "APIHTTPSRule",
        ListenerArn=Ref(api_https_listener),
        Conditions=[
            Condition(
                Field="host-header",
                Values=["app.acme.com",
                        "api.acme.com"]
            )
        ],
        Actions=[
            Action(
                Type="forward",
                TargetGroupArn=Ref(mq_ui_target_group)
            )
        ],
        Priority=2
    )
)

# Export Stack Output values.
api_load_balancer_output = template.add_output(
    Output(
        "APILoadBalancer",
        Value=Ref(api_load_balancer),
        Description="API Load Balancer ID",
        Export=Export(Sub("${AWS::StackName}-api"))
    )
)

api_target_group_output = template.add_output(
    Output(
        "APITargetGroup",
        Value=Ref(api_target_group),
        Description="API Target Group Name",
        Export=Export(Sub("${AWS::StackName}-api-tg"))
    )
)

mq_target_group_output = template.add_output(
    Output(
        "MQTargetGroup",
        Value=Ref(mq_target_group),
        Description="MQ Target Group Name",
        Export=Export(Sub("${AWS::StackName}-mq-tg"))
    )
)

mq_ui_target_group_output = template.add_output(
    Output(
        "MQUITargetGroup",
        Value=Ref(mq_ui_target_group),
        Description="MQ UI Target Group Name",
        Export=Export(Sub("${AWS::StackName}-mq-ui-tg"))
    )
)

api_load_balancer_dns_output = template.add_output(
    Output(
        "APILoadBalancerDNS",
        Value=GetAtt(api_load_balancer, "DNSName"),
        Description="API Load Balancer DNS name",
        Export=Export(Sub("${AWS::StackName}-api-dns"))
    )
)

mq_load_balancer_dns_output = template.add_output(
    Output(
        "MQLoadBalancerDNS",
        Value=GetAtt(mq_load_balancer, "DNSName"),
        Description="MQ Load Balancer DNS name",
        Export=Export(Sub("${AWS::StackName}-mq-dns"))
    )
)

# Generate and write template to file.
try:
    print(template.to_yaml(), file=open(template_file, "w"))
    print("Template written to file %s" % abspath(template_file))
except IOError as e:
    print("Couldn't open or write to file (%s)." % e)
