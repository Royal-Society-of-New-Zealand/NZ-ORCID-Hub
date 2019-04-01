NAME = orcidhub/app
VERSION = 4.23

.PHONY: all build test tag

all: build

build:
	docker build --label version=$(VERSION) -t $(NAME) .
build-dev: build
	docker build --label version=$(VERSION) -f Dockerfile.dev -t $(NAME)-dev .

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
