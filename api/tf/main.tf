provider "aws" {
  region = "us-west-2"
  profile = "default"
}

resource "aws_key_pair" "key_pair" {
  key_name   = "key_pair"
  public_key = file("~/.ssh/id_rsa.pub")
}

resource "aws_iam_role" "ec2_s3_role" {
  name = "s3_access_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "ec2_s3_policy" {
  name = "ec2_s3_policy"
  role = aws_iam_role.ec2_s3_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ],
        Resource = [
          "arn:aws:s3:::nvidia-gaming/*",
          "arn:aws:s3:::nvidia-gaming"
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject"
        ],
        Resource = [
          "arn:aws:s3:::lm-agents-ssh-key-ec2/*"
        ]
      }
    ]
  })
}


resource "aws_iam_instance_profile" "ec2_s3_instance_profile" {
  name = "ec2_s3_instance_profile"
  role = aws_iam_role.ec2_s3_role.name
}

resource "aws_security_group" "allow_traffic" {
  name        = "allow_traffic"
  description = "Allow inbound traffic for ssh and get requests"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "generative-agents-simulation" {
  ami           = "ami-01bfa15e1c92b9dab"
  instance_type = "g5.2xlarge"
  key_name      = aws_key_pair.key_pair.key_name
  vpc_security_group_ids = [aws_security_group.allow_traffic.id]
  associate_public_ip_address = true
  iam_instance_profile = aws_iam_instance_profile.ec2_s3_instance_profile.name

  root_block_device {
    volume_size = 128
    volume_type = "gp2"
  }

  user_data = <<-EOF
              #!/bin/bash
              sudo yum update -y
              sudo yum install -y git
              sudo yum install -y unzip
              sudo yum install -y docker

              #install nvidia drivers
              sudo yum install -y gcc kernel-devel-$(uname -r)
              aws s3 cp --recursive s3://nvidia-gaming/linux/latest/ .
              unzip *Cloud_Gaming-Linux-Guest-Drivers.zip -d nvidia-drivers
              chmod +x nvidia-drivers/NVIDIA-Linux-x86_64*-grid.run
              sudo ./nvidia-drivers/NVIDIA-Linux-x86_64*.run -s
              cat << EOF | sudo tee -a /etc/nvidia/gridd.conf
              vGamingMarketplace=2
              sudo curl -o /etc/nvidia/GridSwCert.txt "https://nvidia-gaming.s3.amazonaws.com/GridSwCert-Archive/GridSwCertLinux_2021_10_2.cert"
              sudo touch /etc/modprobe.d/nvidia.conf
              echo "options nvidia NVreg_EnableGpuFirmware=0" | sudo tee --append /etc/modprobe.d/nvidia.conf
              sudo reboot

              # use nvidia-smi to ensure proper driver installation
              TEST_DRIVER=$(nvidia-smi)
              if [[ $TEST_DRIVER == *"Driver Version"* ]]; then
                echo "Driver installed successfully"
              else
                echo "Driver not installed successfully"
              fi

              sudo usermod -aG docker $USER
              sudo systemctl enable docker
              sudo systemctl start docker
              docker pull vllm/vllm-openai:latest
              EOF

  tags = {
    Name = "generative-agents-simulation"
  }
}

output "ssh_command" {
  value = "ssh ec2-user@${aws_instance.generative-agents-simulation.public_ip}"
}