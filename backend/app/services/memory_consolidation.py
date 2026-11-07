"""Long-Term Memory Consolidation and Context Extraction Service."""
import re
from typing import Any, Dict, List
from app.agents.orchestrator import orchestrator
from app.core.logging import get_audit_logger, logger
from app.memory.manager import memory_manager

audit_logger = get_audit_logger()


class MemoryConsolidator:
    """Extracts persistent facts, preferences, and developer directives from conversation history."""

    DIRECTIVE_PATTERNS = [
        (r"(?:i prefer|preference is)\s+([^.]+)", "preference"),
        (r"(?:my stack is|we use|tech stack includes)\s+([^.]+)", "technology_stack"),
        (r"(?:my role is|i am a)\s+([^.]+)", "operator_role"),
        (r"(?:always use|strictly use)\s+([^.]+)", "operating_directive"),
        (r"(?:target environment is|deploy on)\s+([^.]+)", "target_environment"),
    ]

    def extract_and_consolidate(
        self,
        conversation_id: str,
        messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Analyzes turns and persists extracted knowledge into long-term memory."""
        extracted: List[Dict[str, Any]] = []

        for msg in messages:
            if msg.get("role") != "user":
                continue

            content = msg.get("content", "")
            for pattern, key in self.DIRECTIVE_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    extracted_text = match.group(1).strip()
                    if len(extracted_text) > 3:
                        mem_item = memory_manager.store_memory(
                            category="preferences" if "preference" in key else "profile",
                            key=key,
                            content=extracted_text,
                            importance=3,
                        )
                        extracted.append({
                            "key": key,
                            "category": mem_item.category,
                            "content": extracted_text,
                        })

        if extracted:
            audit_logger.info(f"Consolidated {len(extracted)} long-term memory items from conv '{conversation_id}'")
            orchestrator.log_activity(
                agent_id="personal_agent",
                action="Memory Consolidated",
                details=f"Extracted {len(extracted)} persistent insights from conversation {conversation_id[:8]}",
                status="completed",
            )

        return {
            "conversation_id": conversation_id,
            "extracted_count": len(extracted),
            "memories": extracted,
        }


memory_consolidator = MemoryConsolidator()
