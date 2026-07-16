.PHONY: build up down clean restart logs status

# pre-build the background server template image
build:
	sudo docker build -t server_image:latest ./server

#sign up the load balancer orchestrator
up: build
	sudo docker compose up -d

# gracefully stop and tear down the cluster containers and internal network
down:
	@echo "Stopping the load balancer orchestrator first to disable heartbeats..."
	-sudo docker compose stop
	@echo "Stopping and removing all remaining backend server replicas..."
	-sudo docker ps -a --filter "name=server-" -q | xargs -r sudo docker stop
	-sudo docker ps -a --filter "name=server-" -q | xargs -r sudo docker rm
	@echo "Tearing down networks and compose structures..."
	sudo docker compose down

# view log outputs from the load balancer app
logs:
	sudo docker logs -f load_balancer

# check active status of running containers
status:
	sudo docker ps

#complete reset: wipe down containers, network footprints, and  cached layers
clean: down
	sudo docker system prune -f
	sudo docker rmi lb_image:latest server_image:latest 2>/dev/null || true

#quick restart macro
restart: down up
