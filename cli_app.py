"""
Enhanced CLI Application for Tool Memory Project with Sleep Agent

This module provides the main command-line interface for the Tool Memory system,
integrating the Letta sleep agent with MongoDB memory and Tavily search capabilities.
Enhanced with rich formatting for beautiful terminal output.
"""

import os
import json
import time
import sys
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from letta_client import Letta
from mongodb_memory import MongoDBMemory
from research_tools import TavilySearchTool
from memory_sync import sync_sleep_memories

# Rich imports for beautiful CLI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich import box
from rich.columns import Columns
from rich.align import Align

# Initialize rich console
console = Console()

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
        console.print(f"[red]❌ Error: Agent config file '{file_path}' not found.[/red]")
        return None
    except json.JSONDecodeError:
        console.print(f"[red]❌ Error: Could not decode JSON from '{file_path}'.[/red]")
        return None


class SleepChatSession:
    """
    Enhanced chat session class that manages a conversation session using the Letta sleep agent
    with memory enhancement and web search capabilities. Features beautiful rich formatting.
    """
    
    def __init__(self):
        """
        Initialize the SleepChatSession with enhanced visual feedback.
        
        Raises:
            ValueError: If required configuration or environment variables are missing.
            Exception: If initialization of any service fails.
        """
        # Initialize session tracking
        self.start_time = time.time()
        self.queries_processed = 0
        self.memory_hits = 0
        self.web_searches = 0
        
        # Show initialization progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            
            # Initialize MongoDB memory
            task1 = progress.add_task("[cyan]Connecting to MongoDB memory system...", total=None)
            try:
                self.mongo_memory = MongoDBMemory()
                progress.update(task1, description="[green]✅ MongoDB memory system connected")
                time.sleep(0.5)  # Brief pause for visual effect
            except Exception as e:
                progress.update(task1, description=f"[red]❌ Failed to initialize MongoDB memory: {str(e)}")
                raise
            
            # Initialize Tavily search tool
            task2 = progress.add_task("[cyan]Initializing Tavily search tool...", total=None)
            try:
                self.tavily_search = TavilySearchTool()
                progress.update(task2, description="[green]✅ Tavily search tool initialized")
                time.sleep(0.5)
            except Exception as e:
                progress.update(task2, description=f"[red]❌ Failed to initialize Tavily search: {str(e)}")
                raise
            
            # Get agent configuration
            task3 = progress.add_task("[cyan]Loading sleep agent configuration...", total=None)
            self.agent_config = load_agent_config()
            if not self.agent_config:
                progress.update(task3, description="[red]❌ Agent configuration not found")
                raise ValueError("Agent configuration not found")
            
            self.agent_id = self.agent_config.get("agent_id")
            self.group_id = self.agent_config.get("group_id")
            self.agent_type = self.agent_config.get("agent_type", "unknown")
            
            if not self.agent_id:
                progress.update(task3, description="[red]❌ Agent ID not found in configuration")
                raise ValueError("Agent ID not found in configuration")
            
            progress.update(task3, description="[green]✅ Sleep agent configuration loaded")
            time.sleep(0.5)
            
            # Initialize Letta client with sleep agent
            task4 = progress.add_task("[cyan]Connecting to Letta sleep agent...", total=None)
            try:
                letta_api_token = os.getenv("LETTA_API_TOKEN")
                if not letta_api_token:
                    progress.update(task4, description="[red]❌ LETTA_API_TOKEN not found in environment variables")
                    raise ValueError("LETTA_API_TOKEN not found in environment variables")
                
                self.letta_client = Letta(
                    token=letta_api_token,
                    timeout=60.0
                )
                progress.update(task4, description=f"[green]✅ Letta sleep agent connected: {self.agent_type}")
                time.sleep(0.5)
                
            except Exception as e:
                progress.update(task4, description=f"[red]❌ Failed to connect to Letta sleep agent: {str(e)}")
                raise
        
        # Show success message
        success_panel = Panel(
            Text("🎯 Enhanced Sleep Agent Ready for Interaction!\n💡 Type 'help' to see available commands", style="bold green"),
            title="[bold blue]Tool Memory CLI Initialized",
            border_style="green",
            box=box.ROUNDED
        )
        console.print("\n")
        console.print(success_panel)
        
        if self.group_id:
            console.print(f"[dim]📝 Sleep agent group ID: {self.group_id}[/dim]")
        console.print("\n")
    
    def search_web_if_needed(self, query: str, memory_results: List[Dict]) -> Optional[str]:
        """
        Determine if a web search is needed and perform it if necessary.
        
        Args:
            query (str): User's query.
            memory_results (List[Dict]): Results from memory search.
            
        Returns:
            Optional[str]: Web search results if performed, None otherwise.
        """
        # Check if we have relevant memory results
        if memory_results and len(memory_results) > 0:
            # If we have good memory results, less likely to need web search
            web_trigger_words = ['latest', 'recent', 'current', 'today', 'news', '2024', '2025']
        else:
            # If no memory results, lower threshold for web search
            web_trigger_words = ['latest', 'recent', 'current', 'today', 'news', '2024', '2025', 
                               'what is', 'how to', 'when', 'where', 'who']
        
        query_lower = query.lower()
        needs_web_search = any(trigger in query_lower for trigger in web_trigger_words)
        
        if needs_web_search:
            try:
                with console.status("[cyan]🔍 Searching the web for current information...", spinner="dots"):
                    search_results = self.tavily_search.search(query)
                    self.web_searches += 1
                
                if search_results:
                    console.print("[green]✅ Web search completed[/green]")
                    # Store web search results in memory for future use
                    search_summary = f"Web search results for '{query}': {search_results[:500]}..."
                    metadata = {
                        "source": "tavily_web_search",
                        "query": query,
                        "search_timestamp": time.time()
                    }
                    self.mongo_memory.add_memory(search_summary, metadata=metadata)
                    
                    return search_results
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Web search failed: {str(e)}[/yellow]")
        
        return None
    
    def process_query(self, user_query: str) -> str:
        """
        Process a user query with memory enhancement and web search.
        
        Args:
            user_query (str): The user's question or request.
            
        Returns:
            str: The agent's response.
        """
        # Show query processing header
        query_panel = Panel(
            Text(user_query, style="bold cyan"),
            title="[bold yellow]🤔 Processing Query",
            border_style="yellow",
            box=box.MINIMAL
        )
        console.print(query_panel)
        
        self.queries_processed += 1
        
        try:
            # Search relevant memories with progress indicator
            with console.status("[cyan]🧠 Searching memory database...", spinner="dots"):
                memory_results = self.mongo_memory.search_memories(user_query, limit=5)
            
            if memory_results:
                self.memory_hits += 1
                console.print(f"[green]📚 Found {len(memory_results)} relevant memories[/green]")
            else:
                console.print("[dim]📭 No relevant memories found[/dim]")
            
            # Check if web search is needed
            web_results = self.search_web_if_needed(user_query, memory_results)
            
            # Construct enhanced prompt with context
            enhanced_prompt = f"User query: {user_query}\n\n"
            
            if memory_results:
                enhanced_prompt += "Relevant memories:\n"
                for i, memory in enumerate(memory_results[:3], 1):
                    enhanced_prompt += f"{i}. {memory.get('text', '')[:200]}...\n"
                enhanced_prompt += "\n"
            
            if web_results:
                enhanced_prompt += f"Current web information:\n{web_results[:800]}\n\n"
            
            enhanced_prompt += "Please provide a comprehensive response using the available context."
            
            # Send to Letta sleep agent with progress indicator
            with console.status("[cyan]🤖 Getting response from sleep agent...", spinner="dots"):
                response = self.letta_client.agents.messages.create(
                    agent_id=self.agent_id,
                    messages=[{"role": "user", "text": enhanced_prompt}]
                )
            
            # Extract response text
            if hasattr(response, 'messages') and response.messages:
                agent_response = ""
                for msg in response.messages:
                    if hasattr(msg, 'text') and msg.text:
                        agent_response += msg.text + " "
                
                if agent_response.strip():
                    # Store the interaction in memory
                    interaction_text = f"Q: {user_query}\nA: {agent_response.strip()}"
                    metadata = {
                        "source": "sleep_agent_interaction",
                        "agent_id": self.agent_id,
                        "group_id": self.group_id,
                        "query": user_query,
                        "timestamp": time.time()
                    }
                    self.mongo_memory.add_memory(interaction_text, metadata=metadata)
                    
                    return agent_response.strip()
            
            return "I apologize, but I couldn't generate a response. Please try again."
            
        except Exception as e:
            console.print(f"[red]❌ Error processing query: {str(e)}[/red]")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def show_session_stats(self):
        """Display current session statistics in a beautiful table."""
        current_time = time.time()
        session_duration = current_time - self.start_time
        
        # Create statistics table
        stats_table = Table(title="📊 Session Statistics", box=box.ROUNDED, show_header=True, header_style="bold magenta")
        stats_table.add_column("Metric", style="cyan", no_wrap=True)
        stats_table.add_column("Value", style="green", justify="right")
        
        stats_table.add_row("⏱️ Session Duration", f"{session_duration:.1f} seconds")
        stats_table.add_row("💬 Queries Processed", str(self.queries_processed))
        stats_table.add_row("🧠 Memory Hits", str(self.memory_hits))
        stats_table.add_row("🔍 Web Searches", str(self.web_searches))
        
        # Get memory statistics
        try:
            memory_stats = self.mongo_memory.get_memory_stats()
            stats_table.add_row("📚 Total Memories", str(memory_stats.get('total_memories', 'N/A')))
            
            if 'sources_breakdown' in memory_stats:
                # Create memory sources table
                sources_table = Table(title="📂 Memory Sources", box=box.MINIMAL, show_header=True, header_style="bold cyan")
                sources_table.add_column("Source", style="yellow")
                sources_table.add_column("Count", style="green", justify="right")
                
                for source, count in memory_stats['sources_breakdown'].items():
                    sources_table.add_row(source, str(count))
                
                console.print("\n")
                console.print(stats_table)
                console.print("\n")
                console.print(sources_table)
                return
                
        except Exception as e:
            stats_table.add_row("⚠️ Memory Stats", f"Error: {str(e)}")
        
        console.print("\n")
        console.print(stats_table)
    
    def show_help(self):
        """Display help information in a beautiful formatted panel."""
        help_content = """
[bold cyan]💬 Available Commands:[/bold cyan]
  [yellow]help[/yellow]          - Show this help message
  [yellow]stats[/yellow]         - Show session statistics
  [yellow]sync[/yellow]          - Synchronize sleep agent memories
  [yellow]clear[/yellow]         - Clear screen
  [yellow]quit[/yellow] or [yellow]exit[/yellow]  - Exit the application

[bold cyan]🌟 Features:[/bold cyan]
  • [green]Memory-enhanced responses[/green] using MongoDB
  • [green]Automatic web search[/green] for current information
  • [green]Sleep agent[/green] with background memory processing
  • [green]Session statistics[/green] and memory tracking
  • [green]Persistent conversation history[/green]
  • [green]Beautiful terminal interface[/green] with rich formatting
        """
        
        help_panel = Panel(
            help_content,
            title="[bold blue]🆘 Tool Memory CLI Help",
            border_style="blue",
            box=box.ROUNDED
        )
        
        console.print("\n")
        console.print(help_panel)
    
    def sync_sleep_memories(self):
        """Synchronize sleep agent memories with MongoDB."""
        sync_panel = Panel(
            Text("🔄 Synchronizing sleep agent memories...", style="bold yellow"),
            border_style="yellow",
            box=box.MINIMAL
        )
        console.print("\n")
        console.print(sync_panel)
        
        try:
            with console.status("[cyan]Synchronizing memories...", spinner="dots"):
                success = sync_sleep_memories()
            
            if success:
                console.print("[green]✅ Sleep agent memory synchronization completed![/green]")
            else:
                console.print("[red]❌ Sleep agent memory synchronization failed.[/red]")
        except Exception as e:
            console.print(f"[red]❌ Sync error: {str(e)}[/red]")
    
    def run_cli(self):
        """Main CLI interaction loop with beautiful formatting."""
        # Welcome message
        welcome_panel = Panel(
            Text("🎯 Welcome to the Tool Memory CLI with Sleep Agent!\n💡 Enhanced with persistent memory and web search capabilities\n📝 Your conversations are automatically saved and enhanced", 
                 style="bold green", justify="center"),
            title="[bold blue]Tool Memory System",
            subtitle="[dim]Powered by Letta Sleep Agent + MongoDB + Tavily[/dim]",
            border_style="blue",
            box=box.DOUBLE
        )
        console.print(welcome_panel)
        console.print("\n")
        
        while True:
            try:
                # Get user input with rich prompt
                user_input = Prompt.ask("[bold cyan]🗣️  You", console=console).strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit']:
                    break
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                elif user_input.lower() == 'stats':
                    self.show_session_stats()
                    continue
                elif user_input.lower() == 'sync':
                    self.sync_sleep_memories()
                    continue
                elif user_input.lower() == 'clear':
                    console.clear()
                    continue
                
                # Process the query
                response = self.process_query(user_input)
                
                # Display response in a beautiful panel
                response_panel = Panel(
                    Markdown(response),
                    title="[bold green]🤖 Sleep Agent Response",
                    border_style="green",
                    box=box.ROUNDED
                )
                console.print("\n")
                console.print(response_panel)
                console.print("\n")
                
            except KeyboardInterrupt:
                console.print("\n")
                goodbye_panel = Panel(
                    Text("👋 Goodbye! Thanks for using Tool Memory CLI!", style="bold yellow", justify="center"),
                    border_style="yellow",
                    box=box.ROUNDED
                )
                console.print(goodbye_panel)
                break
            except Exception as e:
                console.print(f"\n[red]❌ Unexpected error: {str(e)}[/red]")
                console.print("[dim]💡 Type 'help' for available commands[/dim]\n")
        
        # Final statistics
        console.print("\n")
        final_panel = Panel(
            Text("📊 Final Session Summary", style="bold magenta", justify="center"),
            border_style="magenta",
            box=box.MINIMAL
        )
        console.print(final_panel)
        self.show_session_stats()
        
        # Clean up
        try:
            self.mongo_memory.close()
            console.print("\n[green]✅ MongoDB connection closed[/green]")
        except:
            pass
        
        # Final goodbye
        final_goodbye = Panel(
            Text("🙏 Thank you for using Tool Memory CLI with Sleep Agent!\n✨ Your memories have been preserved for future sessions", 
                 style="bold blue", justify="center"),
            border_style="blue",
            box=box.DOUBLE
        )
        console.print("\n")
        console.print(final_goodbye)


def main():
    """
    Main entry point for the enhanced CLI application.
    """
    # Load environment variables
    load_dotenv()
    
    try:
        session = SleepChatSession()
        session.run_cli()
    except Exception as e:
        error_panel = Panel(
            f"[red]❌ Failed to initialize CLI: {str(e)}[/red]\n\n[yellow]💡 Make sure you have:[/yellow]\n   1. Run 'python agent_setup.py' to create a sleep agent\n   2. Set LETTA_API_TOKEN environment variable\n   3. Set MONGODB_URI environment variable\n   4. Set TAVILY_API_KEY environment variable",
            title="[bold red]Initialization Error",
            border_style="red",
            box=box.ROUNDED
        )
        console.print(error_panel)
        sys.exit(1)


if __name__ == "__main__":
    main()
