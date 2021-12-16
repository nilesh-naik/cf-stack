#!/usr/bin/env python3
# Generate CloudFormation template to set up database and rabbitmq
# instances for ACME.

from os.path import abspath
from troposphere import Ref, Join, Export
from troposphere import Parameter, Template, ImportValue, Tags, Output, Sub
from troposphere.ec2 import Instance

# Set filename for template.
template_file = "templates/db.yaml"

# Get AWS pseudo parameter values.
ref_stack_name = Ref("AWS::StackName")
ref_region = Ref("AWS::Region")

# Create object to generate the template.
template = Template()

template.set_version("2010-09-09")
template.set_description("Setup DB servers for ACME.")

# Add parameters for stack.
# Parameter for VPC stack name.
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

# Parameter for SSH key name.
keyname_param = template.add_parameter(
    Parameter(
        "KeyName",
        Description=("Name of an existing EC2 KeyPair to enable "
                     "SSH access to the instance"),
        Type="AWS::EC2::KeyPair::KeyName",
        ConstraintDescription="must be the name of an existing EC2 KeyPair."
    )
)

# Parameter for DB AMI ID
db_ami_param = template.add_parameter(
    Parameter(
        "DBAMI",
        Description=("Name of existing AMI to create the DB instance"),
        Type="AWS::EC2::Image::Id",
        ConstraintDescription="must be the name of an existing EC2 AMI."
    )
)

# Parameter for DB instance type
db_instancetype_param = template.add_parameter(
    Parameter(
        "InstanceType",
        Description="Database EC2 instance type",
        Type="String",
        Default="m3.medium",
        AllowedValues=["a1.medium", "a1.large", "a1.xlarge", "a1.2xlarge",
                       "a1.4xlarge", "m4.large", "m4.xlarge", "m4.2xlarge",
                       "m4.4xlarge", "m4.10xlarge", "m4.16xlarge", "m5.large",
                       "m5.xlarge", "m5.2xlarge", "m5.4xlarge", "m5.12xlarge",
                       "m5.24xlarge", "m5a.large", "m5a.xlarge", "m5a.2xlarge",
                       "m5a.4xlarge", "m5a.12xlarge", "m5a.24xlarge",
                       "m5d.large", "m5d.xlarge", "m5d.2xlarge", "m5d.4xlarge",
                       "m5d.12xlarge", "m5d.24xlarge", "t2.nano", "t2.micro",
                       "t2.small", "t2.medium", "t2.large", "t2.xlarge",
                       "t2.2xlarge", "t3.nano", "t3.micro", "t3.small",
                       "t3.medium", "t3.large", "t3.xlarge", "t3.2xlarge",
                       "c4.large", "c4.xlarge", "c4.2xlarge", "c4.4xlarge",
                       "c4.8xlarge", "c5.large", "c5.xlarge", "c5.2xlarge",
                       "c5.4xlarge", "c5.9xlarge", "c5.18xlarge", "c5d.xlarge",
                       "c5d.2xlarge", "c5d.4xlarge", "c5d.9xlarge",
                       "c5d.18xlarge", "c5n.large", "c5n.xlarge",
                       "c5n.2xlarge", "c5n.4xlarge", "c5n.9xlarge",
                       "c5n.18xlarge", "r4.large", "r4.xlarge", "r4.2xlarge",
                       "r4.4xlarge", "r4.8xlarge", "r4.16xlarge", "r5.large",
                       "r5.xlarge", "r5.2xlarge", "r5.4xlarge", "r5.12xlarge",
                       "r5.24xlarge", "r5a.large", "r5a.xlarge", "r5a.2xlarge",
                       "r5a.4xlarge", "r5a.12xlarge", "r5a.24xlarge",
                       "r5d.large", "r5d.xlarge", "r5d.2xlarge", "r5d.4xlarge",
                       "r5d.12xlarge", "r5d.24xlarge", "x1.16xlarge",
                       "x1.32xlarge", "x1e.xlarge", "x1e.2xlarge",
                       "x1e.4xlarge", "x1e.8xlarge", "x1e.16xlarge",
                       "x1e.32xlarge", "z1d.large", "z1d.xlarge",
                       "z1d.2xlarge", "z1d.3xlarge", "z1d.6xlarge",
                       "z1d.12xlarge", "d2.xlarge", "d2.2xlarge", "d2.4xlarge",
                       "d2.8xlarge", "h1.2xlarge", "h1.4xlarge", "h1.8xlarge",
                       "h1.16xlarge", "i3.large", "i3.xlarge", "i3.2xlarge",
                       "i3.4xlarge", "i3.8xlarge", "i3.16xlarge", "f1.2xlarge",
                       "f1.4xlarge", "f1.16xlarge", "g3s.xlarge", "g3.4xlarge",
                       "g3.8xlarge", "g3.16xlarge", "p2.xlarge", "p2.8xlarge",
                       "p2.16xlarge", "p3.2xlarge", "p3.8xlarge",
                       "p3.16xlarge", "p3dn.24xlarge", "m1.small", "m1.medium",
                       "m1.large", "m1.xlarge", "m3.medium", "m3.large",
                       "m3.xlarge", "m3.2xlarge", "c1.medium", "c1.xlarge",
                       "cc2.8xlarge", "c3.large", "c3.xlarge",
                       "c3.2xlarge", "c3.4xlarge", "c3.8xlarge", "m2.xlarge",
                       "m2.2xlarge", "m2.4xlarge", "cr1.8xlarge", "r3.large",
                       "r3.xlarge", "r3.2xlarge", "r3.4xlarge",
                       "r3.8xlarge", "hs1.8xlarge", "i2.xlarge", "i2.2xlarge",
                       "i2.4xlarge", "i2.8xlarge", "g2.2xlarge", "g2.8xlarge",
                       "t1.micro"],
        ConstraintDescription="must be a valid EC2 instance type."
    )
)

# Parameter for Security group.
sg_name_param = template.add_parameter(
    Parameter(
        "SecurityGroupName",
        Description=("Name of security group that will be attached to "
                     "the Database server."),
        Type="List<AWS::EC2::SecurityGroup::Id>"
    )
)

# Create DB instances.
db_instance_1 = template.add_resource(
    Instance(
        "DBServer1",
        ImageId=Ref(db_ami_param),
        InstanceType=Ref(db_instancetype_param),
        KeyName=Ref(keyname_param),
        SubnetId=ImportValue(
            Join("-", [Ref(vpc_stackname_param), "privatesubnet1"])
        ),
        SecurityGroupIds=Ref(sg_name_param),
        Tags=Tags(
            Application=ref_stack_name,
            Name=Join("-", [ref_stack_name, "instance-1"])
        )
    )
)

db_instance_2 = template.add_resource(
    Instance(
        "DBServer2",
        ImageId=Ref(db_ami_param),
        InstanceType=Ref(db_instancetype_param),
        KeyName=Ref(keyname_param),
        SubnetId=ImportValue(
            Join("-", [Ref(vpc_stackname_param), "privatesubnet2"])
        ),
        SecurityGroupIds=Ref(sg_name_param),
        Tags=Tags(
            Application=ref_stack_name,
            Name=Join("-", [ref_stack_name, "instance-2"])
        )
    )
)

db_instance_3 = template.add_resource(
    Instance(
        "DBServer3",
        ImageId=Ref(db_ami_param),
        InstanceType=Ref(db_instancetype_param),
        KeyName=Ref(keyname_param),
        SubnetId=ImportValue(
            Join("-", [Ref(vpc_stackname_param), "privatesubnet3"])
        ),
        SecurityGroupIds=Ref(sg_name_param),
        Tags=Tags(
            Application=ref_stack_name,
            Name=Join("-", [ref_stack_name, "instance-3"])
        )
    )
)

# Export Stack Output values.
db_instance_1_output = template.add_output(
    Output(
        "DBServer1",
        Value=Ref(db_instance_1),
        Description="DB Instance ID",
        Export=Export(Sub("${AWS::StackName}-instance-1"))
    )
)

db_instance_2_output = template.add_output(
    Output(
        "DBServer2",
        Value=Ref(db_instance_2),
        Description="DB Instance ID",
        Export=Export(Sub("${AWS::StackName}-instance-2"))
    )
)

db_instance_3_output = template.add_output(
    Output(
        "DBServer3",
        Value=Ref(db_instance_3),
        Description="DB Instance ID",
        Export=Export(Sub("${AWS::StackName}-instance-3"))
    )
)

# Generate and write template to file.
try:
    print(template.to_yaml(clean_up=True), file=open(template_file, "w"))
    print("Template written to file %s" % abspath(template_file))
except IOError as e:
    print("Couldn't open or write to file (%s)." % e)
