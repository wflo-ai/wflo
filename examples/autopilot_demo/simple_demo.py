"""
Wflo Autopilot Demo - Before vs After

This demo shows the difference between running LLM calls with and without Wflo protection.
"""

import asyncio
import os


def demo_without_wflo():
    """Demo WITHOUT Wflo - No safety net."""
    print("=" * 60)
    print("🔴 WITHOUT WFLO - NO SAFETY NET")
    print("=" * 60)
    print()

    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-fake-key-for-demo"))

        print("Running expensive GPT-4 call...")
        print("Model: gpt-4")
        print("Budget: NONE (unlimited spending!)")
        print()

        # This would normally cost money
        # For demo, we'll just simulate the call
        print("⚠️  Simulating call (requires real API key to execute)")
        print("💸 Estimated cost: $0.15 (no budget enforcement)")
        print("❌ No prediction, no optimization, no safety")
        print()

        # Uncomment below to make real call (requires API key):
        # response = client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[{"role": "user", "content": "Write a short story"}],
        #     max_tokens=500
        # )
        # print(f"Response: {response.choices[0].message.content[:100]}...")

    except Exception as e:
        print(f"❌ Error: {e}")

    print()
    input("Press Enter to continue to the Wflo-protected version...")
    print("\n" * 2)


def demo_with_wflo():
    """Demo WITH Wflo - Full protection."""
    print("=" * 60)
    print("✅ WITH WFLO - FULLY PROTECTED")
    print("=" * 60)
    print()

    try:
        # ============================================
        # THE MAGIC: JUST TWO LINES
        # ============================================
        import wflo

        wflo.init(budget_usd=0.10, auto_optimize=True)  # $0.10 budget
        # ============================================

        print()
        print("Now running the SAME call with Wflo protection...")
        print()

        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-fake-key-for-demo"))

        print("⚠️  Simulating call (requires real API key to execute)")
        print()
        print("Wflo will automatically:")
        print("  1. Predict cost BEFORE execution")
        print("  2. Check against budget ($0.10)")
        print("  3. Auto-optimize (switch gpt-4 → gpt-3.5-turbo)")
        print("  4. Track spending and enforce hard limits")
        print("  5. Self-heal if API fails")
        print()

        # Uncomment below to make real call (requires API key):
        # response = client.chat.completions.create(
        #     model="gpt-4",  # User requested gpt-4
        #     messages=[{"role": "user", "content": "Write a short story"}],
        #     max_tokens=500
        # )
        # print(f"\nResponse: {response.choices[0].message.content[:100]}...")

        print("✅ With Wflo:")
        print("   • Budget enforced: $0.10")
        print("   • Auto-optimized to cheaper model")
        print("   • Full observability")
        print("   • Self-healing on failures")
        print()

    except Exception as e:
        print(f"Error: {e}")


def demo_comparison():
    """Side-by-side comparison."""
    print("\n" * 2)
    print("=" * 60)
    print("📊 COMPARISON SUMMARY")
    print("=" * 60)
    print()

    comparison = [
        ("Feature", "Without Wflo", "With Wflo"),
        ("-" * 20, "-" * 20, "-" * 20),
        ("Budget enforcement", "❌ None", "✅ Hard limit"),
        ("Cost prediction", "❌ None", "✅ Before execution"),
        ("Auto-optimization", "❌ None", "✅ 50-90% savings"),
        ("Self-healing", "❌ None", "✅ Auto-retry"),
        ("Observability", "❌ None", "✅ Full tracing"),
        ("Integration effort", "N/A", "✅ 2 lines of code"),
    ]

    for row in comparison:
        print(f"{row[0]:<25} {row[1]:<25} {row[2]:<25}")

    print()
    print("=" * 60)
    print()


def main():
    """Run the demo."""
    print("\n")
    print("🛡️  WFLO AUTOPILOT DEMO")
    print("The 2-line safety net for AI agents")
    print()

    # Demo 1: Without Wflo
    demo_without_wflo()

    # Demo 2: With Wflo
    demo_with_wflo()

    # Comparison
    demo_comparison()

    print("✅ Demo complete!")
    print()
    print("To use Wflo in your code:")
    print()
    print("    import wflo")
    print("    wflo.init(budget_usd=10.0)")
    print()
    print("    # Your existing code - no changes needed!")
    print()


if __name__ == "__main__":
    main()
