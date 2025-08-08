from openai import OpenAI
import os
import base64
import json
from typing import Dict, Any
from utils.game_state import PlayerInfo, GameState
import logging
from datetime import datetime
import uuid
import re
import boto3
from config import Config

logger = logging.getLogger(__name__)

class MapGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.generated_maps_dir = "static/generated_maps"
        self.maps_metadata_file = "static/generated_maps/maps_metadata.json"
        self.used_styles = set()
        
        # AWS S3 client initialization
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )
        self.s3_bucket = Config.S3_BUCKET_NAME
        self.s3_base_url = f"https://{self.s3_bucket}.s3.{Config.AWS_REGION}.amazonaws.com"
        
        # create generated maps directory (for local metadata)
        os.makedirs(self.generated_maps_dir, exist_ok=True)
        
        # initialize metadata file
        self._init_metadata_file()
    
    def _init_metadata_file(self):
        """initialize metadata file"""
        if not os.path.exists(self.maps_metadata_file):
            with open(self.maps_metadata_file, 'w', encoding='utf-8') as f:
                json.dump({"maps": {}, "used_styles": []}, f, ensure_ascii=False, indent=2)
    
    def generate_map_for_player(self, game_state: GameState, stage: int) -> Dict[str, Any]:
        """generate map for player using ChatGPT and DALLE"""
        player_info = game_state.player_info
        conversation_history = game_state.conversation_history
        print(f"[map generation] stage: {stage}, player: {player_info.name}")
        
        # 1. generate ChatGPT prompt
        prompt = self._make_gpt_prompt(player_info, conversation_history, stage, game_state)
        print(f"[map recommendation] GPT prompt:\n{prompt}")
        
        gpt_response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an NPC that recommends creative game maps. Based on the player's preferences and conversations, recommend a map name and a short description that suits the player. Include the map name (in Korean or English) and a short description in your response."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=1.0
        )
        map_suggestion = gpt_response.choices[0].message.content.strip()
        print(f"[map recommendation] GPT recommendation result: {map_suggestion}")
        
        # 2. extract map name/description
        map_name, map_desc = self._extract_map_name_and_desc(map_suggestion)
        if not map_name:
            map_name = f"creative map {uuid.uuid4().hex[:4]}"
            map_desc = "a unique map reflecting the player's preferences"
        
        # 3. generate image creation prompt
        if stage == 8:
            life_goal = player_info.life_goal
            dalle_prompt = f"2D RPG top-down tile map, final boss stage related to '{life_goal}', {map_name}, {map_desc}, no text, suitable for 2D RPG game"
        else:
            dalle_prompt = f"2D RPG top-down tile map, {map_name}, {map_desc}, no text, suitable for 2D RPG game"
        print(f"[map generation] GPT image generation prompt: {dalle_prompt}")
        
        try:
            dalle_response = self.client.images.generate(
                model="gpt-image-1",
                prompt=dalle_prompt,
                n=1,
                size="1024x1024",
                quality="high"
            )
            # decode image from b64_json field
            b64 = dalle_response.data[0].b64_json
            import base64
            image_bytes = base64.b64decode(b64)
            
            # 안전한 파일명 생성 (특수문자 제거, 길이 제한)
            safe_map_name = re.sub(r'[^a-zA-Z0-9\s]', '', map_name)  # 특수문자 제거
            safe_map_name = re.sub(r'\s+', '_', safe_map_name.strip())  # 공백을 언더스코어로
            safe_map_name = safe_map_name[:30]  # 길이 제한 (30자)
            
            if not safe_map_name:  # 빈 문자열이면 기본값 사용
                safe_map_name = "generated_map"
            
            map_id = f"{safe_map_name}_gptgen_{uuid.uuid4().hex[:8]}"
            image_filename = f"{map_id}.png"
            
            print(f"🔍 원본 맵 이름: '{map_name}'")
            print(f"🔍 안전한 파일명: '{image_filename}'")
            
            # upload image to S3
            s3_key = f"generated_maps/{image_filename}"
            s3_url = self._upload_to_s3(image_bytes, s3_key)
            print(f"[map generation] image uploaded to S3: {s3_url}")
            
            # summarize used elements
            used_elements_this_stage = self._get_used_elements(game_state)
            
            # save metadata
            map_metadata = {
                "id": map_id,
                "name": map_name,
                "description": map_desc,
                "environment": "gpt-ai",
                "themes": [],
                "style": "gpt-ai",
                "image_path": s3_url,
                "generated_at": datetime.now().isoformat(),
                "player_info": {
                    "name": player_info.name,
                    "location": player_info.location,
                    "personality_traits": player_info.personality_traits,
                    "likes": player_info.likes,
                    "life_goal": player_info.life_goal,
                    "fears": player_info.fears,
                },
                "stage": stage,
                "dalle_prompt": dalle_prompt,
                "gpt_suggestion": map_suggestion,
                "used_elements": used_elements_this_stage
            }
            self._save_map_metadata(map_id, map_metadata)
            print(f"[map generation] metadata saved: {map_id}")
            
            logger.info(f"AI map recommendation and generation completed: {map_id} - {map_name}")
            return {
                "map_id": map_id,
                "name": map_name,
                "description": map_desc,
                "environment": "gpt-ai",
                "themes": [],
                "image_path": s3_url,
                "style": "gpt-ai",
                "gpt_suggestion": map_suggestion,
                "reasoning": f"I recommended this map considering your personality and preferences.",
                "used_elements": used_elements_this_stage
            }
        except Exception as e:
            logger.error(f"GPT-based map generation failed: {str(e)}")
            print(f"[map generation] error: {str(e)}")
            raise RuntimeError(f"GPT-based map generation failed: {str(e)}")

    def _get_used_elements(self, game_state: GameState) -> Dict[str, Any]:
        """get used elements from game state"""
        if game_state and hasattr(game_state, 'used_map_elements'):
            # select unused elements
            unused_personality = [p for p in game_state.player_info.personality_traits 
                                if p not in game_state.used_map_elements["personality_traits"]]
            unused_likes = [l for l in game_state.player_info.likes 
                          if l not in game_state.used_map_elements["likes"]]
            unused_fears = [f for f in game_state.player_info.fears 
                          if f not in game_state.used_map_elements["fears"]]
            
            # selected elements
            selected_personality = unused_personality[:2] if unused_personality else game_state.player_info.personality_traits[:2]
            selected_likes = unused_likes[:2] if unused_likes else game_state.player_info.likes[:2]
            selected_fears = unused_fears[:1] if unused_fears else game_state.player_info.fears[:1]
            selected_location = game_state.player_info.location
            
            # mark as used
            game_state.used_map_elements["personality_traits"].extend(selected_personality)
            game_state.used_map_elements["likes"].extend(selected_likes)
            game_state.used_map_elements["fears"].extend(selected_fears)
            
            return {
                "personality_traits": selected_personality,
                "likes": selected_likes,
                "fears": selected_fears,
                "locations": [selected_location] if selected_location else []
            }
        return {}

    def _make_gpt_prompt(self, player_info: PlayerInfo, conversation_history: list, stage: int, game_state=None) -> str:
        """generate GPT prompt"""
        # recent 10 conversations
        recent = conversation_history[-10:] if conversation_history else []
        chat = "\n".join([f"{c['speaker']}: {c['message']}" for c in recent])
        
        # basic info
        location_info = f"\nlocation: {player_info.location}" if player_info.location else ""
        info = f"player name: {player_info.name}\nage: {player_info.age}{location_info}\nlikes/hobbies: {', '.join(player_info.likes)}\npersonality traits: {', '.join(player_info.personality_traits)}\nlife goal: {player_info.life_goal}\nfears: {', '.join(player_info.fears)}"
        
        # special handling for boss stage
        if stage == 8:
            life_goal = player_info.life_goal
            return f"player info:\n{info}\n\nrecent conversations:\n{chat}\n\nnow is the 8th stage (boss stage). recommend a final boss map directly related to the player's 'life goal': {life_goal}. include the map name and description in your response."
        else:
            return f"player info:\n{info}\n\nrecent conversations:\n{chat}\n\nnow is the {stage}th stage. recommend a creative map that suits the player. include the map name and a short description in your response."

    def _extract_map_name_and_desc(self, text: str):
        """extract map name and description from text"""
        print(f"🔍 원본 GPT 응답: {text}")
        
        # 1. "Map Name:" 패턴 찾기
        map_name_match = re.search(r"(?:Map Name|맵 이름):\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if map_name_match:
            name = map_name_match.group(1).strip(' ."')
            # Description 찾기
            desc_match = re.search(r"(?:Description|설명):\s*(.+)", text, re.IGNORECASE | re.DOTALL)
            desc = desc_match.group(1).strip() if desc_match else ""
            print(f"🔍 패턴1 매칭 - 이름: '{name}', 설명: '{desc[:50]}...'")
            return name, desc
        
        # 2. 인용부호로 둘러싸인 이름 (개선된 정규식)
        quote_match = re.search(r'[""\'`]([^""\'`\n]{3,50})[""\'`]', text)
        if quote_match:
            name = quote_match.group(1).strip()
            # 인용부호 뒤의 설명
            remaining_text = text[quote_match.end():].strip(' ,.:\n')
            desc = remaining_text if remaining_text else text[:quote_match.start()].strip()
            print(f"🔍 패턴2 매칭 - 이름: '{name}', 설명: '{desc[:50]}...'")
            return name, desc
        
        # 3. "Welcome to" 패턴
        welcome_match = re.search(r"Welcome to (?:the )?[""\'`]?([^""\'`\n!.]{3,50})[""\'`]?[!.]?", text, re.IGNORECASE)
        if welcome_match:
            name = welcome_match.group(1).strip()
            desc = text.replace(welcome_match.group(0), "").strip(' ,.:\n')
            print(f"🔍 패턴3 매칭 - 이름: '{name}', 설명: '{desc[:50]}...'")
            return name, desc
        
        # 4. 첫 번째 줄을 이름으로, 나머지를 설명으로
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            name = lines[0].strip('*# ."')
            desc = ' '.join(lines[1:]) if len(lines) > 1 else ""
            print(f"🔍 패턴4 매칭 - 이름: '{name}', 설명: '{desc[:50]}...'")
            return name, desc
        
        # 5. 백업: 첫 번째 의미있는 구문 (최소 3단어)
        words = text.split()
        if len(words) >= 3:
            name = ' '.join(words[:3])
            desc = ' '.join(words[3:]) if len(words) > 3 else ""
        else:
            name = text.strip()
            desc = ""
        
        print(f"🔍 백업 매칭 - 이름: '{name}', 설명: '{desc[:50]}...'")
        return name, desc

    def _upload_to_s3(self, image_bytes: bytes, s3_key: str) -> str:
        """upload image to S3 and return URL"""
        try:
            # upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=image_bytes,
                ContentType='image/png',
                ACL='public-read'  # public read permission
            )
            
            # generate S3 URL
            s3_url = f"{self.s3_base_url}/{s3_key}"
            logger.info(f"S3 upload completed: {s3_url}")
            return s3_url
            
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise RuntimeError(f"S3 upload failed: {str(e)}")
    
    def _save_map_metadata(self, map_id: str, metadata: Dict[str, Any]):
        """save map metadata"""
        try:
            # check and create directory
            os.makedirs(os.path.dirname(self.maps_metadata_file), exist_ok=True)
            
            # initialize file if not exists
            if not os.path.exists(self.maps_metadata_file):
                self._init_metadata_file()
            
            with open(self.maps_metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data["maps"][map_id] = metadata
            
            with open(self.maps_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"metadata save failed: {str(e)}")
    
    def get_generated_maps(self) -> Dict[str, Any]:
        """return metadata of generated maps"""
        try:
            # check and create directory
            os.makedirs(os.path.dirname(self.maps_metadata_file), exist_ok=True)
            
            # initialize file if not exists
            if not os.path.exists(self.maps_metadata_file):
                self._init_metadata_file()
            
            with open(self.maps_metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"map metadata load failed: {str(e)}")
            return {"maps": {}, "used_styles": []}
    
    def reset_used_styles(self):
        """reset used styles"""
        self.used_styles.clear()
        logger.info("used styles reset completed") 