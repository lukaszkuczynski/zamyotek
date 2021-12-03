build:
	pip install --target ./package -r requirements.txt

zip: 
	zip my-deployment-package.zip lambda_function.py
	zip -r my-deployment-package.zip lambda_function.py
	cd ./package && zip -r ../my-deployment-package.zip .

deploy: zip
	aws lambda update-function-code --function-name alexa_zamyoteck_run --zip-file fileb://my-deployment-package.zip