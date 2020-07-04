functionName="skill1"
s3Bucket="jingle-skill-bucket"
s3Key="skill_1.zip"
zipName="./skill_1.zip"

cp -r *.py skill_env/

(
cd skill_env
zip -r9 ../${zipName} .
)

aws s3 sync . s3://jingle-skill-bucket
aws lambda update-function-code --function-name ${functionName} --s3-bucket ${s3Bucket} --s3-key ${s3Key}