Successful builds on the master branch will be automatically built into a
docker image and pushed to Docker Hub by Travis.

To deploy this image on the web server:

	# cd /root/hsf_website
	# docker pull ukhackspacefoundation/website:latest
	# docker-compose down && docker-compose up -d

You can view logs with:
	
	# journalctl -f CONTAINER_TAG=hsf-web
