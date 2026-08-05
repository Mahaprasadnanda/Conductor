import json
from fastapi import Response

class FallbackPolicy:
    @staticmethod
    def execute(fallback_response: dict, status_code: int = 503) -> Response:
        """
        Returns a configured JSON fallback response when the circuit is OPEN.
        """
        return Response(
            content=json.dumps(fallback_response),
            status_code=status_code,
            media_type="application/json"
        )
