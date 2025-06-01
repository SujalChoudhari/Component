from dotenv import load_dotenv # Import load_dotenv
load_dotenv()  # Load environment variables from .env file
from src.ai_manager import AIComponentManager

if __name__ == "__main__":
    ai_manager = AIComponentManager(
        components_dir="./src/components",
        # api_key="...",
    )
    ai_manager.start_chat_interface()
