Start the FastAPI backend development server.

Launch the backend API server with hot-reload for development.

Arguments: $ARGUMENTS (optional - "docker" to use Docker, otherwise local)

Steps to execute:

For local development (default):
1. Activate virtual environment at /Users/ashishmarkanday/github/experimentation-platform/venv
2. Set environment to development: export APP_ENV=dev
3. Ensure PostgreSQL is running (check with: docker ps | grep postgres)
4. Start uvicorn server: cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
5. Report server status and URLs:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

For Docker development (if $ARGUMENTS is "docker"):
1. Check if containers are running: docker-compose ps
2. Start services: docker-compose up -d
3. View logs: docker-compose logs -f api
4. Report container status and URLs

Helpful tips:
- Use Ctrl+C to stop the local server
- Check logs for startup errors
- Verify database connection on startup
- Monitor for hot-reload confirmations when files change

Example usage:
- /start-api → start local development server
- /start-api docker → start with Docker Compose
