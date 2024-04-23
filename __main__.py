import pulumi
import pulumi_aws as aws
import base64




# VPC creation
vpc = aws.ec2.Vpc("my-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True)


# Create an Internet Gateway for the VPC
internet_gateway = aws.ec2.InternetGateway("app-gateway",
    vpc_id=vpc.id
)

# Public Subnet creation
subnet = aws.ec2.Subnet("my-subnet", vpc_id=vpc.id, cidr_block="10.0.1.0/24", map_public_ip_on_launch=True)

# Create a Route Table with routes for a public subnet
route_table = aws.ec2.RouteTable("app-route-table",
    vpc_id=vpc.id,
    routes=[{
        'cidr_block': '0.0.0.0/0',
        'gateway_id': internet_gateway.id
    }]
)

# Associate the Subnet with the Route Table
route_table_association = aws.ec2.RouteTableAssociation("app-route-table-assoc",
    route_table_id=route_table.id,
    subnet_id=subnet.id
)

# Security group to allow port 9898
security_group = aws.ec2.SecurityGroup('app-sg',
    description='Allow access to My App',
    vpc_id=vpc.id,
    ingress=[
        {
        'protocol': 'tcp',
        'from_port': 80,
        'to_port': 80,
        'cidr_blocks': ['0.0.0.0/0'],
    },
    {
        'protocol': 'tcp',
        'from_port': 22,
        'to_port': 22,
        'cidr_blocks': ['0.0.0.0/0'],
    },
    {
        'protocol': 'tcp',
        'from_port': 9898,
        'to_port': 9898,
        'cidr_blocks': ['0.0.0.0/0'],
    }
    ],
    egress=[{
        'protocol': '-1',
        'from_port': 0,
        'to_port': 0,
        'cidr_blocks': ['0.0.0.0/0'],
    }]
)

# Launch Template creation

user_data = """#!/bin/bash
                sudo yum update -y
                sudo yum install -y docker
                sudo service docker start
                sudo yum install -y git
                sudo git clone https://github.com/stefanprodan/podinfo.git
                sudo docker run -d -p 80:9898 --name podinfo podinfodocker_podinfo"""

# BASE64-Kodierung der Benutzerdaten
encoded_user_data = base64.b64encode(user_data.encode('utf-8')).decode('utf-8')

# Launch Template creation
ec2_launch_template = aws.ec2.LaunchTemplate("my-launch-template",
    name="my-launch-template",
    image_id="ami-0f673487d7e5f89ca",
    instance_type="t2.micro",
    key_name="my-key-pair",
    network_interfaces=[{
        "associate_public_ip_address": True,
        "device_index": 0,
        "subnet_id": subnet.id,
        "security_groups": [security_group.id],
    }],
    user_data=encoded_user_data) 


# EC2 Instance creation
ec2_instance = aws.ec2.Instance("pulumi-podinfo",
    launch_template={
        "id": ec2_launch_template.id,
    },
    tags={
        "Name": "pulumi-podinfo",
    })

# Export the Instance ID and public IP
pulumi.export("instance_id", ec2_instance.id)
pulumi.export("instance_public_ip", ec2_instance.public_ip)
