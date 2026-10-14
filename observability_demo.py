#!/usr/bin/env python3
"""
Runnable LLM Observability & LiteLLM Gateway Simulation
-------------------------------------------------------
Demonstrates:
1. Primary Provider Failure & Dynamic Fallback Routing (OpenAI -> Anthropic).
2. Latency Measurement (Start-to-finish timing in ms).
3. Token Budgeting & FinOps cost calculation.
4. Structured Langfuse / OpenTelemetry Observability Event Generation.
"""

import json
import os
import sys
import time
import uuid

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


class MockLiteLLMGateway:
    """
    Simulates LiteLLM routing behavior with failover, latency, and telemetry.
    """
    def __init__(self, primary_model="gpt-4o-mini", fallback_model="claude-3-5-haiku", max_budget_usd=0.01):
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.max_budget_usd = max_budget_usd
        self.cumulative_cost_usd = 0.0

    def call_model_with_fallback(self, prompt: str, user_id: str, simulate_primary_failure: bool = False):
        trace_id = f"trace-{uuid.uuid4().hex[:12]}"
        session_id = f"session-{uuid.uuid4().hex[:8]}"
        start_time = time.perf_counter()

        # Step 1: Pre-call Budget Check
        if self.cumulative_cost_usd >= self.max_budget_usd:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            telemetry = {
                "trace_id": trace_id,
                "user_id": user_id,
                "session_id": session_id,
                "status": "REJECTED_BUDGET_EXCEEDED",
                "error": f"Daily budget of ${self.max_budget_usd:.4f} USD exceeded. Current spend: ${self.cumulative_cost_usd:.4f} USD.",
                "latency_ms": latency_ms,
                "routed_model": None,
                "fallback_triggered": False,
                "cost_usd": 0.0,
            }
            return None, telemetry

        # Step 2: Attempt Primary Model
        routed_model = self.primary_model
        fallback_triggered = False

        if simulate_primary_failure:
            print(f"  [Router Warning] Primary model '{self.primary_model}' threw HTTP 503 Overloaded. Triggering fallback...")
            # Simulate network backoff delay
            time.sleep(0.08)
            routed_model = self.fallback_model
            fallback_triggered = True
            response_text = f"[Response from {routed_model}]: In Scalable Broker, PRIME+ offers 4% p.a. interest with unlimited trading on gettex."
            prompt_tokens = 45
            completion_tokens = 32
            cost = (prompt_tokens / 1000 * 0.001) + (completion_tokens / 1000 * 0.005)
        else:
            time.sleep(0.04)  # Simulate fast primary execution
            response_text = f"[Response from {routed_model}]: Scalable Capital supports both ETF savings plans and individual stock trading."
            prompt_tokens = 45
            completion_tokens = 28
            cost = (prompt_tokens / 1000 * 0.00015) + (completion_tokens / 1000 * 0.00060)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        self.cumulative_cost_usd += cost

        # Step 3: Emit Langfuse-compatible Observability Trace
        telemetry = {
            "trace_id": trace_id,
            "user_id": user_id,
            "session_id": session_id,
            "status": "SUCCESS",
            "prompt": prompt,
            "primary_model": self.primary_model,
            "routed_model": routed_model,
            "fallback_triggered": fallback_triggered,
            "latency_ms": latency_ms,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            "cost_usd": round(cost, 6),
            "cumulative_tenant_spend_usd": round(self.cumulative_cost_usd, 6),
            "tags": ["scalable-fintech-ai", "production-routing", f"model:{routed_model}"],
        }

        return response_text, telemetry


def main():
    print("=" * 80)
    print("🤖 STARTING PRODUCTION LLM OBSERVABILITY & LITELLM GATEWAY DEMO")
    print("=" * 80)

    gateway = MockLiteLLMGateway(
        primary_model="gpt-4o-mini",
        fallback_model="claude-3-5-haiku",
        max_budget_usd=0.000200,  # Low threshold to demonstrate budget cutoff in scenario 3
    )

    # --------------------------------------------------------------------------
    # Scenario 1: Normal Primary Routing
    # --------------------------------------------------------------------------
    print("\n[Scenario 1] 🟢 Investor queries trading plans (Primary Provider Healthy):")
    prompt_1 = "Explain the difference between FREE Broker and PRIME+."
    resp, tele = gateway.call_model_with_fallback(
        prompt=prompt_1,
        user_id="usr_alex_101",
        simulate_primary_failure=False,
    )
    print(f"  Response: {resp}")
    print(f"  Routed Model : {tele['routed_model']} (Fallback Triggered: {tele['fallback_triggered']})")
    print(f"  Latency      : {tele['latency_ms']} ms | Cost: ${tele['cost_usd']:.6f} USD")

    # --------------------------------------------------------------------------
    # Scenario 2: Primary Outage -> Automatic Fallback Switchover
    # --------------------------------------------------------------------------
    print("\n[Scenario 2] 🟡 Primary Provider (OpenAI) Outage -> Automatic Fallback to Anthropic:")
    prompt_2 = "What interest rate is paid on uninvested cash in PRIME+?"
    resp, tele = gateway.call_model_with_fallback(
        prompt=prompt_2,
        user_id="usr_alex_101",
        simulate_primary_failure=True,  # Simulate outage!
    )
    print(f"  Response: {resp}")
    print(f"  Routed Model : {tele['routed_model']} (Fallback Triggered: {tele['fallback_triggered']})")
    print(f"  Latency      : {tele['latency_ms']} ms | Cost: ${tele['cost_usd']:.6f} USD")

    # --------------------------------------------------------------------------
    # Scenario 3: Token Budgeting & FinOps Guardrails
    # --------------------------------------------------------------------------
    print("\n[Scenario 3] 🔴 User exceeds daily token/cost budget (FinOps Protection):")
    prompt_3 = "Generate a comprehensive analysis of all DAX 40 constituents."
    resp, tele = gateway.call_model_with_fallback(
        prompt=prompt_3,
        user_id="usr_alex_101",
        simulate_primary_failure=False,
    )
    if resp is None:
        print(f"  🛑 Request Blocked: {tele['error']}")
        print(f"  Latency: {tele['latency_ms']} ms (Zero LLM API charges incurred)")

    # --------------------------------------------------------------------------
    # Scenario 4: Langfuse Observability JSON Event
    # --------------------------------------------------------------------------
    print("\n[Scenario 4] 📡 Sample Langfuse / OpenTelemetry Ingestion Payload:")
    print(json.dumps(tele, indent=2))

    print("\n" + "=" * 80)
    print("✅ High-availability LLM routing, fallback, and observability verified!")
    print("=" * 80)


if __name__ == "__main__":
    main()
