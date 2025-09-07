"""
Utility helper functions for the F1 RAG Chatbot
"""

import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import streamlit as st


def hash_text(text: str, length: int = 8) -> str:
    """Generate a hash for text content"""
    return hashlib.md5(text.encode()).hexdigest()[:length]


def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
    
    # Remove multiple punctuation
    text = re.sub(r'[\.]{2,}', '.', text)
    text = re.sub(r'[\,]{2,}', ',', text)
    
    return text.strip()


def truncate_text(text: str, max_length: int = 200, add_ellipsis: bool = True) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    if add_ellipsis:
        truncated += "..."
    
    return truncated


def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp


def time_ago(timestamp: str) -> str:
    """Get human-readable time difference"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - dt.replace(tzinfo=None)
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    except:
        return "Unknown"


def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """Safely get value from dictionary"""
    try:
        return dictionary.get(key, default)
    except:
        return default


def validate_url(url: str) -> bool:
    """Validate URL format"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return "Unknown"


def calculate_similarity_color(score: float) -> str:
    """Get color based on similarity score"""
    if score >= 0.8:
        return "green"
    elif score >= 0.6:
        return "orange"
    else:
        return "red"


def format_number(number: int) -> str:
    """Format number with commas"""
    return f"{number:,}"


def create_download_link(content: str, filename: str, link_text: str = "Download") -> str:
    """Create a download link for content"""
    import base64
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link_text}</a>'
    return href


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    import platform
    import sys
    
    return {
        "python_version": sys.version.split()[0],
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor()
    }


def log_user_interaction(action: str, details: Dict = None):
    """Log user interactions for analytics"""
    if "user_interactions" not in st.session_state:
        st.session_state.user_interactions = []
    
    interaction = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details or {}
    }
    
    st.session_state.user_interactions.append(interaction)
    
    # Keep only last 100 interactions
    if len(st.session_state.user_interactions) > 100:
        st.session_state.user_interactions = st.session_state.user_interactions[-100:]


def get_interaction_stats() -> Dict[str, Any]:
    """Get user interaction statistics"""
    if "user_interactions" not in st.session_state:
        return {}
    
    interactions = st.session_state.user_interactions
    
    # Count by action type
    action_counts = {}
    for interaction in interactions:
        action = interaction["action"]
        action_counts[action] = action_counts.get(action, 0) + 1
    
    # Recent activity (last hour)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_interactions = [
        i for i in interactions 
        if datetime.fromisoformat(i["timestamp"]) > one_hour_ago
    ]
    
    return {
        "total_interactions": len(interactions),
        "action_counts": action_counts,
        "recent_interactions": len(recent_interactions),
        "most_common_action": max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else None
    }


class ProgressTracker:
    """Progress tracking utility"""
    
    def __init__(self, total_steps: int, description: str = "Processing"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        
    def update(self, step: int = None, status: str = None):
        """Update progress"""
        if step is not None:
            self.current_step = step
        else:
            self.current_step += 1
            
        progress = min(self.current_step / self.total_steps, 1.0)
        self.progress_bar.progress(progress)
        
        if status:
            self.status_text.text(f"{self.description}: {status}")
        else:
            self.status_text.text(f"{self.description}: {self.current_step}/{self.total_steps}")
    
    def complete(self, final_message: str = "Completed!"):
        """Mark as complete"""
        self.progress_bar.progress(1.0)
        self.status_text.text(final_message)


def create_info_box(title: str, content: str, box_type: str = "info"):
    """Create styled info boxes"""
    colors = {
        "info": "#e7f3ff",
        "success": "#d4edda", 
        "warning": "#fff3cd",
        "error": "#f8d7da"
    }
    
    border_colors = {
        "info": "#0066cc",
        "success": "#28a745",
        "warning": "#ffc107", 
        "error": "#dc3545"
    }
    
    st.markdown(f"""
    <div style="
        background-color: {colors.get(box_type, colors['info'])};
        border-left: 4px solid {border_colors.get(box_type, border_colors['info'])};
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    ">
        <strong>{title}</strong><br>
        {content}
    </div>
    """, unsafe_allow_html=True)