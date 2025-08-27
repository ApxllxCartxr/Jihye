# Development: fast reload

This project includes a development Docker image that auto-restarts the bot when Python files change.

Files added:

- `Dockerfile.dev` — development image using `watchdog` to auto-restart on file changes.
- `docker-compose.dev.yml` — a compose file that mounts the project into `/app` and runs the dev image.

How to use (from project root):

1. Build and start in one step:

```bash
docker compose -f docker-compose.dev.yml up --build
```

1. Run detached:

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

1. View logs:

```bash
docker compose -f docker-compose.dev.yml logs -f
```

Notes:

- The dev service mounts your working directory into the container, so file changes are reflected immediately inside the container.
- If you change `requirements.txt` you must rebuild the image because dependencies are installed at build time.
- For production, use the original `Dockerfile` and do not mount source into the image.
