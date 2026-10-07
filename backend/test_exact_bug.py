import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from career_service import get_personalized_chat_response

msg = "explain about skill tracker"

# Since we don't have the exact print statements inside get_personalized_chat_response
# Let's run it for test_user
print(f"Input: {msg}")
reply = get_personalized_chat_response('test_user', msg, [])
print(f"Final Response:\n{reply}\n")

# To test the internal intent detection properly, let's copy the logic momentarily
msg_lower = msg.lower()
intent = "unknown"
feature_topic = None

if any(f in msg_lower for f in ["skill tracker", "career assessment", "the assessment", "career match", "career matching", "learning roadmap", "my roadmap", "resume builder", "interview preparation", "certifications", "certification recommendations", "internship opportunities", "internships", "career analytics", "achievements", "profile completion"]):
    if any(w in msg_lower for w in ["what is", "explain", "how does", "how do", "tell me about", "what does", "what are", "how can i use"]):
        intent = "feature_explanation"
        if "skill tracker" in msg_lower: feature_topic = "skill_tracker"

print(f"Detected intent: {intent}")
print(f"Detected feature/topic: {feature_topic}")
