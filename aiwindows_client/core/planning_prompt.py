"""Planning-mode prompts shared by the Windows chat UI."""
DEFAULT_SYSTEM_PROMPT = "You are AILinux Assistant. Be accurate, concise, and use tools only when they materially help."

def get_planning_system_prompt(enabled: bool = True) -> str:
    if not enabled:
        return DEFAULT_SYSTEM_PROMPT
    return DEFAULT_SYSTEM_PROMPT + " Before complex work, form a short internal plan, verify assumptions, and return the completed result rather than unfinished intentions."
