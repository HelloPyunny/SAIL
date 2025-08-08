# SAIL (Summer of AI Lab) Project - Personalized Adventure Game

## Team Black Hawk

A dynamic, AI-powered adventure game that creates personalized experiences based on player interactions. Built with FastAPI backend and Godot Game Engine.

## 🎮 Overview

This Game is an 8-stage interactive adventure that adapts to each player's personality, preferences, and background. The game uses AI to generate dynamic NPC responses, personalized map recommendations, and creates unique storylines for every player.

### Key Features

- **AI-Powered NPCs**: Dynamic conversations using OpenAI GPT-4
- **Personalized Maps**: AI-generated map recommendations based on player preferences
- **8-Stage Progression**: From tutorial to final boss battle
- **Real-time Adaptation**: Game content adapts based on player information
- **Vector Database**: Persistent conversation history using Pinecone
- **Cross-Platform**: Godot-based frontend with modern pixel art assets

## 🏗️ Architecture

### Backend (FastAPI)
- **GameManager**: Core game state and session management
- **NPCService**: AI-powered NPC response generation
- **StageManager**: Stage progression and completion logic
- **MapRecommender**: Personalized map generation
- **VectorStore**: Conversation history management with Pinecone

### Frontend (Godot 4.4)
- **2D Pixel Art Graphics**: Rich visual assets and animations
- **Real-time Communication**: HTTP-based API integration
- **Dynamic UI**: Adaptive dialogue system and health panels
- **Multi-character Support**: Player and NPC interaction systems

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Godot 4.4+
- OpenAI API Key
- Pinecone API Key
- AWS S3 Bucket (for map storage)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the `backend/` directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_ENVIRONMENT=us-east-1-aws
   AWS_ACCESS_KEY_ID=your_aws_access_key_here
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
   AWS_REGION=ap-northeast-2
   S3_BUCKET_NAME=your_s3_bucket_name_here
   ```

5. **Start the server:**
   ```bash
   python main.py
   ```

   The server will run on `http://localhost:8000`

### Frontend Setup

1. **Open Godot 4.4+**
2. **Import the project:**
   - Open Godot
   - Click "Import"
   - Select the `frontend/` directory
   - Click "Import & Edit"

3. **Run the game:**
   - Press F5 or click the "Play" button
   - The game will connect to the backend automatically

## 🎯 Game Stages

### 1. Tutorial
- Collect basic player information (name, age, location, occupation)
- Gather personality traits and interests
- Set life goals

### 2. Stage 2 - Fear Collection
- Explore player fears and anxieties
- Build emotional depth for story development

### 3. Stage 3 - Background Story
- Collect personal history and background
- Gather additional context for personalization

### 4. Stages 4-7 - Adventure Progression
- Dynamic adventure stages with personalized content
- AI-generated map recommendations
- NPC interactions based on collected information

### 5. Stage 8 - Final Boss
- Culminating battle using all collected player information
- Personalized boss encounter and resolution

## 🔧 API Endpoints

### Core Game Endpoints

- `POST /game/new` - Create a new game session
- `POST /game/chat` - Interact with NPCs
- `POST /game/next-stage/{player_id}` - Advance to next stage
- `POST /game/enemy-defeated/{player_id}` - Notify enemy defeat
- `GET /game/generated-maps` - Retrieve AI-generated maps
- `GET /health` - Health check endpoint

### Example API Usage

```bash
# Create new game
curl -X POST http://localhost:8000/game/new

# Chat with NPC
curl -X POST http://localhost:8000/game/chat \
  -H "Content-Type: application/json" \
  -d '{"player_id": "your_player_id", "message": "Hello, I am John from Seoul"}'
```

## 🎨 Game Features

### AI Integration
- **Dynamic NPC Responses**: Context-aware conversations using GPT-4
- **Personalized Content**: Game adapts based on player information
- **Intelligent Map Generation**: AI-recommended maps based on preferences

### Visual Assets
- **Pixel Art Graphics**: High-quality 2D sprites and animations
- **Multiple Character Types**: Warriors, archers, lancers with different color variants
- **Rich Environment**: Buildings, terrain, decorations, and interactive elements
- **Animated Effects**: Fire effects, projectiles, and environmental animations

### Gameplay Systems
- **Health Management**: Real-time health tracking and UI
- **Combat System**: Enemy encounters and defeat mechanics
- **Stage Progression**: Seamless transitions between game stages
- **Dialogue System**: Interactive conversation interface

## 🛠️ Development

### Project Structure

```
SAIL/
├── backend/                 # FastAPI server
│   ├── services/           # Core game services
│   ├── utils/              # Utility functions
│   ├── vector_db/          # Database integration
│   └── static/             # Generated content
├── frontend/               # Godot game client
│   ├── assets/             # Game assets and sprites
│   ├── player/             # Player character scripts
│   ├── enemy/              # Enemy AI and mechanics
│   ├── stages/             # Game stage scenes
│   └── UI/                 # User interface components
└── docs/                   # Documentation
```

### Key Components

#### Backend Services
- **GameManager**: Orchestrates game flow and state management
- **NPCService**: Handles AI-powered NPC interactions
- **MapRecommender**: Generates personalized map suggestions
- **StageManager**: Manages stage progression and completion

#### Frontend Systems
- **GameAPI**: HTTP communication with backend
- **EnemyManager**: Enemy spawning and management
- **DialogueBox**: Interactive conversation system
- **HealthPanel**: Player status display

## 🔒 Security & Configuration

### Environment Variables
All sensitive configuration is managed through environment variables:
- API keys for external services
- Database credentials
- Server configuration

### Debug Mode
For development without external services:
```env
GAME_DEBUG_MODE=true
```

## 🚀 Deployment

### Production Considerations
- Secure CORS settings
- Implement authentication
- Add rate limiting
- Enhanced error handling
- Monitoring and logging
- Environment-specific configurations

## 🆘 Support

For issues and questions:
- Check the `BACKEND_SETUP_GUIDE.md` for detailed setup instructions
- Review the API documentation in the codebase
- Examine the comprehensive logging system for debugging

## 🎮 Game Controls

- **WASD**: Movement
- **Chat Box**: Interact with NPCs
- **Mouse**: UI interaction
- **Shift**: Run (if implemented)

---

**SAIL** - Where every adventure is uniquely yours!
