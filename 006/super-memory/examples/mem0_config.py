from dotenv import load_dotenv
from mem0 import Memory
from mem0 import AsyncMemory

load_dotenv()
config = {
    		"graph_store": {
	        "provider": "neo4j",
	        "config": {
	            "url": "bolt://144.202.28.108:7687",
	            "username": "neo4j",
	            "password": "65132090"
        		}
    		},
    		"embedder": {
		        "provider": "ollama",
		        "config": {
		            "model": "nomic-embed-text:latest",
                    "ollama_base_url": "http://144.202.28.108:11434",
		        }
		    },
		    "llm": {
		        "provider": "deepseek",
		        "config": {
		            "model": "deepseek-chat",  # default model
		            "temperature": 0.2,
		            "max_tokens": 4096,
		            "top_p": 1.0
		        }
		    },
		    "vector_store": {
		        "provider": "qdrant",
		        "config": {
                    "collection_name": "default_mem0",
                    "host": "144.202.28.108",
                    "port": 6333,
                    "embedding_model_dims": 768,  # Change this according to your local model's dimensions
                },
		    }
		}

async def get_memory_client():
	m = Memory.from_config(config)
	return m
# For a user
# result = m.add("我喜欢每天早上起床写程序，不喜欢晚上写程序", user_id="danwen", metadata={"category": "preferences"})
# s = m.search("作者喜欢什么时间写程序", user_id="danwen",)
# print(s)
