# Applied AI Engineering, Volume IV, Chapter 5
# Hands-on Lab: Containerized AI API Service
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# Build and start the service
export OPENAI_API_KEY=your-api-key-here
docker compose up --build -d

# Wait for health check to pass
docker compose ps   # Status should show "healthy"

# Run smoke tests
chmod +x scripts/smoke_test.sh
./scripts/smoke_test.sh http://localhost:8000

# View logs
docker compose logs -f ai-api

# Shut down
docker compose down
