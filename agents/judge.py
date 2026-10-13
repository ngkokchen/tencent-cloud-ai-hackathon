"""Judge agent — neutral arbiter that weighs both cases and issues a ruling."""

import json

from agents.base import BaseAgent, load_prompt
from evidence.loaders import CaseData
from models.argument import Argument
from models.ruling import Ruling
from models.argument import PolicyCitation


class Judge(BaseAgent):
    """
    Neutral arbiter. Receives both advocates' arguments, independently
    verifies key evidence via tools, applies policy, and outputs a
    structured Ruling with dual explanations.
    """

    def __init__(self, llm, log):
        prompt = load_prompt("judge")
        super().__init__(
            name="judge",
            system_prompt=prompt,
            llm=llm,
            log=log,
        )

    def run(
        self,
        case: CaseData,
        rider_argument: Argument,
        driver_argument: Argument,
    ) -> Ruling:
        """
        Execute the judge pipeline:
        1. Build a summary of both advocates' arguments
        2. LLM decides which tools to call for independent verification
        3. Execute tools (logged to conversation log)
        4. LLM produces the ruling with dual explanations
        """
        trip_id = case.trip.get("ride_id", case.dispute.get("ride_id", ""))
        rider_id = case.rider_profile.get("rider_id", "")
        driver_id = case.driver_profile.get("driver_id", "")
        dispute_type = case.dispute.get("dispute_type", "")

        # ── Step 1: Build summary of both arguments ──────────
        args_summary = self._build_arguments_summary(
            case, rider_argument, driver_argument
        )

        # ── Step 2: LLM decides which tools to call for verification ──
        self._log(
            "reasoning",
            "Reviewing both advocates' arguments and selecting verification tools...",
        )
        selected_tools = self.llm_decide_tools(args_summary)

        # ── Step 3: Execute verification tools ──────────────
        tool_results = self._execute_tools(
            selected_tools, trip_id, rider_id, driver_id, dispute_type
        )

        # ── Step 4: LLM produces ruling ─────────────────────
        results_text = self._format_tool_results(tool_results)
        ruling_prompt = (
            f"## Both Advocates' Arguments\n{args_summary}\n\n"
            f"## Independent Verification Results\n{results_text}\n\n"
            f"## Your Task\n"
            f"You are the Judge. Weigh both arguments against the verified "
            f"evidence and company policy. Apply the relevant policy clauses "
            f"and issue your ruling. Output the JSON ruling as specified in "
            f"your system prompt. Remember to produce separate explanations "
            f"for the rider and the driver."
        )

        result = self.llm_analyze(ruling_prompt, temperature=0.2)

        # ── Step 5: Parse into Ruling model ──────────────────
        ruling = Ruling(
            ruling=result.get("ruling", "no_action"),
            action=result.get("action", ""),
            amount=float(result.get("amount", 0.0)),
            confidence=max(0.0, min(1.0, float(result.get("confidence", 0.5)))),
            reasoning_for_rider=result.get("reasoning_for_rider", ""),
            reasoning_for_driver=result.get("reasoning_for_driver", ""),
            policy_applied=[
                PolicyCitation(**p) for p in result.get("policy_applied", [])
                if isinstance(p, dict)
            ],
            tools_called=selected_tools,
            verification_notes=result.get("verification_notes", ""),
        )

        # Log the final ruling
        self._log(
            "ruling",
            json.dumps(result, indent=2, ensure_ascii=False),
            recipient="all",
            metadata={
                "ruling": ruling.ruling,
                "action": ruling.action,
                "amount": ruling.amount,
                "confidence": ruling.confidence,
            },
        )

        return ruling

    def _build_arguments_summary(
        self,
        case: CaseData,
        rider_arg: Argument,
        driver_arg: Argument,
    ) -> str:
        """Build a summary of both advocates' arguments for the LLM."""

        # Rider advocate's case
        rider_evidence = "\n".join(
            f"  - [{e.source}] {e.fact} (ref: {e.reference})"
            for e in rider_arg.evidence
        )
        rider_policy = "\n".join(
            f"  - {p.clause}: {p.title} — {p.relevance}"
            for p in rider_arg.policy_cited
        )

        # Driver advocate's case
        driver_evidence = "\n".join(
            f"  - [{e.source}] {e.fact} (ref: {e.reference})"
            for e in driver_arg.evidence
        )
        driver_policy = "\n".join(
            f"  - {p.clause}: {p.title} — {p.relevance}"
            for p in driver_arg.policy_cited
        )

        return (
            f"## Dispute\n"
            f"ID: {case.dispute.get('dispute_id', 'N/A')}\n"
            f"Type: {case.dispute.get('dispute_type', 'N/A')}\n"
            f"Trip ID: {case.trip.get('ride_id', 'N/A')}\n"
            f"Rider claim: {case.dispute.get('claim', 'N/A')}\n\n"

            f"## Rider Advocate's Argument\n"
            f"Claim: {rider_arg.claim}\n"
            f"Requested remedy: {rider_arg.requested_remedy} "
            f"${rider_arg.requested_amount:.2f}\n"
            f"Evidence:\n{rider_evidence}\n"
            f"Policy cited:\n{rider_policy}\n"
            f"Reasoning: {rider_arg.reasoning}\n\n"

            f"## Driver Advocate's Argument\n"
            f"Claim: {driver_arg.claim}\n"
            f"Requested remedy: {driver_arg.requested_remedy} "
            f"${driver_arg.requested_amount:.2f}\n"
            f"Evidence:\n{driver_evidence}\n"
            f"Policy cited:\n{driver_policy}\n"
            f"Reasoning: {driver_arg.reasoning}\n\n"

            f"## Key IDs for verification\n"
            f"Trip ID: {case.trip.get('ride_id', 'N/A')}\n"
            f"Rider ID: {case.rider_profile.get('rider_id', 'N/A')}\n"
            f"Driver ID: {case.driver_profile.get('driver_id', 'N/A')}\n"
            f"Dispute type: {case.dispute.get('dispute_type', 'N/A')}"
        )

    def _execute_tools(
        self,
        tool_names: list[str],
        trip_id: str,
        rider_id: str,
        driver_id: str,
        dispute_type: str,
    ) -> dict:
        """Execute verification tools with the correct arguments."""
        results = {}
        for name in tool_names:
            if name == "get_user_history":
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
