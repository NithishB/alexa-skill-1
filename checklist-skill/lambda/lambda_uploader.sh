functionName="skill1"
s3Bucket="jingle-skill-bucket"
s3Key="skill_1.zip"
zipName="./skill_1.zip"

if [ -d "packages" ]; then rm -rf packages; fi
rm -f ${zipName} ?
mkdir -p packages
cp -R skill_env/* packages

(
cd packages
cp -R ../codes .
zip -r9 ../${zipName} .
)

aws s3 cp ${zipName} s3://${s3Bucket}
aws lambda update-function-code --function-name ${functionName} --s3-bucket ${s3Bucket} --s3-key ${s3Key}