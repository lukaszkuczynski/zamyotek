download:
	aws s3 sync s3://sagemaker-s3-luk/events/ /tmp/tensorflow_events --exclude="*" --include "*tfevents*"

showboard:
	tensorboard --logdir /tmp/tensorflow_events
