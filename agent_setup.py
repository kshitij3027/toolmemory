"""
Agent Setup Module for Tool Memory Project

This module creates and configures a Letta sleep-time agent focused on research assistance.
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv
from letta_client import Letta, SleeptimeManagerUpdate


def create_sleep_research_agent() -> dict:
    """
    Create a Letta sleep-time enabled agent focused on research assistance.
    
    Returns:
        dict: Agent information including agent_id and group_id
        
    Raises:
        ValueError: If API token is not found
        Exception: If agent creation fails
    """
    # Load environment variables
    load_dotenv()
    
    # Retrieve API Token
    api_token = os.getenv("LETTA_API_TOKEN")
    if not api_token:
        raise ValueError("LETTA_API_TOKEN not found in environment variables")
    
    try:
        # Initialize Letta client with timeout
        client = Letta(
            token=api_token,
            timeout=60.0
        )
        
        # Create the sleep-time enabled agent with research focus
        agent = client.agents.create(
            name="Research Sleep Agent",
            memory_blocks=[
                {
                    "label": "human",
                    "value": "The user is seeking research assistance on various topics. They value accuracy, comprehensive analysis, and well-sourced information. They prefer systematic approaches to complex problems and appreciate when information is organized logically. The user benefits from your ability to remember previous conversations and build upon past research.",
                    "limit": 5000
                },
                {
                    "label": "persona", 
                    "value": "You are a highly proficient research assistant with advanced memory capabilities. Your goal is to provide accurate, comprehensive, and well-sourced information. You excel at understanding complex queries, breaking them down into searchable components, and maintaining long-term context about previous research sessions.",
                    "limit": 5000
                }
            ],
            model="anthropic/claude-3-5-sonnet-20241022",  # Using context7 (Claude 3.7/3.5 Sonnet)
            embedding="openai/text-embedding-3-small",
            enable_sleeptime=True  # Enable sleep-time agent
        )
        
        print(f"Successfully created sleep-time research agent with ID: {agent.id}")
        
        # Get the multi-agent group information
        group_id = None
        current_frequency = None
        
        try:
            group_id = agent.multi_agent_group.id
            current_frequency = agent.multi_agent_group.sleep_time_agent_frequency
            print(f"Group ID: {group_id}")
            print(f"Current sleep-time frequency: {current_frequency}")
        except AttributeError as e:
            print(f"Warning: Could not access group information: {str(e)}")
            # Try to get group_id from a different path if available
            if hasattr(agent, 'multi_agent_group') and hasattr(agent.multi_agent_group, 'id'):
                group_id = agent.multi_agent_group.id
                print(f"Group ID: {group_id}")
            
            # Check if we can get frequency from group directly
            if group_id:
                try:
                    group_info = client.groups.retrieve(group_id=group_id)
                    if hasattr(group_info, 'sleeptime_agent_frequency'):
                        current_frequency = group_info.sleeptime_agent_frequency
                        print(f"Current sleep-time frequency: {current_frequency}")
                except Exception as group_e:
                    print(f"Could not retrieve group info: {str(group_e)}")
        
        # Update frequency to 2 if it's not already set to 2
        if group_id and current_frequency is not None and current_frequency != 2:
            print("Updating sleep-time agent frequency to 2...")
            try:
                group = client.groups.modify(
                    group_id=group_id,
                    manager_config=SleeptimeManagerUpdate(
                        sleep_time_agent_frequency=2
                    )
                )
                print("Sleep-time frequency updated to 2")
            except Exception as e:
                print(f"Warning: Could not update frequency: {str(e)}")
                print("Continuing with default frequency...")
        
        return {
            "agent_id": agent.id, 
            "name": getattr(agent, 'name', 'Research Sleep Agent'),
            "group_id": group_id,
            "sleep_time_frequency": 2
        }
        
    except Exception as e:
        print(f"Error creating sleep-time agent: {str(e)}")
        raise


def save_agent_config(agent_info: dict, file_path: str = "agent_config.json") -> None:
    """
    Save agent configuration to a JSON file.
    
    Args:
        agent_info (dict): The agent information including agent_id and group_id
        file_path (str): Path to save the configuration file
        
    Raises:
        Exception: If file writing fails
    """
    try:
        config_data = {
            "agent_id": agent_info["agent_id"],
            "group_id": agent_info.get("group_id"),
            "agent_type": "sleep_agent",
            "sleep_time_frequency": agent_info.get("sleep_time_frequency", 2)
        }
        
        with open(file_path, 'w') as f:
            json.dump(config_data, f, indent=4)
            
        print(f"Sleep-time agent configuration saved to {file_path}")
        
    except Exception as e:
        print(f"Error saving agent configuration: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        print("Creating sleep-time research agent...")
        agent_info = create_sleep_research_agent()
        
        if agent_info and "agent_id" in agent_info:
            save_agent_config(agent_info)
            print(f"Sleep-time research agent created successfully!")
            print(f"Agent ID: {agent_info['agent_id']}")
            print(f"Group ID: {agent_info.get('group_id', 'N/A')}")
            print(f"Sleep-time frequency: {agent_info.get('sleep_time_frequency', 2)}")
            print("Configuration saved to agent_config.json")
        else:
            print("Failed to create agent - no agent ID returned")
            
    except Exception as e:
        print(f"Failed to create sleep-time research agent: {str(e)}")
        exit(1)