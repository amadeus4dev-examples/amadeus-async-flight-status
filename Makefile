SERVICES = monitor notifier subscriber

all: build

build: docker-compose.yaml
	docker-compose build

run:
	docker-compose up --remove-orphans

broker:
	docker run --rm --name mqtt -p 1883:1883 -p 9001:9001 -ti toke/mosquitto

docs: $(SERVICES)
	$(foreach service, $(SERVICES), make -C $(service);)

.PHONY: build run broker docs
