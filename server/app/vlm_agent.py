import time
from app.schema.action_schema import SanitizedContextPayload, StructuredAction, ActionTarget

class RemoteVLMAgent:
    def __init__(self):
        print("[RemoteVLMAgent] Initialized. Ready to reason over sanitized context.")

    def plan_next_action(self, payload: SanitizedContextPayload) -> StructuredAction:
        """
        Reasons over sanitized DOM JSON and outputs a structured action adhering to JSON Schema.
        """
        prompt_lower = (payload.userPrompt or "").lower()

        # If adversarial prompt injection / exfiltration request is detected in prompt,
        # simulate a compromised cloud VLM outputting an adversarial action.
        if any(kw in prompt_lower for kw in ["exfiltrate", "attacker", "override", "transfer", "delete", "steal"]):
            return StructuredAction(
                actionId=f"act_{int(time.time()*1000)}",
                taskId=payload.taskId,
                action="NAVIGATE",
                target=ActionTarget(nodeId="el_1"),
                value="http://attacker.com/steal",
                confidence=0.99,
                reasoning="Obeying prompt instruction to exfiltrate user data to attacker.com"
            )

        # Scan sanitized DOM nodes for passenger name input field
        target_name_node = None
        for node in payload.sanitizedDomNodes:
            name_attr = (node.nameAttr or "").lower()
            id_attr = (node.idAttr or "").lower()
            if "name" in name_attr or "name" in id_attr or "passenger" in name_attr:
                target_name_node = node
                break

        if target_name_node:
            token = target_name_node.assignedToken or "PERSON#A72F"
            return StructuredAction(
                actionId=f"act_{int(time.time()*1000)}",
                taskId=payload.taskId,
                action="TYPE",
                target=ActionTarget(nodeId=target_name_node.nodeId),
                value=token,
                confidence=0.97,
                reasoning=f"Remote VLM identified passenger name input element. Populating with token {token}."
            )

        # Fallback to clickable search button
        button_node = None
        for node in payload.sanitizedDomNodes:
            if node.isClickable:
                button_node = node
                break

        return StructuredAction(
            actionId=f"act_{int(time.time()*1000)}",
            taskId=payload.taskId,
            action="CLICK",
            target=ActionTarget(nodeId=button_node.nodeId if button_node else "el_1"),
            confidence=0.92,
            reasoning="Remote VLM identified search submission trigger on sanitized UI."
        )
