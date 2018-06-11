NAME = orcidhub/app
VERSION = 4.14

.PHONY: all build test tag_latest

all: build

build:
	docker build --label version=$(VERSION) -t $(NAME) .
	docker build --label version=$(VERSION) -f Dockerfile.dev -t $(NAME)-dev .

tag_latest: build
	docker tag $(NAME) $(NAME):$(VERSION)
	docker tag $(NAME)-dev $(NAME)-dev:$(VERSION)

push: tag_latest
	docker push $(NAME):$(VERSION)
	docker push $(NAME)-dev:$(VERSION)
	docker push $(NAME):latest
	docker push $(NAME)-dev:latest
