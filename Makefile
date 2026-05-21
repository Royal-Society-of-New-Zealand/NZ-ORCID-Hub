NAME = orcidhub/app
VERSION = 8.0
PROXY_PORT = 3128

.PHONY: all build build-dev build-test build-via-proxy tag tag-dev push push-dev clean

all: build

build:
	docker build \
		--target orcidhub --label version=$(VERSION) -t $(NAME) .

build-dev: build
	docker build \
		--target orcidhub-dev --label version=$(VERSION) -f Dockerfile.dev -t $(NAME)-dev .

build-test:
	docker build -f Dockerfile.test -t $(NAME)-test .

build-via-proxy: squid
	docker build \
		--build-arg http_proxy=http://$(PROXY_IP):$(PROXY_PORT) \
		--target orcidhub --label version=$(VERSION) -t $(NAME) .

squid:
	mkdir -p $(PWD)/.squid/cache
	docker inspect squid &>/dev/null || docker run --name squid -d \
	  --hostname squid \
	  -v $(PWD)/.squid/cache:/var/spool/squid \
	  -v $(PWD)/conf/squid.conf:/etc/squid/squid.conf \
	   -p 3128:3128 -p 3129:3129 \
	  sameersbn/squid:3.5.27-2
	until docker inspect --format '{{.State.Status}}' squid | grep -m 1 "running"; do sleep 1 ; done
	until [ -n "$$(docker inspect --format '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' squid)" ]; do sleep 1 ; done
	$(eval PROXY_IP=$(shell sh -c "docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' squid"))

show_proxy: squid
	$(eval PROXY_IP=$(shell sh -c "docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' squid"))
	@echo Proxy IP: $(PROXY_IP)
	@echo export http_proxy=http://$(PROXY_IP):$(PROXY_PORT) https_proxy=http://$(PROXY_IP):$(PROXY_PORT) ftp_proxy=http://$(PROXY_IP):$(PROXY_PORT)

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
	-docker rm -f squid
	-docker network rm build-net
