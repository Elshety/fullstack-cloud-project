import pulumi
from pulumi_aws import ec2, rds, s3, iam

# Create an S3 bucket for the frontend
frontend_bucket = s3.Bucket("frontend-bucket",
    website=s3.BucketWebsiteArgs(
        index_document="index.html",
        error_document="index.html"
    ),
    acl="public-read")

# Create a security group for RDS
db_security_group = ec2.SecurityGroup("db-security-group",
    description="Allow access to RDS",
    ingress=[ec2.SecurityGroupIngressArgs(
        protocol="tcp",
        from_port=3306,
        to_port=3306,
        cidr_blocks=["0.0.0.0/0"]
    )])

# Create an RDS instance
db_instance = rds.Instance("db-instance",
    engine="mysql",
    instance_class="db.t2.micro",
    allocated_storage=20,
    username="admin",
    password=pulumi.Config().require_secret("db_password"),
    skip_final_snapshot=True,
    publicly_accessible=True,
    vpc_security_group_ids=[db_security_group.id])

# Create an EC2 instance for the backend
backend_instance = ec2.Instance("backend-instance",
    instance_type="t2.micro",
    ami="ami-0c55b159cbfafe1f0",  # Amazon Linux 2 AMI
    user_data="""
        #!/bin/bash
        sudo yum update -y
        sudo yum install -y nodejs npm
        npm install -g pm2
        """,
    tags={"Name": "backend-server"})

# Export the important resources
pulumi.export("frontend_url", frontend_bucket.website_endpoint)
pulumi.export("db_endpoint", db_instance.endpoint)
pulumi.export("backend_ip", backend_instance.public_ip)