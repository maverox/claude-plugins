import sys
import json
import os
import re
from datetime import datetime

def get_session_prompt(session_id):
    """
    Retrieves the first user prompt for the given session ID from history.jsonl.
    """
    history_file = os.path.expanduser("~/.claude/history.jsonl")
    if not os.path.exists(history_file):
        return None

    first_prompt = None
    min_timestamp = float('inf')

    try:
        with open(history_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("sessionId") == session_id:
                        timestamp = entry.get("timestamp", 0)
                        if timestamp < min_timestamp:
                            min_timestamp = timestamp
                            first_prompt = entry.get("display", "")
                except json.JSONDecodeError:
                    continue
    except Exception:
        return None
        
    return first_prompt

def sanitize_filename(text):
    """
    Sanitizes text for use in a filename.
    """
    if not text:
        return "unknown_session"
    
    # Remove special characters and replace spaces with underscores
    clean_text = re.sub(r'[^\w\s-]', '', text)
    clean_text = re.sub(r'[-\s]+', '_', clean_text).strip('_')
    
    # Truncate to 50 chars
    return clean_text[:50]

def main():
    # Read input JSON from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    # Extract session ID
    session_id = input_data.get("session_id")
    
    # Get first prompt for this session
    prompt = get_session_prompt(session_id) if session_id else None
    
    # Construct filename
    sanitized_prompt = sanitize_filename(prompt)
    if session_id:
        filename = f"session_{session_id}_{sanitized_prompt}.jsonl"
    else:
        # Fallback if no session ID
        filename = f"tool_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

    project_dir = os.getcwd()
    # New directory structure: .claude/analytics/tool_usage_history/
    analytics_dir = os.path.join(project_dir, ".claude", "analytics", "tool_usage_history")
    
    # Ensure directory exists
    os.makedirs(analytics_dir, exist_ok=True)
    
    output_file = os.path.join(analytics_dir, filename)

    # Structure the log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": input_data.get("tool_name"),
        "input": input_data.get("tool_input"),
        "result": input_data.get("tool_response"),
        "session_id": session_id
    }

    # Append to the log file
    try:
        with open(output_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Error writing to tool usage log: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
