NAME = orcidhub/app
VERSION = 4.15

.PHONY: all build test tag_latest

all: build

build:
	docker build --label version=$(VERSION) -t $(NAME) .
build-dev:
	docker build --label version=$(VERSION) -f Dockerfile.dev -t $(NAME)-dev .

tag_latest: build
	docker tag $(NAME) $(NAME):$(VERSION)

tag_latest-dev: build-dev
	docker tag $(NAME)-dev $(NAME)-dev:$(VERSION)

push: tag_latest tag_latest-dev
	docker push $(NAME):$(VERSION)
	docker push $(NAME)-dev:$(VERSION)
	docker push $(NAME):latest
	docker push $(NAME)-dev:latest

push-dev: tag_latest-dev
	docker push $(NAME)-dev:$(VERSION)
	docker push $(NAME)-dev:latest
