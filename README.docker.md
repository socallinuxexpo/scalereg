# scalereg in a container

The included Dockerfile is enough to get a simple C7 container running apache
and listening SSL-less on port 80. From there you can start the container with
port forwarding on localhost and then wrap that in SSL using nginx or apache or
whatever else.

For various reasons, it is designed to be bind-mounting in the code from the
host.

## Build the docker

Build the docker container with:

```shell
docker build  --load -t scalereg .
```

Or tag it and push it to your preferred registry.

## Run it

Run the container with something like:

```shell
PATH_TO_SCALE_REG_REPO=...
docker run -dit -v $PATH_TO_SCALE_REG_REPO:/var/www/django --name scalereg -p 127.0.0.1:8000:80 scalereg
```

How you forward :443 to localhost:8000 is up to you.
