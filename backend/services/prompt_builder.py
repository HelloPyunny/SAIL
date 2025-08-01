from typing import Dict, List
from utils.game_state import GameState
from services.stage_manager import StageManager

class PromptBuilder:
    """manage prompt generation"""
    
    def __init__(self, stage_manager: StageManager):
        self.stage_manager = stage_manager
        
        # NPC personality
        self.npc_personality = """
        you are a mysterious NPC that guides adventurers.
        you are friendly and warm, and genuinely interested in the player's personal stories.
        you understand the player's background and goals, and provide personalized responses accordingly.
        you always maintain a encouraging and positive attitude, and help the player grow.
        
        important: focus only on collecting information required for the current stage, and do not mention stages or maps that the player has not yet reached.
        stage transition is only possible through the "next stage" button, and only then will a new map and adventure begin.
        """
    
    def build_system_prompt(self, game_state: GameState, player_history: List[Dict]) -> str:
        """build system prompt"""
        
        # get stage instructions
        stage_instructions = self.stage_manager.get_stage_instructions(game_state.current_stage)
        
        # build player history text
        history_text = ""
        if player_history:
            history_text = "\n".join([item["content"] for item in player_history[-5:]])
        
        system_prompt = f"""
        {self.npc_personality}
        
        {stage_instructions}
        
        current game state:
        - stage: {game_state.current_stage.value}
        - player info: {game_state.player_info.to_dict()}
        - current map: {game_state.current_map or "none"}
        - boss goal: {game_state.boss_goal or "not set"}
        - life goal: {game_state.player_info.life_goal or "not set"}
        
        player history:
        {history_text}
        
        stage-specific approach:
        - 1st stage (tutorial): focus only on basic info collection (name, age, location, occupation, likes/hobbies, personality, life goal)
        - 2nd stage: focus only on fear info collection (fears)
        - 3rd stage: focus only on background info collection (background)
        - 4-7 stages: focus on story expansion and character development
        - 8th stage (boss): finish the journey meaningfully through a final battle with the final boss related to the player's life goal, and congratulate the player's growth. naturally emphasize that the final battle is the last challenge for the player to achieve their life goal.
        
        important constraints:
        - focus only on collecting information required for the current stage
        - do not mention stages or maps that the player has not yet reached
        - stage transition is only possible through the "next stage" button
        
        maintain story continuity:
        - mention the player's experience and growth from previous stages to maintain story continuity
        - create a meaningful journey related to the player's personal goal
        - naturally emphasize that each stage is an important part of the overall story
        - naturally reflect the player's growth and change continuously
        
        basic instructions:
        1. always maintain a friendly and encouraging tone
        2. genuinely show interest in the player's personal stories
        3. provide personalized responses reflecting the player's background and goals
        4. use an approach appropriate for the purpose of each stage
        5. naturally lead the conversation and enrich the player's experience
        6. naturally emphasize the continuity of the story and the player's growth
        7. in 4-7 stages, focus on story expansion and character development to enrich the player's journey.
        """
        
        return system_prompt
    
    def build_user_prompt(self, player_message: str, game_state: GameState) -> str:
        """build user prompt"""
        
        # recent conversation history (max 10, use all if less than 10)
        recent_conversations = game_state.conversation_history[-min(10, len(game_state.conversation_history)):]
        
        conversation_context = ""
        if recent_conversations:
            conversation_context = "\n".join([
                f"{conv['speaker']}: {conv['message']}" 
                for conv in recent_conversations
            ])
        
        user_prompt = f"""
        recent 10 conversations:
        {conversation_context}
        
        player's new message: {player_message}
        
        consider the above conversation context to generate a natural and personalized response.
        """
        
        return user_prompt
    
    def build_stage_intro_prompt(self, game_state: GameState, player_history: List[Dict]) -> str:
        """build stage intro prompt"""
        
        # build history context
        history_context = ""
        if player_history:
            history_context = "\n".join([item["content"] for item in player_history])
        
        system_prompt = f"""
        you are an NPC guide for a personalized adventure game. based on the player's personal information and conversation history, you need to lead the story.

NPC personality:
{self.npc_personality}

current game state:
- stage: {game_state.current_stage.value} ({game_state.current_stage.name})
- player name: {game_state.player_info.name}
- current map: {game_state.current_map or 'none'}

recent conversation history:
{history_context}

requirements:
1. use the player's personal information to write a personalized message
2. explain why you recommended this map
3. naturally emphasize the connection between the player's interests, personality, and the map
4. maintain a tone that leads the story
5. provide a clear direction for what the player should do
6. use descriptive expressions to enhance immersion
7. write naturally in English
8. 200-300 characters in length, if possible, if not, write as much as possible

the message should be friendly and adventurous, and motivate the player to move to the next stage.
"""
        
        return system_prompt 