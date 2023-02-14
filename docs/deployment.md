# Deployment

Successful builds on the `main` branch will be automatically built as a
docker image and pushed to github container registry. This is then
automatically deployed by watchtower.

You can view logs with:
	
	# journalctl -f CONTAINER_TAG=hsf-web
