import pulumi
from pulumi_aws import ec2, rds, s3, iam, cloudwatch

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

# Create an IAM Role for EC2
backend_role = iam.Role("backend-role",
    assume_role_policy='''{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }''')

# Attach AmazonS3ReadOnlyAccess policy
iam.RolePolicyAttachment("backend-policy",
    role=backend_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess")

# Create instance profile
backend_profile = iam.InstanceProfile("backend-profile",
    role=backend_role.name)

# Create a CloudWatch Log Group
log_group = cloudwatch.LogGroup("backend-logs",
    retention_in_days=7)

# Create an EC2 instance for the backend
backend_instance = ec2.Instance("backend-instance",
    instance_type="t2.micro",
    ami="ami-0c55b159cbfafe1f0",  # Amazon Linux 2 AMI
    iam_instance_profile=backend_profile.name,
    user_data=f"""
        #!/bin/bash
        sudo yum update -y
        sudo yum install -y nodejs npm awslogs
        npm install -g pm2

        # Configure AWS Logs
        echo "[general]
        state_file = /var/lib/awslogs/agent-state

        [/var/log/messages]
        file = /var/log/messages
        log_group_name = {log_group.name}
        log_stream_name = backend-instance
        datetime_format = %b %d %H:%M:%S" > /etc/awslogs/awslogs.conf

        # Start AWS Logs Service
        systemctl start awslogsd
    """,
    tags={"Name": "backend-server"})

# Export the important resources
pulumi.export("frontend_url", frontend_bucket.website_endpoint)
pulumi.export("db_endpoint", db_instance.endpoint)
pulumi.export("backend_ip", backend_instance.public_ip)