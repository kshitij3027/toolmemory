"""
Memory Synchronization for Tool Memory Project

This module extracts memories from Letta sleep agent and stores them in MongoDB
for enhanced memory capabilities.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from letta_client import Letta
from mongodb_memory import MongoDBMemory


def load_agent_config(file_path: str = "agent_config.json") -> Optional[Dict[str, Any]]:
    """
    Load agent configuration from configuration file.
    
    Args:
        file_path (str): Path to the agent configuration file.
        
    Returns:
        Optional[Dict[str, Any]]: Agent configuration if found, None otherwise.
    """
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print(f"Error: Agent config file '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{file_path}'.")
        return None


class SleepMemorySynchronizer:
    """
    A class for synchronizing memories between Letta sleep agent and MongoDB.
    
    Extracts various types of memories from Letta sleep agent and stores them
    in MongoDB for persistent, searchable memory.
    """
    
    def __init__(self):
        """
        Initialize the SleepMemorySynchronizer.
        
        Raises:
            ValueError: If required API keys or agent ID are missing.
            Exception: If initialization of services fails.
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize MongoDB memory
        try:
            self.mongo_memory = MongoDBMemory()
            print("MongoDB memory initialized successfully")
        except Exception as e:
            print(f"Failed to initialize MongoDB memory: {str(e)}")
            raise
        
        # Get Letta API token
        self.letta_api_token = os.getenv("LETTA_API_TOKEN")
        if not self.letta_api_token:
            raise ValueError("LETTA_API_TOKEN not found in environment variables")
        
        # Get agent configuration
        self.agent_config = load_agent_config()
        if not self.agent_config:
            raise ValueError("Agent configuration not found in agent_config.json")
        
        self.agent_id = self.agent_config.get("agent_id")
        self.group_id = self.agent_config.get("group_id")
        self.agent_type = self.agent_config.get("agent_type", "unknown")
        
        if not self.agent_id:
            raise ValueError("Agent ID not found in agent_config.json")
        
        # Initialize Letta client
        try:
            self.letta_client = Letta(
                token=self.letta_api_token,
                timeout=60.0
            )
            print(f"Letta client initialized for {self.agent_type}: {self.agent_id}")
            if self.group_id:
                print(f"Sleep agent group ID: {self.group_id}")
        except Exception as e:
            print(f"Failed to initialize Letta client: {str(e)}")
            raise
        
        print("SleepMemorySynchronizer initialized successfully")
    
    def get_sleep_agent_memories(self) -> List[str]:
        """
        Get memories from the sleep agent in the multi-agent group.
        
        Returns:
            List[str]: List of sleep agent IDs in the group.
        """
        try:
            if not self.group_id:
                print("No group ID found - this may not be a sleep-enabled agent")
                return []
            
            # Get group information
            group = self.letta_client.groups.retrieve(group_id=self.group_id)
            sleep_agents = []
            
            if hasattr(group, 'agents'):
                for agent_id in group.agents:
                    if agent_id != self.agent_id:  # This is likely the sleep agent
                        sleep_agents.append(agent_id)
                        print(f"Found sleep agent: {agent_id}")
            
            return sleep_agents
            
        except Exception as e:
            print(f"Error getting sleep agent memories: {str(e)}")
            return []
    
    def sync_core_memory(self) -> int:
        """
        Synchronize core memory blocks from Letta agent to MongoDB.
        For sleep agents, we sync the primary agent's memory blocks which are managed by the sleep agent.
        
        Returns:
            int: Number of core memory blocks synchronized.
            
        Raises:
            Exception: If core memory retrieval or storage fails.
        """
        try:
            print("Syncing core memory blocks from sleep-enabled agent...")
            
            # Get core memory from the primary agent (which is managed by sleep agent)
            core_memory = self.letta_client.agents.core_memory.retrieve(agent_id=self.agent_id)
            
            synchronized_count = 0
            
            # Process human memory block
            if hasattr(core_memory, 'human') and core_memory.human:
                text_content = str(core_memory.human)
                metadata = {
                    "source": "letta_sleep_core_memory",
                    "type": "human",
                    "agent_id": self.agent_id,
                    "group_id": self.group_id,
                    "agent_type": "sleep_agent"
                }
                
                self.mongo_memory.add_memory(text_content, metadata=metadata)
                print(f"Synced human memory block: {text_content[:50]}...")
                synchronized_count += 1
            
            # Process persona memory block
            if hasattr(core_memory, 'persona') and core_memory.persona:
                text_content = str(core_memory.persona)
                metadata = {
                    "source": "letta_sleep_core_memory",
                    "type": "persona",
                    "agent_id": self.agent_id,
                    "group_id": self.group_id,
                    "agent_type": "sleep_agent"
                }
                
                self.mongo_memory.add_memory(text_content, metadata=metadata)
                print(f"Synced persona memory block: {text_content[:50]}...")
                synchronized_count += 1
            
            # Get any additional memory blocks that may have been created by the sleep agent
            try:
                blocks = self.letta_client.agents.blocks.list(agent_id=self.agent_id)
                for block in blocks:
                    if hasattr(block, 'label') and block.label not in ['human', 'persona']:
                        if hasattr(block, 'value') and block.value:
                            text_content = str(block.value)
                            metadata = {
                                "source": "letta_sleep_core_memory",
                                "type": block.label,
                                "agent_id": self.agent_id,
                                "group_id": self.group_id,
                                "agent_type": "sleep_agent"
                            }
                            
                            self.mongo_memory.add_memory(text_content, metadata=metadata)
                            print(f"Synced {block.label} memory block: {text_content[:50]}...")
                            synchronized_count += 1
            except Exception as e:
                print(f"Warning: Could not retrieve additional memory blocks: {str(e)}")
            
            print(f"Core memory synchronization complete: {synchronized_count} blocks")
            return synchronized_count
            
        except Exception as e:
            print(f"Error syncing core memory: {str(e)}")
            raise
    
    def sync_chat_history(self, limit: int = 100) -> int:
        """
        Synchronize chat history from Letta agent to MongoDB.
        
        Args:
            limit (int): Maximum number of messages to sync.
            
        Returns:
            int: Number of messages synchronized.
            
        Raises:
            Exception: If chat history retrieval or storage fails.
        """
        try:
            print(f"Syncing chat history from sleep-enabled agent (limit: {limit})...")
            
            # Get messages from the primary agent
            messages = self.letta_client.agents.messages.list(
                agent_id=self.agent_id,
                limit=limit
            )
            
            synchronized_count = 0
            
            for message in messages:
                # Skip empty messages
                if not hasattr(message, 'text') or not message.text or message.text.strip() == "":
                    continue
                
                text_content = message.text
                metadata = {
                    "source": "letta_sleep_chat_history",
                    "role": getattr(message, 'role', 'unknown'),
                    "agent_id": self.agent_id,
                    "group_id": self.group_id,
                    "agent_type": "sleep_agent",
                    "message_id": str(getattr(message, 'id', '')),
                    "timestamp": getattr(message, 'created_at', None),
                    "tool_calls": getattr(message, 'tool_calls', None),
                    "tool_call_id": getattr(message, 'tool_call_id', None)
                }
                
                self.mongo_memory.add_memory(text_content, metadata=metadata)
                print(f"Synced {metadata['role']} message: {text_content[:50]}...")
                synchronized_count += 1
            
            print(f"Chat history synchronization complete: {synchronized_count} messages")
            return synchronized_count
            
        except Exception as e:
            print(f"Error syncing chat history: {str(e)}")
            raise
    
    def sync_sleep_agent_state(self) -> int:
        """
        Synchronize sleep agent state information to MongoDB.
        
        Returns:
            int: Number of state items synchronized.
            
        Raises:
            Exception: If agent state retrieval or storage fails.
        """
        try:
            print("Syncing sleep agent state information...")
            
            # Get primary agent details
            agent = self.letta_client.agents.retrieve(agent_id=self.agent_id)
            
            synchronized_count = 0
            
            # Sync agent name
            if hasattr(agent, 'name') and agent.name:
                text_content = f"Sleep agent name: {agent.name}"
                metadata = {
                    "source": "letta_sleep_agent_state",
                    "type": "agent_name",
                    "agent_id": self.agent_id,
                    "group_id": self.group_id,
                    "agent_type": "sleep_agent"
                }
                self.mongo_memory.add_memory(text_content, metadata=metadata)
                synchronized_count += 1
            
            # Sync agent description if available
            if hasattr(agent, 'description') and agent.description:
                text_content = f"Sleep agent description: {agent.description}"
                metadata = {
                    "source": "letta_sleep_agent_state",
                    "type": "agent_description",
                    "agent_id": self.agent_id,
                    "group_id": self.group_id,
                    "agent_type": "sleep_agent"
                }
                self.mongo_memory.add_memory(text_content, metadata=metadata)
                synchronized_count += 1
            
            # Sync system prompt if available
            if hasattr(agent, 'system') and agent.system:
                text_content = f"Sleep agent system prompt: {agent.system}"
                metadata = {
                    "source": "letta_sleep_agent_state",
                    "type": "system_prompt",
                    "agent_id": self.agent_id,
                    "group_id": self.group_id,
                    "agent_type": "sleep_agent"
                }
                self.mongo_memory.add_memory(text_content, metadata=metadata)
                synchronized_count += 1
            
            # Sync sleep agent configuration
            if self.group_id:
                try:
                    group = self.letta_client.groups.retrieve(group_id=self.group_id)
                    if hasattr(group, 'sleep_time_agent_frequency'):
                        text_content = f"Sleep agent frequency: {group.sleep_time_agent_frequency}"
                        metadata = {
                            "source": "letta_sleep_agent_state",
                            "type": "sleep_frequency",
                            "agent_id": self.agent_id,
                            "group_id": self.group_id,
                            "agent_type": "sleep_agent"
                        }
                        self.mongo_memory.add_memory(text_content, metadata=metadata)
                        synchronized_count += 1
                except Exception as e:
                    print(f"Warning: Could not retrieve group information: {str(e)}")
            
            print(f"Sleep agent state synchronization complete: {synchronized_count} items")
            return synchronized_count
            
        except Exception as e:
            print(f"Error syncing sleep agent state: {str(e)}")
            raise
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about synchronized memories.
        
        Returns:
            Dict[str, Any]: Synchronization statistics.
        """
        try:
            stats = self.mongo_memory.get_memory_stats()
            
            # Add agent-specific information
            agent_stats = {
                "agent_id": self.agent_id,
                "group_id": self.group_id,
                "agent_type": self.agent_type,
                "sync_timestamp": time.time(),
                "mongodb_stats": stats
            }
            
            return agent_stats
            
        except Exception as e:
            print(f"Error getting sync statistics: {str(e)}")
            return {"error": str(e)}


def sync_sleep_memories() -> bool:
    """
    Main function to synchronize all memories from Letta sleep agent to MongoDB.
    
    Returns:
        bool: True if synchronization was successful, False otherwise.
    """
    try:
        print("=== Sleep Agent Memory Synchronization Started ===")
        start_time = time.time()
        
        # Initialize synchronizer
        synchronizer = SleepMemorySynchronizer()
        
        total_synced = 0
        
        # Get sleep agent information
        sleep_agents = synchronizer.get_sleep_agent_memories()
        if sleep_agents:
            print(f"Found {len(sleep_agents)} sleep agent(s) in group")
        
        # Sync core memory (managed by sleep agent)
        core_count = synchronizer.sync_core_memory()
        total_synced += core_count
        
        # Sync chat history
        chat_count = synchronizer.sync_chat_history()
        total_synced += chat_count
        
        # Sync sleep agent state
        state_count = synchronizer.sync_sleep_agent_state()
        total_synced += state_count
        
        # Get final statistics
        stats = synchronizer.get_sync_statistics()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n=== Sleep Agent Memory Synchronization Summary ===")
        print(f"Agent Type: {synchronizer.agent_type}")
        print(f"Core memory blocks: {core_count}")
        print(f"Chat messages: {chat_count}")
        print(f"Agent state items: {state_count}")
        print(f"Total memories synced: {total_synced}")
        print(f"Synchronization completed in {duration:.2f} seconds")
        
        if stats.get("mongodb_stats"):
            mongo_stats = stats["mongodb_stats"]
            print(f"Total memories in database: {mongo_stats.get('total_memories', 'N/A')}")
            print(f"Sources breakdown: {mongo_stats.get('sources_breakdown', {})}")
        
        print("=== Sleep Agent Memory Synchronization Complete ===")
        
        # Clean up
        synchronizer.mongo_memory.close()
        
        return True
        
    except Exception as e:
        print(f"Sleep agent memory synchronization failed: {str(e)}")
        return False


if __name__ == "__main__":
    """
    Run sleep agent memory synchronization when script is executed directly.
    """
    success = sync_sleep_memories()
    if success:
        print("\nSleep agent memory synchronization completed successfully!")
    else:
        print("\nSleep agent memory synchronization failed. Check error messages above.")
        exit(1)
