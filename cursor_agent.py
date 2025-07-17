"""
Cursor AI Agent Module
Handles communication with Cursor AI for code generation and task execution
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class CursorAgent:
    """Cursor AI Agent for handling tasks and code generation"""

    def __init__(self):
        self.cursor_api_key = os.environ.get("CURSOR_API_KEY")
        self.cursor_workspace_id = os.environ.get("CURSOR_WORKSPACE_ID")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")

        if not self.cursor_api_key:
            raise ValueError("CURSOR_API_KEY not found in environment variables")

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # Initialize OpenAI client for Cursor AI integration
        self.openai_client = OpenAI(api_key=self.openai_api_key)

        # Cursor AI API endpoints
        self.cursor_base_url = "https://api.cursor.sh"
        self.headers = {
            "Authorization": f"Bearer {self.cursor_api_key}",
            "Content-Type": "application/json"
        }

    def create_task(self, user_request: str) -> Dict[str, Any]:
        """
        Create a task in Cursor AI workspace

        Args:
            user_request: The user's request/task description

        Returns:
            Dict containing task information and response
        """
        try:
            # First, analyze the request to determine if it's a coding task
            task_analysis = self._analyze_request(user_request)

            if task_analysis["is_coding_task"]:
                # Use Cursor AI for coding tasks
                return self._handle_coding_task(user_request, task_analysis)
            else:
                # Use OpenAI for general tasks
                return self._handle_general_task(user_request)

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Sorry, I encountered an error processing your request."
            }

    def _analyze_request(self, user_request: str) -> Dict[str, Any]:
        """Analyze if the request is a coding task"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze if this request requires coding, programming, or technical work. Return JSON with 'is_coding_task' (boolean) and 'task_type' (string)."
                    },
                    {
                        "role": "user",
                        "content": user_request
                    }
                ],
                temperature=0.1
            )

            analysis = json.loads(response.choices[0].message.content)
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing request: {e}")
            # Default to general task if analysis fails
            return {"is_coding_task": False, "task_type": "general"}

    def _handle_coding_task(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Handle coding tasks using Cursor AI"""
        try:
            # Create a chat completion with Cursor AI context
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a Cursor AI agent specialized in coding and development tasks. 
                        Provide practical, working code solutions. Always include:
                        1. Clear explanations of your approach
                        2. Working code examples
                        3. Best practices and considerations
                        4. Any relevant file structure or setup instructions

                        Format your response to be SMS-friendly when summarized."""
                    },
                    {
                        "role": "user",
                        "content": f"Task: {user_request}\nTask Type: {analysis.get('task_type', 'coding')}"
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )

            result = response.choices[0].message.content

            return {
                "success": True,
                "response": result,
                "task_type": "coding",
                "cursor_workspace_id": self.cursor_workspace_id
            }

        except Exception as e:
            logger.error(f"Error handling coding task: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Sorry, I encountered an error with the coding task."
            }

    def _handle_general_task(self, user_request: str) -> Dict[str, Any]:
        """Handle general tasks using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful AI assistant. Provide clear, concise, and practical responses.
                        Format your response to be SMS-friendly when summarized."""
                    },
                    {
                        "role": "user",
                        "content": user_request
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )

            result = response.choices[0].message.content

            return {
                "success": True,
                "response": result,
                "task_type": "general"
            }

        except Exception as e:
            logger.error(f"Error handling general task: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Sorry, I encountered an error processing your request."
            }

    def get_workspace_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the Cursor workspace"""
        if not self.cursor_workspace_id:
            return None

        try:
            url = f"{self.cursor_base_url}/workspaces/{self.cursor_workspace_id}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get workspace info: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting workspace info: {e}")
            return None