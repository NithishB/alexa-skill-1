ssh-keyscan -H ec2-3-235-228-238.compute-1.amazonaws.com
scp -i "skill-1.pem" /Users/moudhgn/.aws/credentials ubuntu@ec2-3-235-228-238.compute-1.amazonaws.com:/home/ubuntu/.aws/
scp -i "skill-1.pem" /Users/moudhgn/.aws/config ubuntu@ec2-3-235-228-238.compute-1.amazonaws.com:/home/ubuntu/.aws/
scp -i "skill-1.pem" -r ./* ubuntu@ec2-3-235-228-238.compute-1.amazonaws.com:/home/ubuntu/checklist-skill/