"""Rider Advocate agent — argues the rider's case with a pro-rider bias."""

import json

from agents.base import BaseAgent, load_prompt
from evidence.loaders import CaseData
from models.argument import Argument, EvidenceItem, PolicyCitation


class RiderAdvocate(BaseAgent):
    """
    Advocates for the rider. Decides which tools to call, gathers evidence,
    and produces a structured Argument favoring the rider's position.
    """

    def __init__(self, llm, log):
        prompt = load_prompt("rider_advocate")
        super().__init__(
            name="rider_advocate",
            system_prompt=prompt,
            llm=llm,
            log=log,
        )

    def run(self, case: CaseData) -> Argument:
        """
        Execute the advocate pipeline:
        1. Build a dispute summary
        2. LLM decides which tools to call
        3. Execute tools (logged to conversation log)
        4. LLM analyzes results and produces structured argument
        """
        trip_id = case.trip.get("ride_id", case.dispute.get("ride_id", ""))
        rider_id = case.rider_profile.get("rider_id", "")
        driver_id = case.driver_profile.get("driver_id", "")
        dispute_type = case.dispute.get("dispute_type", "")

        summary = self._build_summary(case)

        # ── Step 1: LLM decides which tools to call ──────────
        self._log("reasoning", "Reviewing dispute and selecting tools...")
        selected_tools = self.llm_decide_tools(summary)

        # ── Step 2: Execute selected tools ──────────────────
        tool_results = self._execute_tools(
            selected_tools, trip_id, rider_id, driver_id, dispute_type
        )

        # ── Step 3: LLM analyzes evidence and builds argument ─
        results_text = self._format_tool_results(tool_results)
        analysis_prompt = (
            f"## Dispute\n{summary}\n\n"
            f"## Tool Results\n{results_text}\n\n"
            f"## Your Task\n"
            f"Analyze the evidence above and build your structured argument "
            f"for the rider. Output the JSON argument as specified in your "
            f"system prompt instructions. Remember: you advocate for the rider."
        )

        result = self.llm_analyze(analysis_prompt, temperature=0.3)

        # ── Step 4: Parse into Argument model ───────────────
        argument = Argument(
            agent="rider_advocate",
            claim=result.get("claim", ""),
            evidence=[
                EvidenceItem(**e) for e in result.get("evidence", [])
                if isinstance(e, dict)
            ],
            policy_cited=[
                PolicyCitation(**p) for p in result.get("policy_cited", [])
                if isinstance(p, dict)
            ],
            requested_remedy=result.get("requested_remedy", "no_action"),
            requested_amount=float(result.get("requested_amount", 0.0)),
            reasoning=result.get("reasoning", ""),
            tools_called=selected_tools,
            tool_reasoning=result.get("tool_reasoning", ""),
        )

        # Log the final argument
        self._log(
            "argument",
            json.dumps(result, indent=2, ensure_ascii=False),
            metadata={
                "claim": argument.claim,
                "remedy": argument.requested_remedy,
                "amount": argument.requested_amount,
                "evidence_count": len(argument.evidence),
            },
        )

        return argument

    def _build_summary(self, case: CaseData) -> str:
        """Build a concise dispute summary for the LLM."""
        d = case.dispute
        t = case.trip
        f = case.fare_breakdown
        return (
            f"Dispute ID: {d.get('dispute_id', 'N/A')}\n"
            f"Type: {d.get('dispute_type', 'N/A')}\n"
            f"Filed by: {d.get('filed_by', 'N/A')}\n"
            f"Claim: {d.get('claim', 'N/A')}\n"
            f"Requested remedy: {d.get('requested_remedy', {}).get('type', 'N/A')} "
            f"${d.get('requested_remedy', {}).get('amount', 0):.2f}\n"
            f"Trip ID: {t.get('ride_id', 'N/A')}\n"
            f"Pickup: {t.get('pickup', {}).get('address', 'N/A')}\n"
            f"Dropoff: {t.get('dropoff', {}).get('address', 'N/A')}\n"
            f"Status: {t.get('status', 'N/A')}\n"
            f"Est. distance: {t.get('estimated_distance_km', 0)}km, "
            f"actual: {t.get('actual_distance_km', 0)}km\n"
            f"Est. duration: {t.get('estimated_duration_min', 0)}min, "
            f"actual: {t.get('actual_duration_min', 0)}min\n"
            f"Fare total: ${f.get('total', 0):.2f} "
            f"(expected optimal: ${f.get('expected_total_optimal', 0):.2f})\n"
            f"Rider ID: {case.rider_profile.get('rider_id', 'N/A')}\n"
            f"Driver ID: {case.driver_profile.get('driver_id', 'N/A')}"
        )

    def _execute_tools(
        self,
        tool_names: list[str],
        trip_id: str,
        rider_id: str,
        driver_id: str,
        dispute_type: str,
    ) -> dict:
        """Execute selected tools with the correct arguments."""
        results = {}
        for name in tool_names:
            if name == "get_user_history":
                # Call for both parties — both are relevant
                r = self.call_tool(name, user_id=rider_id)
                results["get_user_history(rider)"] = r
                d = self.call_tool(name, user_id=driver_id)
                results["get_user_history(driver)"] = d
            elif name == "get_route_analysis":
                results[name] = self.call_tool(name, trip_id=trip_id)
            elif name == "get_chat_log":
                results[name] = self.call_tool(name, trip_id=trip_id)
            elif name == "get_fare_breakdown":
                results[name] = self.call_tool(name, trip_id=trip_id)
            elif name == "get_policy":
                results[name] = self.call_tool(name, dispute_type=dispute_type)
            else:
                self._log("reasoning", f"Skipping unknown tool '{name}'")
        return results
