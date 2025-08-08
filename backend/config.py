import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Pinecone settings
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
    
    # AWS S3 settings
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    
    # game settings
    GAME_DEBUG_MODE = os.getenv("GAME_DEBUG_MODE", "false").lower() == "true"
    GAME_LOG_LEVEL = os.getenv("GAME_LOG_LEVEL", "INFO")
    
    # server settings
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
    
    @classmethod
    def validate(cls):
        """validate required environment variables"""
        # 개발/테스트 모드에서는 검증 스킵
        if cls.GAME_DEBUG_MODE:
            print("🔧 DEBUG MODE: 환경변수 검증을 스킵합니다.")
            # 더미 값 설정
            if not cls.OPENAI_API_KEY:
                cls.OPENAI_API_KEY = "sk-test-key-for-development"
            if not cls.PINECONE_API_KEY:
                cls.PINECONE_API_KEY = "test-pinecone-key"
            if not cls.AWS_ACCESS_KEY_ID:
                cls.AWS_ACCESS_KEY_ID = "test-aws-key"
            if not cls.AWS_SECRET_ACCESS_KEY:
                cls.AWS_SECRET_ACCESS_KEY = "test-aws-secret"
            if not cls.S3_BUCKET_NAME:
                cls.S3_BUCKET_NAME = "test-bucket"
            return True
        
        required_vars = [
            "OPENAI_API_KEY",
            "PINECONE_API_KEY",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "S3_BUCKET_NAME"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"required environment variables are not set: {', '.join(missing_vars)}")
        
        return True
    
    @classmethod
    def print_setup_instructions(cls):
        """print setup instructions"""
        print("🔧 environment setup is required!")
        print("=" * 50)
        print("1. create a .env file and add the following contents:")
        print("")
        print("OPENAI_API_KEY=your_openai_api_key_here")
        print("PINECONE_API_KEY=your_pinecone_api_key_here")
        print("PINECONE_ENVIRONMENT=us-east-1-aws")
        print("AWS_ACCESS_KEY_ID=your_aws_access_key_here")
        print("AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here")
        print("AWS_REGION=ap-northeast-2")
        print("S3_BUCKET_NAME=your_s3_bucket_name_here")
        print("")
        print("2. replace with actual API keys:")
        print("   - OpenAI API key: https://platform.openai.com/api-keys")
        print("   - Pinecone API key: https://app.pinecone.io/")
        print("")
        print("3. restart the server: python main.py")
        print("=" * 50) 