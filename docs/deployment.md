To deploy, you'll need access to the [Docker Hub team](https://hub.docker.com/u/ukhackspacefoundation/).

Run `make deploy` to build a production Docker image and upload it to Docker Hub.

On the web server:

	# cd /root/hsf_website
	# docker pull ukhackspacefoundation/website:latest
	# docker-compose down && docker-compose up -d

You can view logs with:
	
	# journalctl -f CONTAINER_TAG=hsf-web
