from typing import Dict, List, Any
from utils.game_state import GameState, PlayerInfo
from openai import OpenAI
import os
from dotenv import load_dotenv
import json

load_dotenv()

class InfoCollector:
    """manage player info collection"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def extract_player_info(self, player_message: str, game_state: GameState) -> Dict[str, Any]:
        """extract information from player message. extract accurate information for each stage."""
        
        current_stage = game_state.current_stage
        
        # system prompt for each stage - to extract more accurate information
        if current_stage.value == 1:  # tutorial
            system_prompt = """
            extract basic and additional information from the player's message. in the tutorial stage, collect the following information:
            
            basic extraction fields:
            - name (name)
            - age (age, only numbers)
            - location (location)
            - occupation (occupation, including student)
            - personality_traits (personality traits, separated by commas)
            - likes (likes/hobbies/things they like, separated by commas)
            - life_goal (life goal)
            - extra_info (all additional information not covered by the above fields, returned as an array)
            
            attention:
            1. only extract information explicitly mentioned in the message
            2. do not include simple evaluations like "good", "great", "okay" in likes
            3. likes should only include specific activities, hobbies, and interests (e.g. "game", "music", "movie", "programming")
            4. extra_info should include all meaningful information not covered by the basic fields
            5. always return valid JSON format only
            
            extra_info examples:
            - "I often meet with friends"
            - "I'm busy these days"
            - "I like spending time alone at home"
            - "I like learning new things"
            """
        elif current_stage.value == 2:  # stage 2
            system_prompt = """
            extract information related to fears and additional information from the player's message. in stage 2, collect the following information:
            
            extraction fields:
            - fears (fears, separated by commas)
            - personality_traits (personality traits mentioned for the first time)
            - likes (new interests mentioned)
            - extra_info (all additional information not covered by the above fields, returned as an array)
            
            attention:
            1. fears should only include content expressed as "afraid", "worried", "scary", "anxious" etc.
            2. extra_info should include all meaningful information not covered by the basic fields
            3. always return valid JSON format only
            """
        elif current_stage.value == 3:  # stage 3
            system_prompt = """
            extract background information and additional information from the player's message. in stage 3, collect the following information:
            
            extraction fields:
            - background (background story - education, experience, past experiences, family relationships, etc.)
            - personality_traits (personality traits mentioned for the first time)
            - likes (new interests mentioned)
            - extra_info (all additional information not covered by the above fields, returned as an array)
            
            attention:
            1. background should only include past experiences, education background, growth process, important events, etc.
            2. extra_info should include all meaningful information not covered by the basic fields
            3. always return valid JSON format only
            """
        else:  # stage 4-8
            system_prompt = """
            extract new information and additional information from the player's message. in stage 4 and later, collect the following information:
            
            extraction fields:
            - personality_traits (personality traits mentioned for the first time)
            - likes (new interests mentioned)
            - fears (new fears mentioned)
            - background (new background information mentioned)
            - extra_info (all additional information not covered by the above fields, returned as an array)
            
            attention:
            1. only extract information that is actually mentioned
            2. extra_info should include all meaningful information not covered by the basic fields
            3. always return valid JSON format only
            4. do not miss any information, including conversation content, emotions, opinions, experiences, etc.
            
            extra_info examples:
            - "I'm feeling good"
            - "This game is fun"
            - "My friends are really nice people"
            - "Today's weather is good"
            - "I want to try something new"
            """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": player_message}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            # parse JSON
            response_content = response.choices[0].message.content.strip()
            
            # extract JSON block
            if "```json" in response_content:
                start = response_content.find("```json") + 7
                end = response_content.find("```", start)
                response_content = response_content[start:end].strip()
            elif "```" in response_content:
                start = response_content.find("```") + 3
                end = response_content.find("```", start)
                response_content = response_content[start:end].strip()

            extracted_info = json.loads(response_content)
            
            # remove null values
            extracted_info = {k: v for k, v in extracted_info.items() if v is not None and v != ""}
            
            print(f"🔍🔍🔍 extracted info (stage {current_stage.value}):")
            print(f"   original message: {player_message}")
            print(f"   extracted info: {extracted_info}")
            
            return extracted_info
            
        except Exception as e:
            print(f"❌❌❌ error extracting info:")
            print(f"   error message: {e}")
            print(f"   original message: {player_message}")
            return {}
    
    def generate_info_collection_question(self, game_state: GameState, missing_info: List[str]) -> str:
        """generate a natural question about the missing information"""
        current_stage = game_state.current_stage
        player_info = game_state.player_info
        
        # emphasize personality_traits and likes if they are missing
        first_missing = missing_info[0]
        
        # generate a personalized question based on the collected information
        context = f"""
current situation:
- stage: {current_stage.value} ({current_stage.name})
- player name: {player_info.name if player_info.name else 'unknown'}
- collected information: {self._get_collected_info_summary(player_info)}
- missing information: {', '.join(missing_info)}
- first missing information: {first_missing}

ask one of the following information naturally: {first_missing}

special conditions:
- if "{first_missing}" is "personality (more specifically)", ask a question to add to the current personality traits ({player_info.personality_traits}) to learn more about personality traits. naturally emphasize that at least 3 personality traits are needed to complete the tutorial.
- if "{first_missing}" is "likes/hobbies (more specifically)", ask a question to add to the current likes ({player_info.likes}) to learn more about likes. naturally emphasize that more information is needed to learn more about likes.
- if "{first_missing}" is "personality", ask a question to learn more about the player's personality traits.
- if "{first_missing}" is "likes/hobbies", ask a question to learn more about the player's likes/hobbies.
- if "{first_missing}" is "life goal", ask a question to learn more about the player's life goal.

requirements:
1. generate a personalized question based on the collected information
2. be natural and conversational
3. concise and within 300 characters
4. be creative and not a fixed template
5. consider the player's interests or personality in a personalized question
6. ask a question about information that the player has not yet answered
7. do not react as if the player has already answered
8. naturally emphasize that the information is needed to complete the tutorial
9. naturally explain that more information is needed if the number condition is not met
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "you are a personalized adventure game NPC. you naturally talk with the player and collect the necessary information. to complete the tutorial, all required information is needed."},
                    {"role": "user", "content": context}
                ],
                max_tokens=150,
                temperature=0.8
            )
            
            question = response.choices[0].message.content.strip()
            print(f"AI info collection question: {question}")
            return question
            
        except Exception as e:
            print(f"AI question generation failed: {e}")
            # fallback: basic question
            missing = missing_info[0]
            if player_info.name:
                return f"{player_info.name}, talk about {missing}."
            else:
                return f"talk about {missing}."
    
    def _get_collected_info_summary(self, player_info: PlayerInfo) -> str:
        """summarize the collected player information so far"""
        collected = []
        
        if player_info.name:
            collected.append(f"name: {player_info.name}")
        if player_info.age:
            collected.append(f"age: {player_info.age}")
        if player_info.location:
            collected.append(f"location: {player_info.location}")
        if player_info.occupation:
            collected.append(f"occupation: {player_info.occupation}")
        if player_info.life_goal:
            collected.append(f"life goal: {player_info.life_goal}")
        if player_info.personality_traits:
            collected.append(f"personality traits: {player_info.personality_traits} ({len(player_info.personality_traits)} items)")
        if player_info.likes:
            collected.append(f"likes: {player_info.likes} ({len(player_info.likes)} items)")
        if player_info.fears:
            collected.append(f"fears: {player_info.fears}")
        if player_info.background:
            collected.append(f"background: {player_info.background}")
        if player_info.extra_info:
            collected.append(f"extra info: {player_info.extra_info} ({len(player_info.extra_info)} items)")
        
        return "; ".join(collected) if collected else "none" 