# SAIL Backend Server Setup Guide

## Overview

The SAIL (Personalized Adventure Game) backend is a FastAPI-based REST API server that powers an 8-stage personalized adventure game. The system uses AI to generate dynamic responses, personalized map recommendations, and manages player progression through various stages.

## Architecture Components

### Core Services

- **GameManager**: Manages overall game state and player sessions
- **NPCService**: Generates AI-powered NPC responses using OpenAI GPT-4
- **StageManager**: Handles stage progression logic and completion conditions
- **InfoCollector**: Extracts and processes player information from conversations
- **MapRecommender**: Generates personalized map recommendations
- **VectorStore**: Manages conversation history using Pinecone vector database

### Game Flow

The game consists of 8 stages:

1. **Tutorial**: Collect basic player info (name, age, location, occupation, personality, likes, life goal)
2. **Stage 2**: Collect fear information
3. **Stage 3**: Collect background/history information
4. **Stages 4-7**: Progressive adventure stages with NPC interactions
5. **Stage 8 (Boss)**: Final boss battle and game completion

## Prerequisites

### Required API Keys and Services

- **OpenAI API Key**: For GPT-4 powered NPC responses
- **Pinecone API Key**: For vector database (conversation storage)
- **AWS Credentials**: For S3 bucket (map image storage)

### Python Requirements

- Python 3.8+
- Virtual environment (recommended)

## Installation & Setup

### 1. Clone and Navigate to Backend

```bash
cd backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the `backend/` directory with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-east-1-aws

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=ap-northeast-2
S3_BUCKET_NAME=your_s3_bucket_name_here

# Optional: Development Settings
GAME_DEBUG_MODE=false
GAME_LOG_LEVEL=INFO
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

#### How to Get API Keys:

**OpenAI API Key:**

1. Visit https://platform.openai.com/api-keys
2. Create a new secret key
3. Ensure you have sufficient credits for GPT-4 usage

**Pinecone API Key:**

1. Visit https://app.pinecone.io/
2. Create an account and project
3. Generate an API key from the dashboard

**AWS S3 Setup:**

1. Create an AWS account and S3 bucket
2. Generate IAM credentials with S3 read/write permissions
3. Note your bucket name and region

### 5. Debug Mode (Optional)

For development/testing without external services, set:

```env
GAME_DEBUG_MODE=true
```

This will use dummy values for API keys and skip external service calls.

## Running the Server

### Start the Server

```bash
python main.py
```

The server will start on `http://localhost:8000` by default.

### Verify Installation

Check the health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "Personalized Adventure Game API"
}
```

## API Endpoints

### Core Game Endpoints

#### 1. Create New Game

```http
POST /game/new
```

**Response:**

```json
{
  "player_id": "uuid-string",
  "welcome_message": "Hello, brave adventurer!..."
}
```

#### 2. Chat with NPC

```http
POST /game/chat
Content-Type: application/json

{
  "player_id": "uuid-string",
  "message": "Hello, I'm John from Seoul"
}
```

**Response:**

```json
{
  "npc_response": "Nice to meet you John!...",
  "stage_progress": {"stage_completed": false},
  "map_recommendation": null,
  "game_completed": false,
  "current_stage": 1,
  "player_info": {...}
}
```

#### 3. Advance to Next Stage

```http
POST /game/next-stage/{player_id}
```

#### 4. Enemy Defeated Notification

```http
POST /game/enemy-defeated/{player_id}
```

#### 5. Get Generated Maps

```http
GET /game/generated-maps
```

### Testing the API

#### Quick Test Sequence:

```bash
# 1. Create a new game
curl -X POST http://localhost:8000/game/new

# 2. Extract player_id from response and chat
curl -X POST http://localhost:8000/game/chat \
  -H "Content-Type: application/json" \
  -d '{"player_id": "YOUR_PLAYER_ID", "message": "Hi, I am John, 25 years old from Seoul"}'

# 3. Check health
curl http://localhost:8000/health
```

## Code Structure Review

### Key Files to Review:

#### 1. `main.py` - FastAPI Application

- API endpoint definitions
- CORS configuration
- Request/response models
- Error handling

#### 2. `config.py` - Configuration Management

- Environment variable validation
- Debug mode handling
- Setup instructions display

#### 3. `services/game_manager.py` - Game Logic Core

- Game state management
- Player progression logic
- Stage advancement handling
- Map recommendation integration

#### 4. `services/npc_service.py` - AI Integration

- OpenAI GPT-4 integration
- Response generation logic
- Prompt building and management

#### 5. `utils/game_state.py` - Data Models

- Game state data structures
- Player information models
- Stage progression tracking

#### 6. `vector_db/vector_store.py` - Database Integration

- Pinecone vector database integration
- Conversation storage and retrieval
- Context management

## Troubleshooting

### Common Issues:

#### 1. Environment Variable Errors

```
Error: required environment variables are not set: OPENAI_API_KEY
```

**Solution:** Ensure all required environment variables are set in `.env` file

#### 2. Pinecone Connection Issues

```
Error: PINECONE_API_KEY and OPENAI_API_KEY are required
```

**Solution:** Verify Pinecone API key and check internet connectivity

#### 3. OpenAI API Errors

```
Error: Model gpt-4.1 not found
```

**Solution:** Check OpenAI API key validity and account credits

#### 4. Port Already in Use

```
Error: [Errno 48] Address already in use
```

**Solution:** Kill process using port 8000 or change port in config

### Debug Commands:

```bash
# Check if requirements are installed
pip list

# Verify environment variables
python -c "from config import Config; Config.validate()"

# Test OpenAI connection
python -c "from openai import OpenAI; client = OpenAI(); print('OpenAI OK')"
```

## Development Notes

### Code Quality Considerations:

- The codebase uses proper separation of concerns with distinct service layers
- Error handling is implemented but could be enhanced with more specific exception types
- Logging is basic and could benefit from structured logging
- The system uses Pydantic models for data validation

### Performance Considerations:

- Vector database operations are asynchronous
- OpenAI API calls may introduce latency
- Consider implementing caching for frequently accessed data
- Monitor API rate limits for external services

### Security Notes:

- API keys are properly loaded from environment variables
- CORS is currently set to allow all origins (adjust for production)
- No authentication is implemented (consider adding for production)

## Production Deployment

### Before Production:

1. **Secure CORS settings**: Restrict allowed origins
2. **Add authentication**: Implement proper user authentication
3. **Enhanced logging**: Add structured logging and monitoring
4. **Rate limiting**: Implement API rate limiting
5. **Error handling**: Add comprehensive error handling and user-friendly error messages
6. **Health checks**: Implement detailed health checks for dependencies
7. **Environment separation**: Use different configurations for dev/staging/prod

### Recommended Production Setup:

- Use Docker containers for consistent deployment
- Implement proper secrets management
- Set up monitoring and alerting
- Use a reverse proxy (nginx) for load balancing
- Implement database connection pooling

## Support

For issues related to:

- **Game Logic**: Review `services/game_manager.py` and `services/stage_manager.py`
- **AI Responses**: Check `services/npc_service.py` and OpenAI API configuration
- **Database Issues**: Examine `vector_db/vector_store.py` and Pinecone configuration
- **API Issues**: Look at `main.py` endpoint definitions

The codebase includes comprehensive logging that will help identify specific issues during runtime.
