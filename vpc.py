#!/usr/bin/env python3
# Generate CloudFormation template to set up VPC environment in AWS.

from os.path import abspath
from troposphere import FindInMap, Select, Ref, GetAZs, Join, Export, GetAtt
from troposphere import Template, Tags, Output, Sub
from troposphere.ec2 import VPC, Subnet, InternetGateway, \
    VPCGatewayAttachment, Route, RouteTable, SubnetRouteTableAssociation, \
    NetworkAcl, NetworkAclEntry, SubnetNetworkAclAssociation, \
    DHCPOptions, VPCDHCPOptionsAssociation, EIP, NatGateway

# Set filename for template.
template_file = "templates/vpc.yaml"

# Define CIDR blocks for VPC and subnets.
vpc_cidr_block = "10.10.0.0/16"
public_subnet_1_cidr = "10.10.1.0/24"
public_subnet_2_cidr = "10.10.2.0/24"
public_subnet_3_cidr = "10.10.3.0/24"
private_subnet_1_cidr = "10.10.128.0/24"
private_subnet_2_cidr = "10.10.129.0/24"
private_subnet_3_cidr = "10.10.130.0/24"
office_ip_1 = "192.xxx.xxx.xxx/32"
office_ip_2 = "192.xxx.xxx.xxx/32"

# Get AWS pseudo parameter values.
ref_region = Ref("AWS::Region")
ref_stack_id = Ref("AWS::StackId")
ref_stack_name = Ref("AWS::StackName")

# Create object to generate the template.
template = Template()

template.set_version("2010-09-09")
template.set_description("VPC for hosting ACME Corp application.")

# Define template parameters.
# Define template mappings.
template.add_mapping("SubnetConfig", {
    "VPC": {"CIDR": vpc_cidr_block},
    "PublicSubnet1": {"CIDR": public_subnet_1_cidr},
    "PublicSubnet2": {"CIDR": public_subnet_2_cidr},
    "PublicSubnet3": {"CIDR": public_subnet_3_cidr},
    "PrivateSubnet1": {"CIDR": private_subnet_1_cidr},
    "PrivateSubnet2": {"CIDR": private_subnet_2_cidr},
    "PrivateSubnet3": {"CIDR": private_subnet_3_cidr},
})

# Define template resources.
# Create new VPC.
vpc = template.add_resource(
    VPC(
        "VPC",
        CidrBlock=FindInMap("SubnetConfig", "VPC", "CIDR"),
        EnableDnsSupport="true",
        EnableDnsHostnames=True,
        Tags=Tags(Name=ref_stack_name, Application=ref_stack_name)
    )
)

# Define 3 public subnets.
public_subnet_1 = template.add_resource(
    Subnet(
        "PublicSubnet1",
        AvailabilityZone=Select(0, GetAZs(region=ref_region)),
        CidrBlock=FindInMap("SubnetConfig", "PublicSubnet1", "CIDR"),
        VpcId=Ref(vpc),
        MapPublicIpOnLaunch=True,
        Tags=Tags(
            Name=Join("-", [ref_stack_name, "public-subnet-1"]),
            Application=ref_stack_name
        )
    )
)

public_subnet_2 = template.add_resource(
    Subnet(
        "PublicSubnet2",
        AvailabilityZone=Select(1, GetAZs(region=ref_region)),
        CidrBlock=FindInMap("SubnetConfig", "PublicSubnet2", "CIDR"),
        VpcId=Ref(vpc),
        MapPublicIpOnLaunch=True,
        Tags=Tags(
            Name=Join("-", [ref_stack_name, "public-subnet-2"]),
            Application=ref_stack_name
        )
    )
)

public_subnet_3 = template.add_resource(
    Subnet(
        "PublicSubnet3",
        AvailabilityZone=Select(2, GetAZs(region=ref_region)),
        CidrBlock=FindInMap("SubnetConfig", "PublicSubnet3", "CIDR"),
        VpcId=Ref(vpc),
        MapPublicIpOnLaunch=True,
        Tags=Tags(
            Name=Join("-", [ref_stack_name, "public-subnet-3"]),
            Application=ref_stack_name
        )
    )
)

# Define 3 private subnets.
private_subnet_1 = template.add_resource(
    Subnet(
        "PrivateSubnet1",
        AvailabilityZone=Select(0, GetAZs(region=ref_region)),
        CidrBlock=FindInMap("SubnetConfig", "PrivateSubnet1", "CIDR"),
        VpcId=Ref(vpc),
        MapPublicIpOnLaunch=False,
        Tags=Tags(
            Name=Join("-", [ref_stack_name, "private-subnet-1"]),
            Application=ref_stack_name
        )
    )
)

private_subnet_2 = template.add_resource(
    Subnet(
        "PrivateSubnet2",
        AvailabilityZone=Select(1, GetAZs(region=ref_region)),
        CidrBlock=FindInMap("SubnetConfig", "PrivateSubnet2", "CIDR"),
        VpcId=Ref(vpc),
        MapPublicIpOnLaunch=False,
        Tags=Tags(
            Name=Join("-", [ref_stack_name, "private-subnet-2"]),
            Application=ref_stack_name
        )
    )
)

private_subnet_3 = template.add_resource(
    Subnet(
        "PrivateSubnet3",
        AvailabilityZone=Select(2, GetAZs(region=ref_region)),
        CidrBlock=FindInMap("SubnetConfig", "PrivateSubnet3", "CIDR"),
        VpcId=Ref(vpc),
        MapPublicIpOnLaunch=False,
        Tags=Tags(
            Name=Join("-", [ref_stack_name, "private-subnet-3"]),
            Application=ref_stack_name
        )
    )
)

# Create and attach Internet Gateway.
internet_gateway = template.add_resource(
    InternetGateway(
        "InternetGateway",
        Tags=Tags(Application=ref_stack_name)
    )
)

gateway_attachment = template.add_resource(
    VPCGatewayAttachment(
        "AttachGateway",
        VpcId=Ref(vpc),
        InternetGatewayId=Ref(internet_gateway)
    )
)

# Create route tables and route to the Internet.
public_route_table = template.add_resource(
    RouteTable(
        "PublicRouteTable",
        VpcId=Ref(vpc),
        Tags=Tags(
            Name=Join("-", [ref_stack_name, "public-rt"]),
            Application=ref_stack_name
        )
    )
)

private_route_table = template.add_resource(
    RouteTable(
        "PrivateRouteTable",
        VpcId=Ref(vpc),
        Tags=Tags(
            Name=Join("-", [ref_stack_name, "private-rt"]),
            Application=ref_stack_name
        )
    )
)

route_to_internet = template.add_resource(
    Route(
        "RouteToInternet",
        DependsOn="AttachGateway",
        GatewayId=Ref(internet_gateway),
        DestinationCidrBlock="0.0.0.0/0",
        RouteTableId=Ref(public_route_table)
    )
)

# Create and attach NAT Gateway.
nat_ip = template.add_resource(
    EIP(
        "NatEip",
        Domain="vpc"
    )
)

nat_gateway = template.add_resource(
    NatGateway(
        "NATGateway",
        AllocationId=GetAtt(nat_ip, "AllocationId"),
        SubnetId=Ref(public_subnet_1),
        Tags=Tags(Application=ref_stack_name)
    )
)

nat_route = template.add_resource(
    Route(
        "NATRoute",
        RouteTableId=Ref(private_route_table),
        NatGatewayId=Ref(nat_gateway),
        DestinationCidrBlock="0.0.0.0/0"
    )
)

# Associate subnets with route table.
public_subnet_1_route_table_association = template.add_resource(
    SubnetRouteTableAssociation(
        "PublicSubnet1RouteTableAssociation",
        SubnetId=Ref(public_subnet_1),
        RouteTableId=Ref(public_route_table)
    )
)

public_subnet_2_route_table_association = template.add_resource(
    SubnetRouteTableAssociation(
        "PublicSubnet2RouteTableAssociation",
        SubnetId=Ref(public_subnet_2),
        RouteTableId=Ref(public_route_table)
    )
)

public_subnet_3_route_table_association = template.add_resource(
    SubnetRouteTableAssociation(
        "PublicSubnet3RouteTableAssociation",
        SubnetId=Ref(public_subnet_3),
        RouteTableId=Ref(public_route_table)
    )
)

private_subnet_1_route_table_association = template.add_resource(
    SubnetRouteTableAssociation(
        "PrivateSubnet1RouteTableAssociation",
        SubnetId=Ref(private_subnet_1),
        RouteTableId=Ref(private_route_table)
    )
)

private_subnet_2_route_table_association = template.add_resource(
    SubnetRouteTableAssociation(
        "PrivateSubnet2RouteTableAssociation",
        SubnetId=Ref(private_subnet_2),
        RouteTableId=Ref(private_route_table)
    )
)

private_subnet_3_route_table_association = template.add_resource(
    SubnetRouteTableAssociation(
        "PrivateSubnet3RouteTableAssociation",
        SubnetId=Ref(private_subnet_3),
        RouteTableId=Ref(private_route_table)
    )
)

# Create Network ACLs.
public_network_acl = template.add_resource(
    NetworkAcl(
        "PublicNetworkAcl",
        VpcId=Ref(vpc),
        Tags=Tags(
            Name=Join("-", [ref_stack_name, "public-nacl"]),
            Application=ref_stack_name
        )
    )
)

private_network_acl = template.add_resource(
    NetworkAcl(
        "PrivateNetworkAcl",
        VpcId=Ref(vpc),
        Tags=Tags(
            Name=Join("-", [ref_stack_name, "private-nacl"]),
            Application=ref_stack_name
        )
    )
)

# Define public inbound ACL rule.
inbound_public_acl_entry = template.add_resource(
    NetworkAclEntry(
        "InboundPublicNetworkAclEntry",
        NetworkAclId=Ref(public_network_acl),
        RuleNumber=100,
        Protocol=-1,
        RuleAction="allow",
        Egress=False,
        CidrBlock="0.0.0.0/0"
    )
)

# Define public outbound ACL rule.
outbound_public_acl_entry = template.add_resource(
    NetworkAclEntry(
        "OutboundPublicNetworkAclEntry",
        NetworkAclId=Ref(public_network_acl),
        RuleNumber=100,
        Protocol=-1,
        RuleAction="allow",
        Egress=True,
        CidrBlock="0.0.0.0/0"
    )
)

# Define private inbound ACL rule.
inbound_private_acl_entry = template.add_resource(
    NetworkAclEntry(
        "InboundPrivateNetworkAclEntry",
        NetworkAclId=Ref(private_network_acl),
        RuleNumber=110,
        Protocol=-1,
        RuleAction="allow",
        Egress=False,
        CidrBlock=vpc_cidr_block
    )
)

# Define private outbound ACL rule.
outbound_private_acl_entry = template.add_resource(
    NetworkAclEntry(
        "OutboundPrivateNetworkAclEntry",
        NetworkAclId=Ref(private_network_acl),
        RuleNumber=110,
        Protocol=-1,
        RuleAction="allow",
        Egress=True,
        CidrBlock="0.0.0.0/0"
    )
)

# Associate subnets with network ACL.
public_subnet_1_network_acl_association = template.add_resource(
    SubnetNetworkAclAssociation(
        "PublicSubnet1NetworkACLAssociation",
        SubnetId=Ref(public_subnet_1),
        NetworkAclId=Ref(public_network_acl)
    )
)

public_subnet_2_network_acl_association = template.add_resource(
    SubnetNetworkAclAssociation(
        "PublicSubnet2NetworkACLAssociation",
        SubnetId=Ref(public_subnet_2),
        NetworkAclId=Ref(public_network_acl)
    )
)

public_subnet_3_network_acl_association = template.add_resource(
    SubnetNetworkAclAssociation(
        "PublicSubnet3NetworkACLAssociation",
        SubnetId=Ref(public_subnet_3),
        NetworkAclId=Ref(public_network_acl)
    )
)

private_subnet_1_network_acl_association = template.add_resource(
    SubnetNetworkAclAssociation(
        "PrivateSubnet1NetworkACLAssociation",
        SubnetId=Ref(private_subnet_1),
        NetworkAclId=Ref(private_network_acl)
    )
)

private_subnet_2_network_acl_association = template.add_resource(
    SubnetNetworkAclAssociation(
        "PrivateSubnet2NetworkACLAssociation",
        SubnetId=Ref(private_subnet_2),
        NetworkAclId=Ref(private_network_acl)
    )
)

private_subnet_3_network_acl_association = template.add_resource(
    SubnetNetworkAclAssociation(
        "PrivateSubnet3NetworkACLAssociation",
        SubnetId=Ref(private_subnet_3),
        NetworkAclId=Ref(private_network_acl)
    )
)

# Create DHCP options and associate with VPC.
dhcp_options = template.add_resource(
    DHCPOptions(
        "DHCPOptions",
        DomainName=Join(".", [ref_region, "compute.internal"]),
        DomainNameServers=["AmazonProvidedDNS"],
        Tags=Tags(Application=ref_stack_name)
    )
)

dhcp_options_association = template.add_resource(
    VPCDHCPOptionsAssociation(
        "DHCPOptionsAssociation",
        DhcpOptionsId=Ref(dhcp_options),
        VpcId=Ref(vpc)
    )
)

# Export Stack Output values.
vpc_output = template.add_output(
    Output(
        "VPCID",
        Value=Ref(vpc),
        Description="VPC ID",
        Export=Export(Sub("${AWS::StackName}-id"))
    )
)

vpc_cidr_output = template.add_output(
    Output(
        "VPCCIDR",
        Value=vpc_cidr_block,
        Description="VPC CIDR Block",
        Export=Export(Sub("${AWS::StackName}-cidr"))
    )
)

public_subnet_1_output = template.add_output(
    Output(
        "PublicSubnet1ID",
        Value=Ref(public_subnet_1),
        Description="Public Subnet 1 ID",
        Export=Export(Sub("${AWS::StackName}-publicsubnet1"))
    )
)

public_subnet_2_output = template.add_output(
    Output(
        "PublicSubnet2ID",
        Value=Ref(public_subnet_2),
        Description="Public Subnet 2 ID",
        Export=Export(Sub("${AWS::StackName}-publicsubnet2"))
    )
)

public_subnet_3_output = template.add_output(
    Output(
        "PublicSubnet3ID",
        Value=Ref(public_subnet_3),
        Description="Public Subnet 3 ID",
        Export=Export(Sub("${AWS::StackName}-publicsubnet3"))
    )
)

private_subnet_1_output = template.add_output(
    Output(
        "PrivateSubnet1ID",
        Value=Ref(private_subnet_1),
        Description="Private Subnet 1 ID",
        Export=Export(Sub("${AWS::StackName}-privatesubnet1"))
    )
)

private_subnet_2_output = template.add_output(
    Output(
        "PrivateSubnet2ID",
        Value=Ref(private_subnet_2),
        Description="Private Subnet 2 ID",
        Export=Export(Sub("${AWS::StackName}-privatesubnet2"))
    )
)

private_subnet_3_output = template.add_output(
    Output(
        "PrivateSubnet3ID",
        Value=Ref(private_subnet_3),
        Description="Private Subnet 3 ID",
        Export=Export(Sub("${AWS::StackName}-privatesubnet3"))
    )
)


# Generate and write template to file.
try:
    print(template.to_yaml(), file=open(template_file, "w"))
    print("Template written to file %s" % abspath(template_file))
except IOError as e:
    print("Couldn't open or write to file (%s)." % e)
