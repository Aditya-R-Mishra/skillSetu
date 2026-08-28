from datetime import datetime, timezone
from typing import Dict, Any

def sync_with_igot_karmayogi(competency_area: str, user_id: str) -> Dict[str, Any]:
    """
    Simulates integration adapter with India's iGOT Karmayogi capacity building portal.
    Maps identified competency gap to corresponding course enrollment protocol.
    """
    code_prefix = competency_area[:3].upper() if len(competency_area) >= 3 else "GEN"
    igot_course_code = f"IGOT-{code_prefix}-101"
    
    return {
        "status": "synced",
        "competency_area": competency_area,
        "igot_course_code": igot_course_code,
        "course_title": f"IGOT {competency_area} Capacity Building Module",
        "message": f"Successfully registered competency gap for '{competency_area}' on iGOT Karmayogi ecosystem. Recommended course [{igot_course_code}] assigned to learner profile.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
