NAME = orcidhub/app
VERSION = 7.0

.PHONY: all build test tag

all: build
# -v $(PWD)/conf:/etc/squid \
# -v $(PWD)/.squid/cache:/var/spool/squid \

squid:
	docker network inspect build-net &>/dev/null || docker network create build-net
	# docker volume create squid-cache || true
	mkdir -p $(PWD)/.squid/cache
	docker run --name squid -d \
	  --hostname squid \
	  --network build-net \
	  -v $(PWD)/.squid/cache:/var/spool/squid \
	  -v $(PWD)/conf/squid.conf:/etc/squid/squid.conf \
	   -p 3128:3128 -p 3129:3129 \
	  sameersbn/squid:3.5.27-2

build:
	DOCKER_BUILDKIT=1 docker build --squash \
					--network build-net --build-arg http_proxy=http://squid:3128 \
					--target orcidhub --label version=$(VERSION) -t $(NAME) .
build-dev: build
	DOCKER_BUILDKIT=1 docker build --squash \
					--network build-net --build-arg http_proxy=http://squid:3128 \
					--target orcidhub --label version=$(VERSION) -f Dockerfile.dev -t $(NAME)-dev .

tag: build
	docker tag $(NAME) $(NAME):$(VERSION)

tag-dev: build-dev
	docker tag $(NAME)-dev $(NAME)-dev:$(VERSION)

push: tag tag-dev
	docker push $(NAME):$(VERSION)
	docker push $(NAME)-dev:$(VERSION)
	docker push $(NAME):latest
	docker push $(NAME)-dev:latest

push-dev: tag-dev
	docker push $(NAME)-dev:$(VERSION)
	docker push $(NAME)-dev:latest


clean:
	docker rm -f squid
	docker network rm build-net
