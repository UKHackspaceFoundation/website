FROM python:3.7-alpine AS base
WORKDIR /usr/src/app

RUN pip install --no-cache-dir pipenv \
    && apk add --no-cache postgresql-client

# We need a build environment for some of our python dependencies.
# This mess is mostly from the upstream python-alpine dockerfile.
RUN apk add --no-cache --virtual .build-deps  \
		bzip2-dev \
		coreutils \
		dpkg-dev dpkg \
		expat-dev \
		findutils \
		gcc \
		gdbm-dev \
		libc-dev \
		libffi-dev \
		libnsl-dev \
		libressl-dev \
		libtirpc-dev \
		linux-headers \
		make \
		ncurses-dev \
		pax-utils \
		readline-dev \
		sqlite-dev \
		tcl-dev \
		tk \
		tk-dev \
		util-linux-dev \
		xz-dev \
		zlib-dev \
		postgresql-dev

EXPOSE 8000
ENTRYPOINT ["pipenv", "run"]

# The above commands run for both dev and production builds. Below we define
# targets so we can customise dev and production images.

FROM base AS dev

# No need to copy the whole app in here, as we'll be mounting it in.
COPY Pipfile ./
COPY Pipfile.lock ./
RUN pipenv sync --dev
CMD ["./docker/start_dev.sh"]

FROM base AS prod
COPY . .
RUN pipenv sync && apk del .build-deps
CMD ["./docker/start_prod.sh"]
