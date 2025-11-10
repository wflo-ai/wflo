---
layout: default
title: Use Cases
description: "Real-world use cases and applications for Wflo in production environments"
---

<div class="container" style="margin-top: 3rem;">

# Use Cases

Real-world applications of Wflo across different industries and scenarios.

---

## Financial Services

### Fraud Detection & Investigation

AI agents analyze transactions for fraud patterns, but require approval before blocking accounts.

**Key Requirements:**
- Human approval before blocking customer accounts
- Complete audit trail for compliance
- Cost controls to prevent runaway analysis
- Rollback capability if false positives occur

**Wflo Solution:**

```python
from wflo import Workflow, ApprovalPolicy

workflow = Workflow("fraud-detection")
workflow.set_budget(max_cost_usd=100.00)

@workflow.step
async def analyze_transactions(context):
    """Analyze recent transactions for fraud patterns"""
    transactions = await context.db.query(
        "SELECT * FROM transactions WHERE processed=false"
    )

    # AI analysis of patterns
    analysis = await context.llm.analyze(
        model="gpt-4",
        data=transactions,
        prompt="Identify suspicious transaction patterns"
    )

    return {"suspicious": analysis.flagged_transactions}

@workflow.step(
    depends_on=["analyze_transactions"],
    approval=ApprovalPolicy(
        required=True,
        approvers=["fraud-team", "compliance"],
        timeout_seconds=3600,
        notify=["slack://fraud-alerts", "pagerduty://fraud-team"]
    ),
    rollback_enabled=True
)
async def block_suspicious_accounts(context):
    """Block accounts flagged as suspicious (requires approval)"""
    suspicious = context.steps["analyze_transactions"].output["suspicious"]

    # Pauses here for human review
    for account_id in suspicious:
        await context.db.execute(
            "UPDATE accounts SET status='blocked' WHERE id=?",
            account_id
        )

    return {"blocked_count": len(suspicious)}
```

**Benefits:**
- ✅ No false positive account blocks without human review
- ✅ Complete compliance audit trail
- ✅ Cost-controlled AI analysis
- ✅ Rollback if needed

---

## Healthcare

### Clinical Decision Support

AI assists with diagnosis and treatment recommendations, with mandatory physician approval.

**Key Requirements:**
- HIPAA compliance with full audit logs
- Physician approval for all treatment recommendations
- Patient data must stay within secure boundaries
- Cost tracking for budget planning

**Wflo Solution:**

```python
workflow = Workflow("clinical-decision-support")

# Enforce sandboxing for patient data
workflow.configure_sandbox(
    SandboxConfig(
        enabled=True,
        network_enabled=False,  # No data exfiltration
        readonly_root=True
    )
)

@workflow.step
async def analyze_patient_data(context):
    """Analyze patient records"""
    patient_id = context.inputs["patient_id"]

    # PHI stays in sandbox
    records = await context.db.query(
        "SELECT * FROM patient_records WHERE patient_id=?",
        patient_id
    )

    analysis = await context.llm.analyze(
        model="gpt-4-medical",  # Specialized medical model
        data=records,
        prompt="Analyze symptoms and suggest differential diagnosis"
    )

    return {"diagnosis": analysis.diagnosis, "confidence": analysis.confidence}

@workflow.step(
    depends_on=["analyze_patient_data"],
    approval=ApprovalPolicy(
        required=True,
        approvers=["attending-physician"],
        timeout_seconds=7200,
        notify=["pager://on-call-physician"]
    )
)
async def recommend_treatment(context):
    """Generate treatment plan (requires physician approval)"""
    diagnosis = context.steps["analyze_patient_data"].output["diagnosis"]

    treatment_plan = await context.llm.complete(
        model="gpt-4-medical",
        prompt=f"Recommend treatment plan for: {diagnosis}"
    )

    # Physician reviews and approves before proceeding
    return {"treatment_plan": treatment_plan.text}
```

**Benefits:**
- ✅ HIPAA-compliant with full audit logs
- ✅ Physician maintains final authority
- ✅ Patient data never leaves secure environment
- ✅ Cost tracking for hospital budget

---

## E-commerce

### Customer Service Automation

AI handles customer inquiries but requires approval for refunds or account changes.

**Key Requirements:**
- Auto-handle simple queries
- Human approval for refunds > $100
- Cost limits per customer interaction
- Track customer satisfaction

**Wflo Solution:**

```python
from wflo import Policy, Condition

workflow = Workflow("customer-service")
workflow.set_budget(max_cost_usd=5.00)  # Per customer interaction

# Dynamic approval based on refund amount
workflow.add_policy(
    Policy(
        name="large_refund_approval",
        condition=Condition("refund_amount > 100"),
        actions=[
            RequireApproval(approvers=["customer-service-manager"]),
            Notify("slack://cs-managers")
        ]
    )
)

@workflow.step
async def understand_query(context):
    """Understand customer inquiry"""
    customer_message = context.inputs["message"]

    intent = await context.llm.classify(
        model="gpt-3.5-turbo",
        text=customer_message,
        categories=["refund", "question", "complaint", "other"]
    )

    return {"intent": intent.category, "details": intent.details}

@workflow.step(depends_on=["understand_query"])
async def handle_query(context):
    """Handle based on intent"""
    intent = context.steps["understand_query"].output["intent"]

    if intent == "question":
        # Auto-handle questions
        response = await context.llm.answer(
            question=context.inputs["message"],
            knowledge_base=context.kb
        )
        return {"response": response, "refund_amount": 0}

    elif intent == "refund":
        # Calculate refund amount
        order_id = context.inputs["order_id"]
        refund_amount = await context.db.get_refund_amount(order_id)

        # If > $100, requires approval (policy triggers)
        if refund_amount > 100:
            # Pauses for approval
            await context.db.process_refund(order_id, refund_amount)

        return {"response": "Refund processed", "refund_amount": refund_amount}

@workflow.step(depends_on=["handle_query"])
async def collect_feedback(context):
    """Ask for customer satisfaction"""
    await context.email.send(
        to=context.inputs["customer_email"],
        subject="How did we do?",
        body="Please rate your support experience..."
    )

    return {"feedback_requested": True}
```

**Benefits:**
- ✅ Fast response for simple queries
- ✅ Human oversight for expensive operations
- ✅ Cost control per interaction
- ✅ Customer satisfaction tracking

---

## Data Engineering

### ETL Pipeline with Validation

AI-powered data transformation with validation gates and rollback on errors.

**Key Requirements:**
- Transform large datasets efficiently
- Validate transformations before applying
- Rollback on data quality issues
- Track compute costs

**Wflo Solution:**

```python
workflow = Workflow("etl-pipeline")

@workflow.step
async def extract_data(context):
    """Extract data from source"""
    source_url = context.inputs["source_url"]

    data = await context.http.fetch(source_url)

    context.logger.info("data_extracted", rows=len(data))
    return {"raw_data": data}

@workflow.step(depends_on=["extract_data"])
async def transform_data(context):
    """Transform data with AI assistance"""
    raw_data = context.steps["extract_data"].output["raw_data"]

    # AI figures out transformation logic
    transformed = await context.llm.transform(
        model="gpt-4",
        data=raw_data,
        instructions="Normalize addresses and extract key fields"
    )

    return {"transformed_data": transformed}

@workflow.step(depends_on=["transform_data"])
async def validate_quality(context):
    """Validate data quality"""
    transformed = context.steps["transform_data"].output["transformed_data"]

    # AI validates quality
    validation = await context.llm.validate(
        model="gpt-3.5-turbo",
        data=transformed,
        rules=[
            "All addresses properly formatted",
            "No missing required fields",
            "Data types correct"
        ]
    )

    if not validation.passed:
        raise ValueError(f"Quality check failed: {validation.issues}")

    return {"validation": "passed"}

@workflow.step(
    depends_on=["validate_quality"],
    approval=ApprovalPolicy(
        required=True,
        approvers=["data-team"],
        notify=["slack://data-eng"]
    ),
    rollback_enabled=True
)
async def load_to_warehouse(context):
    """Load to data warehouse (requires approval + rollback)"""
    transformed = context.steps["transform_data"].output["transformed_data"]

    # Snapshot before loading
    await context.db.bulk_insert(
        table="production.customers",
        data=transformed
    )

    return {"loaded_rows": len(transformed)}
```

**Benefits:**
- ✅ AI-powered transformation logic
- ✅ Automated quality validation
- ✅ Human review before production load
- ✅ Rollback on issues

---

## DevOps

### Infrastructure Automation

AI suggests infrastructure changes with approval gates and rollback capability.

**Key Requirements:**
- AI analyzes infrastructure and suggests optimizations
- Require approval before applying changes
- Rollback on deployment failures
- Track cloud costs

**Wflo Solution:**

```python
workflow = Workflow("infrastructure-optimization")

@workflow.step
async def analyze_infrastructure(context):
    """Analyze current infrastructure"""
    # Get current state
    infra_state = await context.terraform.get_state()

    # AI analyzes for optimizations
    recommendations = await context.llm.analyze(
        model="gpt-4",
        data=infra_state,
        prompt="""
        Analyze this infrastructure and recommend:
        1. Cost optimizations
        2. Security improvements
        3. Performance enhancements
        """
    )

    return {"recommendations": recommendations}

@workflow.step(
    depends_on=["analyze_infrastructure"],
    approval=ApprovalPolicy(
        required=True,
        approvers=["sre-team", "security-team"],
        timeout_seconds=7200,
        notify=["slack://sre", "pagerduty://sre-oncall"]
    )
)
async def generate_terraform(context):
    """Generate Terraform config (requires approval)"""
    recommendations = context.steps["analyze_infrastructure"].output

    # AI generates Terraform code
    terraform_code = await context.llm.generate_code(
        model="gpt-4",
        language="terraform",
        requirements=recommendations["recommendations"]
    )

    return {"terraform": terraform_code}

@workflow.step(
    depends_on=["generate_terraform"],
    rollback_enabled=True
)
async def apply_changes(context):
    """Apply infrastructure changes with rollback"""
    terraform = context.steps["generate_terraform"].output["terraform"]

    # Apply changes (automatic snapshot)
    result = await context.terraform.apply(terraform)

    # If fails, automatically rolls back
    return {"applied": True, "resources": result.resources}
```

**Benefits:**
- ✅ AI-suggested optimizations
- ✅ Multi-team approval process
- ✅ Automatic rollback on failure
- ✅ Infrastructure as code

---

## Content Moderation

### Automated Content Review

AI reviews user-generated content with human review for edge cases.

**Key Requirements:**
- Fast automated review for clear cases
- Human review for ambiguous content
- Cost control for large volumes
- Audit trail for decisions

**Wflo Solution:**

```python
from wflo import Policy, Condition

workflow = Workflow("content-moderation")
workflow.set_budget(max_cost_usd=0.10)  # Per content item

# Auto-approve obvious safe content
workflow.add_policy(
    Policy(
        name="auto_approve_safe",
        condition=Condition("confidence > 0.95 AND verdict == 'safe'"),
        actions=[AutoApprove()]
    )
)

# Require human review for ambiguous cases
workflow.add_policy(
    Policy(
        name="human_review_ambiguous",
        condition=Condition("confidence < 0.80"),
        actions=[
            RequireApproval(approvers=["moderation-team"]),
            Notify("slack://moderation")
        ]
    )
)

@workflow.step
async def analyze_content(context):
    """Analyze content for policy violations"""
    content = context.inputs["content"]

    analysis = await context.llm.moderate(
        model="gpt-4",
        content=content,
        policies=[
            "No hate speech",
            "No violence",
            "No spam",
            "No adult content"
        ]
    )

    return {
        "verdict": analysis.verdict,  # safe, review, block
        "confidence": analysis.confidence,
        "reasoning": analysis.reasoning
    }

@workflow.step(depends_on=["analyze_content"])
async def take_action(context):
    """Take action based on verdict"""
    analysis = context.steps["analyze_content"].output

    if analysis["verdict"] == "block":
        # Auto-block obvious violations
        await context.db.execute(
            "UPDATE content SET status='blocked' WHERE id=?",
            context.inputs["content_id"]
        )
        return {"action": "blocked"}

    elif analysis["confidence"] < 0.80:
        # Ambiguous - requires human review (policy triggers)
        # Execution pauses here
        decision = context.approval.decision

        if decision == "reject":
            await context.db.execute(
                "UPDATE content SET status='blocked' WHERE id=?",
                context.inputs["content_id"]
            )
        return {"action": decision}

    else:
        # Safe - auto-approve
        await context.db.execute(
            "UPDATE content SET status='approved' WHERE id=?",
            context.inputs["content_id"]
        )
        return {"action": "approved"}
```

**Benefits:**
- ✅ Fast automated moderation
- ✅ Human review for edge cases
- ✅ Cost-controlled per item
- ✅ Audit trail for compliance

---

## Research & Academia

### Automated Literature Review

AI analyzes research papers with human validation of findings.

**Key Requirements:**
- Process large numbers of papers
- Cost control for API usage
- Human validation of conclusions
- Reproducible results

**Wflo Solution:**

```python
workflow = Workflow("literature-review")
workflow.set_budget(max_cost_usd=50.00)

@workflow.step
async def fetch_papers(context):
    """Fetch relevant papers"""
    query = context.inputs["research_query"]

    papers = await context.api.search_papers(
        query=query,
        limit=100
    )

    return {"papers": papers}

@workflow.step(depends_on=["fetch_papers"])
async def analyze_papers(context):
    """Analyze each paper"""
    papers = context.steps["fetch_papers"].output["papers"]

    analyses = []
    for paper in papers:
        analysis = await context.llm.analyze(
            model="gpt-4",
            data=paper,
            prompt="""
            Analyze this research paper:
            1. Key findings
            2. Methodology
            3. Relevance to query
            4. Citations to follow up
            """
        )
        analyses.append(analysis)

    return {"analyses": analyses}

@workflow.step(depends_on=["analyze_papers"])
async def synthesize_findings(context):
    """Synthesize overall findings"""
    analyses = context.steps["analyze_papers"].output["analyses"]

    synthesis = await context.llm.synthesize(
        model="gpt-4",
        data=analyses,
        prompt="Synthesize key themes and conclusions across all papers"
    )

    return {"synthesis": synthesis}

@workflow.step(
    depends_on=["synthesize_findings"],
    approval=ApprovalPolicy(
        required=True,
        approvers=["principal-investigator"],
        notify=["email://pi@university.edu"]
    )
)
async def publish_findings(context):
    """Publish findings (requires PI approval)"""
    synthesis = context.steps["synthesize_findings"].output["synthesis"]

    # PI reviews before publication
    await context.publish(synthesis)

    return {"published": True}
```

**Benefits:**
- ✅ Process hundreds of papers automatically
- ✅ Cost-controlled analysis
- ✅ Human validation of conclusions
- ✅ Reproducible research workflow

---

## Next Steps

- [Features](features) - Explore all Wflo features
- [Getting Started](getting-started) - Build your first workflow
- [Examples](examples) - More code examples
- [Architecture](architecture) - How Wflo works
</div>
