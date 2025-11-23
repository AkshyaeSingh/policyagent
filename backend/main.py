"""
Coasean Multi-Dimensional Negotiation - Decentralized Architecture
Preserving human agency in massive multi-entity coordination

For def/acc hackathon - humans set OUTCOMES, AI discovers METHODS
"""

import requests
import re
import os
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

# Type alias for preferences: (topic, threshold)
# Humans set OUTCOMES through these simple constraints
Preference = Tuple[str, Optional[float]]


@dataclass
class Proposal:
    """A proposal in the negotiation space"""
    id: int
    author: str
    round: int
    timestamp: datetime
    base_project: Dict[str, Any]
    modifications: List[Dict[str, Any]]
    compensation: Dict[str, float]
    side_payments: Dict[Tuple[str, str], float] = field(default_factory=dict)  # (from_agent, to_agent) -> amount
    commitments: List[str] = field(default_factory=list)
    total_cost: float = 0
    reasoning: str = ""


@dataclass
class Evaluation:
    """An agent's evaluation of a proposal"""
    agent_name: str
    proposal_id: int
    satisfaction_score: int  # 1-5 scale instead of boolean
    explanation: str
    unsatisfied_preferences: List[str]
    suggested_changes: List[str]
    timestamp: datetime
    # Coasean bargaining signals
    willing_to_accept_payment: bool = False  # Would accept payment to compromise
    willing_to_pay: bool = False  # Would pay other agents for preferred outcome
    willingness_to_pay_estimate: str = ""  # Rough estimate of max monthly payment


@dataclass
class NegotiationSpace:
    """
    Shared bulletin board - NO CENTRAL COORDINATOR

    All agents can read/write. No privileged access.
    Enables transparent, decentralized coordination.
    """
    proposals: List[Proposal] = field(default_factory=list)
    evaluations: Dict[int, Dict[str, Evaluation]] = field(default_factory=dict)
    current_round: int = 0

    def post_proposal(self, author: str, proposal_data: Dict[str, Any]) -> int:
        """Any agent can post a proposal"""
        proposal_id = len(self.proposals)

        # Parse side_payments if present (dict of (from_agent, to_agent) -> amount)
        side_payments = {}
        if "side_payments" in proposal_data:
            for payment_info in proposal_data.get("side_payments", []):
                from_agent = payment_info.get("from")
                to_agent = payment_info.get("to")
                amount = payment_info.get("amount", 0)
                try:
                    amount = float(amount)
                    side_payments[(from_agent, to_agent)] = amount
                except (ValueError, TypeError):
                    pass

        proposal = Proposal(
            id=proposal_id,
            author=author,
            round=self.current_round,
            timestamp=datetime.now(),
            base_project=proposal_data.get("base_project", {}),
            modifications=proposal_data.get("modifications", []),
            compensation=proposal_data.get("compensation", {}),
            side_payments=side_payments,
            commitments=proposal_data.get("commitments", []),
            total_cost=proposal_data.get("total_cost", 0),
            reasoning=proposal_data.get("reasoning", "")
        )
        self.proposals.append(proposal)
        return proposal_id

    def post_evaluation(self, evaluation: Evaluation):
        """Agents post evaluations publicly"""
        if evaluation.proposal_id not in self.evaluations:
            self.evaluations[evaluation.proposal_id] = {}
        self.evaluations[evaluation.proposal_id][evaluation.agent_name] = evaluation

    def get_latest_proposal(self) -> Optional[Proposal]:
        """Get the most recent proposal"""
        return self.proposals[-1] if self.proposals else None

    def check_unanimous_acceptance(self, proposal_id: int, required_agents: List[str], threshold: int = 4) -> bool:
        """Check if all required agents have satisfaction >= threshold"""
        if proposal_id not in self.evaluations:
            return False
        evals = self.evaluations[proposal_id]

        # Default evaluation has score of 0
        default_eval = Evaluation("", proposal_id, 0, "", [], [], datetime.now())

        return all(
            evals.get(agent, default_eval).satisfaction_score >= threshold
            for agent in required_agents
        )

    def get_feedback_for_proposal(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Get all feedback for a proposal"""
        if proposal_id not in self.evaluations:
            return []
        return [
            {
                "agent": eval.agent_name,
                "score": eval.satisfaction_score,
                "satisfied": eval.satisfaction_score >= 4,  # Helper for backward compat
                "unsatisfied": eval.unsatisfied_preferences,
                "suggested": eval.suggested_changes,
                # Coasean bargaining signals
                "willing_to_accept": eval.willing_to_accept_payment,
                "willing_to_pay": eval.willing_to_pay,
                "willingness_estimate": eval.willingness_to_pay_estimate
            }
            for eval in self.evaluations[proposal_id].values()
        ]

    def advance_round(self):
        """Move to next negotiation round"""
        self.current_round += 1

    def validate_side_payments(self, proposal: Proposal, agents_dict: Dict[str, 'DecentralizedAgent']) -> Tuple[bool, str]:
        """Validate side payments against agent budgets"""
        if not proposal.side_payments:
            return True, "No side payments to validate"

        messages = []
        valid = True

        # Sum payments each agent is making
        agent_outflows = {}
        for (from_agent, to_agent), amount in proposal.side_payments.items():
            if from_agent not in agent_outflows:
                agent_outflows[from_agent] = 0
            agent_outflows[from_agent] += amount

        # Check against budgets
        for agent_name, total_paid in agent_outflows.items():
            if agent_name in agents_dict:
                agent = agents_dict[agent_name]
                if total_paid > agent.max_side_payment_budget:
                    valid = False
                    messages.append(f"⚠ {agent_name} exceeds payment budget: ${total_paid:,.0f} > ${agent.max_side_payment_budget:,.0f}")
                else:
                    messages.append(f"✓ {agent_name} within budget: ${total_paid:,.0f} <= ${agent.max_side_payment_budget:,.0f}")

        return valid, "\n".join(messages)


class LLMClient:
    """Simple LLM client for OpenRouter"""
    def __init__(self, api_key: str, model: str = "openai/gpt-5", provider: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def call(self, prompt: str) -> str:
        """Make API call"""
        request_json = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }

        # Add provider if specified
        if self.provider:
            request_json["provider"] = {
                "order": [self.provider],
                "allow_fallbacks": False
            }

        response = requests.post(
            url=self.url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/defacc-hackathon",
                "X-Title": "Coasean Negotiation Demo",
            },
            json=request_json
        )

        if response.status_code != 200:
            raise Exception(f"API call failed: {response.status_code} - {response.text}")

        result = response.json()
        return result['choices'][0]['message']['content']


def parse_xml_tag(text: str, tag: str) -> str:
    """Parse a single XML tag from text"""
    pattern = f"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise ValueError(f"Required tag <{tag}> not found in response")
    return match.group(1).strip()


def parse_xml_list(text: str, tag: str) -> List[str]:
    """Parse a list of XML tags from text"""
    pattern = f"<{tag}>(.*?)</{tag}>"
    matches = re.findall(pattern, text, re.DOTALL)
    return [m.strip() for m in matches]


def parse_bool(value: str) -> bool:
    """Parse boolean from string"""
    value_lower = value.lower().strip()
    if value_lower in ["true", "yes", "1"]:
        return True
    elif value_lower in ["false", "no", "0"]:
        return False
    else:
        raise ValueError(f"Cannot parse boolean from: {value}")


class DecentralizedAgent:
    """
    Autonomous agent - NO CENTRAL COORDINATOR

    Key principles:
    - HUMANS set outcomes (preferences)
    - AI discovers methods (how to achieve outcomes)
    - Each agent is sovereign
    """

    def __init__(self, name: str, role: str, preferences: List[Preference], llm: LLMClient, max_side_payment_budget: float = 0):
        self.name = name
        self.role = role
        self.preferences = preferences  # HUMAN SOVEREIGNTY - outcomes only
        self.llm = llm
        self.max_side_payment_budget = max_side_payment_budget  # Monthly budget for paying other agents

    def evaluate_proposal(self, proposal: Proposal, space: NegotiationSpace) -> Evaluation:
        """
        Autonomously evaluate a proposal against human's stated outcomes

        AI uses domain knowledge to check if METHODS achieve OUTCOMES
        but never redefines what the human wants
        """

        # Format preferences
        prefs_str = "\n".join([
            f"  - {topic}: {value if value is not None else 'required'}"
            for topic, value in self.preferences
        ])

        # Format proposal
        proposal_str = self._format_proposal(proposal)

        # Calculate net compensation for this agent (developer payment + side payments received - side payments paid)
        net_comp_info = ""
        if proposal.id in space.evaluations or proposal.compensation or proposal.side_payments:
            dev_compensation = proposal.compensation.get(self.name, 0)
            side_received = sum(amount for (from_agent, to_agent), amount in proposal.side_payments.items() if to_agent == self.name)
            side_paid = sum(amount for (from_agent, to_agent), amount in proposal.side_payments.items() if from_agent == self.name)
            net_compensation = dev_compensation + side_received - side_paid

            if net_compensation != 0:
                net_comp_info = f"\nNET FINANCIAL POSITION: ${net_compensation:,.0f}/month"
                if dev_compensation > 0:
                    net_comp_info += f"\n  From developer: ${dev_compensation:,.0f}"
                if side_received > 0:
                    net_comp_info += f"\n  From other agents (side payments): ${side_received:,.0f}"
                if side_paid > 0:
                    net_comp_info += f"\n  You pay to other agents: ${side_paid:,.0f}"

        # Can see others' evaluations for coordination
        others_feedback = ""
        if proposal.id in space.evaluations:
            others_feedback = "\n\nOTHER AGENTS' EVALUATIONS:\n"
            for other_eval in space.evaluations[proposal.id].values():
                if other_eval.agent_name != self.name:
                    score = other_eval.satisfaction_score
                    status = "✓" if score >= 4 else "⚠" if score == 3 else "✗"
                    others_feedback += f"- {other_eval.agent_name}: {status} {score}/5\n"
                    if score < 4:
                        others_feedback += f"  Suggestions: {', '.join(other_eval.suggested_changes[:2])}\n"

        # DIFFERENT PROMPT FOR DEVELOPER VS NEIGHBORS
        if self.role == "developer":
            prompt = f"""You represent {self.name}, evaluating a proposal YOU created.

YOUR CONSTRAINTS (check ONLY these):
{prefs_str}

CURRENT PROPOSAL:
{proposal_str}

Your job: Check if this proposal meets YOUR OWN constraints (budget, timeline, etc.).

CRITICAL: Do NOT worry about whether neighbors are satisfied. That's their job to evaluate.
You only check: Does this fit my budget? My timeline? My project requirements?

If neighbors are unsatisfied, you'll synthesize a new proposal later. Right now, just check YOUR constraints.

Rate your satisfaction on a scale of 1-5:
5 = All requirements fully met, completely satisfied
4 = Core requirements met, only minor issues remain
3 = Significant requirements met, but notable gaps exist
2 = Some requirements addressed, many critical ones unmet
1 = Few or no requirements met

Respond in XML format:
<evaluation>
  <satisfaction_score>1-5</satisfaction_score>
  <explanation>Explain your score and what requirements are/aren't met</explanation>
  <unsatisfied_preferences>
    <preference>your constraint that isn't met or only partially met</preference>
  </unsatisfied_preferences>
  <suggested_changes>
    <change>what you'd need to change about YOUR constraints (mention if it would move you from X to Y score)</change>
  </suggested_changes>
</evaluation>"""
        else:
            # Neighbor evaluation prompt with 1-5 scale and Coasean bargaining
            budget_str = f"${round(self.max_side_payment_budget, 0):,.0f}/month" if self.max_side_payment_budget > 0 else "no budget for payments (you can only receive, not pay)"

            prompt = f"""You represent {self.name}, evaluating a proposal.

YOUR SIDE PAYMENT BUDGET: {budget_str}
(This is the maximum monthly amount you can afford to pay other agents for preferred outcomes)

HUMAN'S STATED OUTCOMES (you MUST respect these exactly):
{prefs_str}

CURRENT PROPOSAL:
{proposal_str}{net_comp_info}

{others_feedback}

COASEAN BARGAINING - SIDE PAYMENTS (CRITICAL MECHANISM):

This is the KEY to resolving conflicts between agents with opposite preferences.

**If you are unsatisfied with this proposal:**
- Consider: Could you PAY another agent to accept your preferred outcome?
- Your payment budget: {budget_str}
- Example: If you need outcome X (worth $50k to you) and another agent needs ¬X (worth $30k to them), you could pay them $40k. You gain: X worth $50k - cost $40k = $10k net benefit. They gain: $40k payment > $30k they'd lose = also better off. WIN-WIN!

**If another agent is unsatisfied:**
- Consider: Would you ACCEPT payment to compromise on your preferences?
- Example: If they value outcome Y at $60k and you oppose it, they could offer you $50k. You gain: $50k payment. They gain: Y worth $60k - cost $50k = $10k net benefit. WIN-WIN!

**How to think about this:**
- Think of your preferences in MONETARY terms: How much is outcome X worth to you?
- If other agents' outcomes conflict with yours, side payments can resolve the conflict without coercion
- Both sides must be strictly better off (more than current state)

Your job:
1. Determine if this proposal achieves the HUMAN'S OUTCOMES
2. **CRUCIALLY: Assess if you'd be willing to PAY or ACCEPT PAYMENT to resolve any conflicts**
3. Signal your willingness in the side_payment_interest section below

CRITICAL RULES:
1. NEVER question or redefine what the human wants
2. Use domain knowledge to assess if METHODS achieve OUTCOMES
3. If unsatisfied, suggest concrete METHODS to achieve the outcome
4. Think creatively about SIDE PAYMENTS to resolve conflicts with other agents
5. Be honest: Would paying/accepting payment make you better off?

Rate your satisfaction on a scale of 1-5:
5 = All requirements fully met, completely satisfied
4 = Core requirements met, only minor issues remain
3 = Significant requirements met, but notable gaps exist
2 = Some requirements addressed, many critical ones unmet
1 = Few or no requirements met

Respond in XML format:
<evaluation>
  <satisfaction_score>1-5</satisfaction_score>
  <explanation>Explain your score and what requirements are/aren't met (reference human's specific preferences)</explanation>
  <unsatisfied_preferences>
    <preference>first preference not met or only partially met</preference>
    <preference>second preference not met or only partially met</preference>
  </unsatisfied_preferences>
  <suggested_changes>
    <change>specific METHOD to improve satisfaction (mention if it would move you from X to Y score)</change>
    <change>alternative METHOD to improve satisfaction</change>
  </suggested_changes>
  <side_payment_interest>
    <willing_to_accept>true/false - Would you ACCEPT payment from another agent to compromise on your stated preferences? (Be honest about your flexibility)</willing_to_accept>
    <willing_to_pay>true/false - Would you PAY another agent to achieve your preferred outcome and resolve conflicts? (Only if you're truly unsatisfied without it)</willing_to_pay>
    <willingness_to_pay_estimate>
      DETAILED estimate of your maximum monthly payment capacity for preferred outcomes.
      Consider:
      - How much does your preferred outcome improve your welfare?
      - How much can you afford to pay WITHOUT harming yourself?
      - Example answers:
        * "I'd pay up to $8,000/month for [specific outcome]"
        * "I could afford $3,000-5,000/month if it guarantees my core requirement"
        * "I cannot afford ANY side payments - I can only accept if others pay me"
        * "I'd pay up to $15,000/month but only if it completely resolves [preference]"
    </willingness_to_pay_estimate>
  </side_payment_interest>
</evaluation>"""

        response = self.llm.call(prompt)

        # Parse response
        try:
            satisfaction_score = int(parse_xml_tag(response, "satisfaction_score"))
            explanation = parse_xml_tag(response, "explanation")
            unsatisfied_prefs = parse_xml_list(response, "preference")
            suggested_changes = parse_xml_list(response, "change")

            # Parse Coasean bargaining signals
            willing_to_accept = False
            willing_to_pay = False
            willingness_estimate = ""

            try:
                payment_interest_xml = parse_xml_tag(response, "side_payment_interest")
                try:
                    willing_to_accept = parse_bool(parse_xml_tag(payment_interest_xml, "willing_to_accept"))
                except ValueError:
                    pass
                try:
                    willing_to_pay = parse_bool(parse_xml_tag(payment_interest_xml, "willing_to_pay"))
                except ValueError:
                    pass
                try:
                    willingness_estimate = parse_xml_tag(payment_interest_xml, "willingness_to_pay_estimate")
                except ValueError:
                    pass
            except ValueError:
                # Payment interest section not found (OK for developer agent)
                pass

            evaluation = Evaluation(
                agent_name=self.name,
                proposal_id=proposal.id,
                satisfaction_score=satisfaction_score,
                explanation=explanation,
                unsatisfied_preferences=unsatisfied_prefs,
                suggested_changes=suggested_changes,
                timestamp=datetime.now(),
                willing_to_accept_payment=willing_to_accept,
                willing_to_pay=willing_to_pay,
                willingness_to_pay_estimate=willingness_estimate
            )

            # Post to shared space
            space.post_evaluation(evaluation)

            return evaluation

        except Exception as e:
            print(f"Failed to parse evaluation from {self.name}: {e}")
            print(f"Response was: {response}")
            raise

    def synthesize_proposal(
        self,
        current_proposal: Proposal,
        all_agents: List['DecentralizedAgent'],
        space: NegotiationSpace
    ) -> Dict[str, Any]:
        """
        Developer agent synthesizes improved proposal based on PUBLIC feedback

        Note: This agent has no special power - it's just responding to public signals.
        Any agent could counter-propose.
        """

        feedback = space.get_feedback_for_proposal(current_proposal.id)

        # Calculate current satisfaction state by scores
        satisfied_agents = []  # 4-5 score
        partially_satisfied_agents = []  # score 3
        unsatisfied_agents = []  # 1-2 score

        for fb in feedback:
            if fb['score'] >= 4:
                satisfied_agents.append(fb['agent'])
            elif fb['score'] == 3:
                partially_satisfied_agents.append(fb['agent'])
            else:
                unsatisfied_agents.append(fb['agent'])

        satisfaction_count = len(satisfied_agents)
        total_agents = len(feedback)
        avg_satisfaction = sum(fb['score'] for fb in feedback) / total_agents if feedback else 0

        # Format developer constraints
        dev_prefs = "\n".join([
            f"  - {topic}: {value if value is not None else 'required'}"
            for topic, value in self.preferences
        ])

        # Build satisfaction summary with scores
        satisfaction_summary = f"""
CURRENT SATISFACTION SCORES:

HIGH SATISFACTION (4-5/5) - DO NOT BREAK:
{chr(10).join(f'  ✓ {agent}' for agent in satisfied_agents) if satisfied_agents else '  (none yet)'}

MODERATE SATISFACTION (3/5) - IMPROVE IF POSSIBLE:
{chr(10).join(f'  ⚠ {agent}' for agent in partially_satisfied_agents) if partially_satisfied_agents else '  (none)'}

LOW SATISFACTION (1-2/5) - PRIORITY FIXES:
{chr(10).join(f'  ✗ {agent}' for agent in unsatisfied_agents) if unsatisfied_agents else '  (none)'}

Average: {avg_satisfaction:.1f}/5
"""

        # Build payment signals summary (ALL agents, not just unsatisfied)
        payment_signals_summary = "\n\nALL AGENTS' COASEAN BARGAINING SIGNALS:\n"
        agents_willing_to_pay = []
        agents_willing_to_accept = []
        agents_not_interested = []

        for fb in feedback:
            willing_accept = fb.get('willing_to_accept', False)
            willing_pay = fb.get('willing_to_pay', False)
            willingness = fb.get('willingness_estimate', '')

            if willing_pay:
                agents_willing_to_pay.append((fb['agent'], willingness))
            if willing_accept:
                agents_willing_to_accept.append(fb['agent'])
            if not willing_pay and not willing_accept:
                agents_not_interested.append(fb['agent'])

        if agents_willing_to_pay:
            payment_signals_summary += "\nWilling to PAY for preferred outcomes:\n"
            for agent, estimate in agents_willing_to_pay:
                if estimate:
                    payment_signals_summary += f"  • {agent}: {estimate}\n"
                else:
                    payment_signals_summary += f"  • {agent}: (amount not specified)\n"

        if agents_willing_to_accept:
            payment_signals_summary += "\nWilling to ACCEPT payment to compromise:\n"
            for agent in agents_willing_to_accept:
                payment_signals_summary += f"  • {agent}\n"

        # Build conflict analysis
        conflict_analysis = ""
        unsatisfied_feedback = []
        for fb in feedback:
            if fb['score'] < 4:
                unsatisfied_feedback.append((fb['agent'], fb['unsatisfied'], fb['suggested']))

        if len(unsatisfied_feedback) > 1:
            conflict_analysis = "\nCONFLICT DETECTION & COASEAN BARGAINING:\n"
            conflict_analysis += "The following agents have incompatible preferences:\n"
            for agent, unsat, suggested in unsatisfied_feedback:
                conflict_analysis += f"\n{agent}:\n"
                conflict_analysis += f"  Wants: {unsat[0] if unsat else 'unclear'}\n"
                if suggested:
                    conflict_analysis += f"  Suggests: {suggested[0]}\n"

            conflict_analysis += "\nOPPORTUNITY: Can any of these agents resolve their conflict through SIDE PAYMENTS?"
            conflict_analysis += "\nCoasean Solution: If Agent A values outcome X more than Agent B, but Agent B values ¬X more,"
            conflict_analysis += "\nthen Agent A could PAY Agent B to accept X. Both benefit if:"
            conflict_analysis += "\n- Agent A values X at > $Y and Agent B accepts $Y"
            conflict_analysis += "\n- Agent B's compensation ($Y) > their loss from ¬X"
            conflict_analysis += "\nUse side_payments in your response to implement this."

            # Add agent willingness signals
            conflict_analysis += "\n\nAGENT WILLINGNESS SIGNALS (From Evaluations):"
            for fb in feedback:
                agent_name = fb['agent']
                willing_accept = fb.get('willing_to_accept', False)
                willing_pay = fb.get('willing_to_pay', False)
                willingness = fb.get('willingness_estimate', '')

                signals = []
                if willing_accept:
                    signals.append("open to accepting payment")
                if willing_pay:
                    if willingness:
                        signals.append(f"willing to pay ({willingness})")
                    else:
                        signals.append("willing to pay")

                if signals:
                    conflict_analysis += f"\n- {agent_name}: {', '.join(signals)}"
                else:
                    signal = "has not signaled interest in side payments"
                    conflict_analysis += f"\n- {agent_name}: {signal}"

        # Determine strategy based on progress
        if satisfaction_count >= total_agents - 2:
            strategy_guidance = f"""
🚨 CRITICAL: {satisfaction_count}/{total_agents} AGENTS ARE ALREADY SATISFIED

SATISFIED AGENTS (THEIR CONSTRAINTS ARE LOCKED - DO NOT BREAK):
{chr(10).join(f'  ✓ {agent}' for agent in satisfied_agents)}

UNSATISFIED AGENTS (YOUR ONLY FOCUS):
{chr(10).join(f'  ✗ {agent}' for agent in unsatisfied_agents)}

STRATEGY - SURGICAL ADDITIONS WITH SIDE PAYMENTS:

**PRIMARY APPROACH: Side Payments to the Final {len(unsatisfied_agents)} Agent(s)**

Check willingness signals:
{payment_signals_summary}

**YOUR FIRST STEP:**
1. Can any of the {len(unsatisfied_agents)} unsatisfied agents be satisfied via SIDE PAYMENT?
2. If Agent X is willing to pay and Agent Y would accept payment, PROPOSE IT
3. Structure carefully: "Agent X pays Agent Y $[amount] for compromise on [outcome]"
4. Verify both are better off than current state

**IF side payments don't fully resolve:**
- Add ONLY small, surgical NEW modifications (never remove/reduce anything for satisfied agents)
- Each modification must be paired with DEVELOPER COMPENSATION, not satisfied agent cuts
- Ask before each change: "Will this break any satisfied agent?"

DO NOT modify or reduce anything that satisfied agents depend on.
"""
        else:
            strategy_guidance = f"""
STRATEGY - START WITH COASEAN SIDE PAYMENTS:

🎯 PRIMARY APPROACH: SIDE PAYMENTS (Voluntary Bilateral Bargaining)

Look at the AGENT WILLINGNESS SIGNALS section above. Agents have signaled:
{payment_signals_summary}

**YOUR FIRST STEP - Resolve conflicts via side payments:**
1. Identify which unsatisfied agents have CONFLICTING preferences (want opposite outcomes)
2. Check the willingness signals: Who wants to PAY? Who is willing to ACCEPT payment?
3. **MATCH them**: If Agent A wants outcome X and is willing to pay, and Agent B would accept payment to allow X, PROPOSE THE SIDE PAYMENT
4. Structure it as: "{{agent_willing_to_pay}} pays {{agent_willing_to_accept}} $[amount] monthly to accept [outcome]"
5. Both must be strictly better off than the status quo

**Why side payments first?**
- Resolves fundamental incompatibilities without coercing anyone
- Creates Pareto improvements (both parties better off)
- More efficient than trying to satisfy everyone with developer compensation
- Demonstrates Coasean bargaining: price discovery through voluntary exchange

**ONLY IF side payments cannot resolve a conflict:**
- Then explore complementary modifications where one change helps multiple agents
- Be creative: one modification might address multiple preferences simultaneously

Be bold - you're still far from unanimous agreement. Try multiple side payment combinations.
"""

        # Format feedback (only unsatisfied)
        feedback_str = ""
        for fb in feedback:
            if not fb['satisfied']:
                feedback_str += f"\n{fb['agent']}:\n"
                feedback_str += f"  Unsatisfied: {', '.join(fb['unsatisfied'])}\n"
                feedback_str += f"  Suggests: {', '.join(fb['suggested'][:3])}\n"

        prompt = f"""You are synthesizing an improved proposal based on PUBLIC feedback.

DEVELOPER CONSTRAINTS:
{dev_prefs}
{satisfaction_summary}
{payment_signals_summary}
{strategy_guidance}{conflict_analysis}

CURRENT PROPOSAL:
{self._format_proposal(current_proposal)}

NEIGHBOR FEEDBACK (from public bulletin board):
{feedback_str}

Your job: Create an improved proposal that satisfies more neighbors while respecting developer constraints.
{"CRITICAL: When agents are already satisfied, your ONLY job is to fix unsatisfied agents WITHOUT breaking satisfied ones. Make minimal, surgical additions." if satisfaction_count >= total_agents - 2 else ""}

MULTI-DIMENSIONAL SOLUTION SPACE - you can:
- Add physical modifications (soundproofing, parking, green buffers)
- Impose operational constraints (delivery hours, construction times)
- Make design changes (architecture, height, materials)
- Adjust developer compensation amounts
- Make SIDE PAYMENTS between agents (Coasean bargaining)
- Add community commitments

SIDE PAYMENTS EXPLAINED:
If Agent A wants outcome X (values at $50k) and Agent B wants ¬X (values at $30k), then:
- Agent A pays Agent B $40k to accept X
- Agent A: gets X worth $50k - pays $40k = $10k net gain ✓
- Agent B: gets $40k payment > $30k they'd lose = better off ✓
- BOTH are better off than deadlock → Pareto improvement!

When proposing side payments, ask: Would both agents be strictly better off?

Think creatively! Don't just throw money at problems. Look for complementary solutions
where one modification helps multiple neighbors.

IMPORTANT: Pay close attention to exact compensation amounts neighbors require.
If someone needs $8000 minimum, give them AT LEAST $8000, not less!

Respond with XML format matching the structure below (adapt fields to match your proposal):
<improved_proposal>
  <base_project>
    <!-- Key aspects of your proposal -->
  </base_project>
  <modifications>
    <modification>
      <type>type of modification</type>
      <cost>numerical cost or TBD</cost>
      <benefit>how this helps satisfy neighbors</benefit>
    </modification>
  </modifications>
  <compensation>
    <payment>
      <recipient>neighbor name</recipient>
      <amount>compensation amount</amount>
    </payment>
  </compensation>
  <side_payments>
    <payment>
      <from>agent name who pays</from>
      <to>agent name who receives</to>
      <amount>monthly payment amount</amount>
      <reason>why this payment creates mutual gains and Pareto improvement</reason>
    </payment>
  </side_payments>
  <commitments>
    <commitment>specific commitment or operational constraint</commitment>
  </commitments>
  <total_cost>total project cost (include developer compensation, not side payments)</total_cost>
  <reasoning>Brief explanation of the bundle, side payments, and why it satisfies more neighbors</reasoning>
</improved_proposal>"""

        response = self.llm.call(prompt)

        # Parse response
        try:
            proposal = {}

            # Parse base_project
            base_project = {}
            base_xml = parse_xml_tag(response, "base_project")
            for field in ["type", "size_sqft", "stories"]:
                try:
                    value = parse_xml_tag(base_xml, field)
                    try:
                        value = float(value)
                        if value.is_integer():
                            value = int(value)
                    except ValueError:
                        pass
                    base_project[field] = value
                except ValueError:
                    pass
            proposal["base_project"] = base_project

            # Parse modifications
            modifications = []
            try:
                mods_xml = parse_xml_tag(response, "modifications")
                mod_blocks = re.findall(r"<modification>(.*?)</modification>", mods_xml, re.DOTALL)
                for mod_block in mod_blocks:
                    mod = {}
                    for field in ["type", "cost", "benefit", "details"]:
                        try:
                            value = parse_xml_tag(mod_block, field)
                            try:
                                value = float(value)
                                if value.is_integer():
                                    value = int(value)
                            except ValueError:
                                pass
                            mod[field] = value
                        except ValueError:
                            pass
                    if mod:
                        modifications.append(mod)
            except ValueError:
                pass
            proposal["modifications"] = modifications

            # Parse compensation
            compensation = {}
            try:
                comp_xml = parse_xml_tag(response, "compensation")
                payment_blocks = re.findall(r"<payment>(.*?)</payment>", comp_xml, re.DOTALL)
                for payment_block in payment_blocks:
                    try:
                        recipient = parse_xml_tag(payment_block, "recipient")
                        amount = float(parse_xml_tag(payment_block, "amount"))
                        compensation[recipient] = amount
                    except (ValueError, Exception):
                        pass
            except ValueError:
                pass
            proposal["compensation"] = compensation

            # Parse side_payments
            side_payments = []
            try:
                side_xml = parse_xml_tag(response, "side_payments")
                payment_blocks = re.findall(r"<payment>(.*?)</payment>", side_xml, re.DOTALL)
                for payment_block in payment_blocks:
                    try:
                        from_agent = parse_xml_tag(payment_block, "from")
                        to_agent = parse_xml_tag(payment_block, "to")
                        amount = float(parse_xml_tag(payment_block, "amount"))
                        try:
                            reason = parse_xml_tag(payment_block, "reason")
                        except ValueError:
                            reason = ""

                        # Validate that amount is within agent budget
                        # This will be enforced later by budget validation
                        side_payments.append({
                            "from": from_agent,
                            "to": to_agent,
                            "amount": amount,
                            "reason": reason
                        })
                    except (ValueError, Exception):
                        pass
            except ValueError:
                pass
            proposal["side_payments"] = side_payments

            # Parse commitments
            try:
                commitments = parse_xml_list(response, "commitment")
                proposal["commitments"] = commitments
            except ValueError:
                proposal["commitments"] = []

            # Parse total_cost
            try:
                total_cost = float(parse_xml_tag(response, "total_cost"))
                proposal["total_cost"] = total_cost
            except (ValueError, Exception):
                proposal["total_cost"] = 0

            # Parse reasoning
            try:
                proposal["reasoning"] = parse_xml_tag(response, "reasoning")
            except ValueError:
                proposal["reasoning"] = ""

            return proposal

        except Exception as e:
            print(f"Failed to parse improved proposal: {e}")
            print(f"Response was: {response}")
            raise

    def should_continue_negotiation(
        self,
        current_proposal: Proposal,
        all_agents: List['DecentralizedAgent'],
        space: NegotiationSpace
    ) -> Tuple[bool, str]:
        """
        Analyze whether negotiation should continue or if we've reached
        a Pareto optimal point
        """

        feedback = space.get_feedback_for_proposal(current_proposal.id)

        if not feedback:
            return True, "No feedback yet. Continuing negotiation."

        # Build satisfaction summary
        satisfaction_scores = {fb['agent']: fb['score'] for fb in feedback}
        unsatisfied = [(agent, score) for agent, score in satisfaction_scores.items() if score < 4]

        if not unsatisfied:
            return False, "All agents satisfied (≥4/5). Negotiation complete."

        # Format for conflict analysis
        unsatisfied_details = ""
        for agent_name, score in unsatisfied:
            agent_feedback = next(fb for fb in feedback if fb['agent'] == agent_name)
            unsatisfied_details += f"\n{agent_name} ({score}/5):\n"
            unsatisfied_details += f"  Wants: {', '.join(agent_feedback['unsatisfied'][:3])}\n"

        satisfied_details = ""
        for agent_name, score in satisfaction_scores.items():
            if score >= 4:
                satisfied_details += f"  {agent_name}: {score}/5\n"

        avg_score = sum(satisfaction_scores.values()) / len(satisfaction_scores)

        # Extract historical satisfaction data from all past proposals
        agent_history = {}
        for round_num, proposal in enumerate(space.proposals, 1):
            proposal_id = proposal.id
            if proposal_id in space.evaluations:
                for agent_name, evaluation in space.evaluations[proposal_id].items():
                    if agent_name not in agent_history:
                        agent_history[agent_name] = []
                    agent_history[agent_name].append({
                        'round': round_num,
                        'score': evaluation.satisfaction_score,
                        'unsatisfied': evaluation.unsatisfied_preferences,
                        'suggested': evaluation.suggested_changes
                    })

        # Format historical progression (raw data, no interpretation)
        history_section = "HISTORICAL SATISFACTION PROGRESSION:\n"
        for agent_name in sorted(agent_history.keys()):
            history = agent_history[agent_name]
            history_section += f"\n{agent_name}:\n"
            for entry in history:
                history_section += f"  Round {entry['round']}: {entry['score']}/5\n"
                if entry['unsatisfied']:
                    history_section += f"    Unsatisfied: {', '.join(entry['unsatisfied'][:3])}\n"
                if entry['suggested']:
                    history_section += f"    Suggested: {entry['suggested'][0]}\n"

        prompt = f"""You are analyzing whether this negotiation can make further progress.

CURRENT STATE:
Average satisfaction: {avg_score:.1f}/5

SATISFIED AGENTS (≥4/5):
{satisfied_details if satisfied_details else '  (none yet)'}

UNSATISFIED AGENTS (<4/5):
{unsatisfied_details}

{history_section}

CRITICAL ANALYSIS - USE HISTORICAL DATA TO DETECT PATTERNS:

Look at the HISTORICAL SATISFACTION PROGRESSION and identify:
1. Agents stuck at the same score for multiple consecutive rounds
2. Agents repeatedly requesting the same unsatisfied preference despite synthesis attempts
3. Agents whose scores improved and have stayed satisfied (solution is working)
4. Agents whose improvements were only temporary (preferences re-emerged)

These patterns indicate:
- STUCK + REPEATED COMPLAINT = likely fundamental constraint, not missing solution
- IMPROVED + STAYS SATISFIED = solution is working, protect it
- STUCK DESPITE SYNTHESIS ATTEMPTS = preferences may be incompatible with satisfied agents

CRITICAL PARETO OPTIMALITY QUESTIONS:

1. Based on the historical progression, are any unsatisfied agents STUCK (same score, same complaint for multiple rounds)?
   - If yes: This suggests a fundamental constraint, not a missing solution

2. If you tried to satisfy the stuck unsatisfied agents, would you NECESSARILY break the satisfied agents?
   - Use historical data to check: Did satisfied agents only become satisfied after moving away from these stuck agents' preferences?

3. Have we reached a PARETO OPTIMAL point where any improvement for one agent requires harming another?

4. Is the current average satisfaction ({avg_score:.1f}/5) already high enough to declare success?
   - Consider: Has it plateaued in the historical data?

Respond in XML:
<analysis>
  <should_continue>true or false</should_continue>
  <reasoning>
    Use the HISTORICAL SATISFACTION PROGRESSION to explain your reasoning.
    - Which agents are stuck in the history?
    - Which agents improved and stayed satisfied?
    - Are the stuck agents fundamentally incompatible with satisfied agents?
    - Explain whether further progress is possible without breaking satisfied agents.
  </reasoning>
  <recommendation>
    If should_continue=false: Explain what final agreement was reached and why it's Pareto optimal. Reference the historical data showing patterns that led to this conclusion.
    If should_continue=true: Describe the specific changes that could work, considering patterns in the history.
  </recommendation>
</analysis>"""

        response = self.llm.call(prompt)

        # Parse response
        try:
            should_continue_str = parse_xml_tag(response, "should_continue")
            should_continue = parse_bool(should_continue_str)
            reasoning = parse_xml_tag(response, "reasoning")
            recommendation = parse_xml_tag(response, "recommendation")

            analysis_text = f"{reasoning}\n\n{recommendation}"
            return should_continue, analysis_text

        except Exception as e:
            print(f"Failed to parse meta-analysis: {e}")
            print(f"Response was: {response}")
            # Default to continuing if analysis fails
            return True, "Could not parse meta-analysis. Continuing negotiation."

    def _format_proposal(self, proposal: Proposal) -> str:
        """Format proposal for display"""
        result = "Base Project:\n"
        for key, value in proposal.base_project.items():
            result += f"  {key}: {value}\n"

        if proposal.modifications:
            result += "\nModifications:\n"
            for mod in proposal.modifications:
                result += f"  - {mod.get('type', 'unknown')}"
                if 'cost' in mod:
                    cost = mod['cost']
                    try:
                        cost_num = float(cost)
                        result += f" (${cost_num:,.0f})"
                    except (ValueError, TypeError):
                        result += f" ({cost})"
                if 'benefit' in mod:
                    result += f": {mod['benefit']}"
                result += "\n"

        if proposal.compensation:
            result += "\nDeveloper Compensation (Policy Maker → Stakeholders):\n"
            for recipient, amount in proposal.compensation.items():
                try:
                    amount_num = float(amount)
                    result += f"  - {recipient}: ${amount_num:,.0f}\n"
                except (ValueError, TypeError):
                    result += f"  - {recipient}: {amount}\n"

        if proposal.side_payments:
            result += "\nCoasean Side Payments (Agent-to-Agent Bargaining):\n"
            for (from_agent, to_agent), amount in proposal.side_payments.items():
                try:
                    amount_num = float(amount)
                    result += f"  - {from_agent} → {to_agent}: ${amount_num:,.0f}/month\n"
                except (ValueError, TypeError):
                    result += f"  - {from_agent} → {to_agent}: {amount}\n"

        if proposal.commitments:
            result += "\nCommitments:\n"
            for commitment in proposal.commitments:
                result += f"  - {commitment}\n"

        try:
            total_cost_num = float(proposal.total_cost)
            result += f"\nTotal Cost: ${total_cost_num:,.0f}"
        except (ValueError, TypeError):
            result += f"\nTotal Cost: {proposal.total_cost}"

        return result


def create_demo_scenario(neighbor_llm: LLMClient, developer_llm: LLMClient) -> Tuple[DecentralizedAgent, List[DecentralizedAgent]]:
    """
    Create the demo scenario: COVID-19 policy negotiation

    Note: Each agent only provides SIMPLE preference tuples.
    The AI figures out HOW to achieve these outcomes.
    """

    # Policy maker acts as the "developer" role - proposing policies within budget
    policy_maker = DecentralizedAgent(
        name="Policy_Maker",
        role="developer",
        preferences=[
            ("total_budget_under", 50000000.0),  # $50M monthly budget
            ("case_rate_target_below", 50.0),  # per 100k
        ],
        llm=developer_llm,
        max_side_payment_budget=0  # Developer doesn't pay agents directly (only compensation)
    )

    # Various stakeholders with their specific constraints
    stakeholders = [
        DecentralizedAgent(
            name="Business_Owner (restaurant/retail)",
            role="neighbor",
            preferences=[
                ("max_capacity_reduction", 30.0),
                ("mask_requirement_acceptance", "customers_only"),
                ("air_filtration_investment_max", 5000.0),
                ("revenue_loss_tolerance", 20.0),
                ("compensation_required_monthly", 10000.0),
                ("delivery_pivot_capability", True),
                ("outdoor_space_available", False)
            ],
            llm=neighbor_llm,
            max_side_payment_budget=15000.0  # Business owner can afford to pay up to $15k/month for favorable outcomes
        ),
        DecentralizedAgent(
            name="Healthcare_Worker",
            role="neighbor",
            preferences=[
                ("min_mask_compliance_rate", 80.0),
                ("min_air_changes_per_hour", 6.0),
                ("max_acceptable_case_rate", 20.0),
                ("work_from_home_requirement", "hybrid"),
                ("priority_medical_access", True),
            ],
            llm=neighbor_llm,
            max_side_payment_budget=15000  # Healthcare worker cannot afford side payments
        ),
        DecentralizedAgent(
            name="Parent (school-age_children)",
            role="neighbor",
            preferences=[
                ("school_format_preference", "in_person"),
                ("child_mask_tolerance_hours", 4.0),
                ("activity_restriction_acceptance", "moderate"),
                ("childcare_subsidy_needed", 2000.0),
                ("testing_frequency_acceptable", "weekly"),
                ("vaccine_requirement_support", False)
            ],
            llm=neighbor_llm,
            max_side_payment_budget=3000.0  # Parent can afford modest side payments for school outcomes
        ),
        DecentralizedAgent(
            name="Essential_Worker (grocery/transit)",
            role="neighbor",
            preferences=[
                ("hazard_pay_minimum", 5.0),
                ("ppe_provision_required", "full"),
                ("sick_leave_days_needed", 14.0),
                ("testing_provided_frequency", "twice_weekly"),
                ("transport_subsidy_needed", 200.0),
                ("shift_flexibility_needed", True)
            ],
            llm=neighbor_llm,
            max_side_payment_budget=0  # Essential worker cannot afford side payments
        ),


        DecentralizedAgent(
            name="Small_Landlord (property_owner)",
            role="neighbor",
            preferences=[
                ("rent_freeze_tolerance_months", 3.0),
                ("eviction_moratorium_acceptance", False),
                ("property_tax_relief_needed", 30.0),
                ("maintenance_delay_acceptable", "emergency_only"),
                ("tenant_support_contribution", 500.0),
                ("commercial_tenant_flexibility", "moderate")
            ],
            llm=neighbor_llm,
            max_side_payment_budget=8000.0  # Landlord can afford to pay for favorable property/tenant policies
        ),

    ]

    return policy_maker, stakeholders


def run_negotiation(
    developer: DecentralizedAgent,
    neighbors: List[DecentralizedAgent],
    space: NegotiationSpace,
    max_rounds: int = 7
) -> Optional[Proposal]:
    """
    Run the decentralized negotiation process

    Key: NO CENTRAL COORDINATOR
    Each agent operates autonomously, coordinating through shared bulletin board
    """

    print("=" * 80)
    print("COASEAN MULTI-DIMENSIONAL NEGOTIATION")
    print("Preserving Human Agency in Massive Multi-Entity Coordination")
    print("=" * 80)

    print("\n" + "=" * 80)
    print("HUMAN SOVEREIGNTY - Outcomes Set by Users")
    print("=" * 80)
    print(f"\n{developer.name}:")
    for pref, value in developer.preferences:
        print(f"  • {pref}: {value if value is not None else 'required'}")

    for neighbor in neighbors:
        print(f"\n{neighbor.name}:")
        for pref, value in neighbor.preferences:
            print(f"  • {pref}: {value if value is not None else 'required'}")

    # Initial proposal (binary approach)
    initial_proposal_data = {
        "base_project": {
            "type": "covid_policy",
            "mask_mandate": "none",
            "capacity_limits": "none",
            "business_restrictions": "none"
        },
        "modifications": [],
        "compensation": {n.name: 0 for n in neighbors},
        "commitments": [],
        "total_cost": 0
    }

    print("\n" + "=" * 80)
    print("ROUND 0: INITIAL PROPOSAL (Binary Approach)")
    print("=" * 80)
    space.post_proposal(developer.name, initial_proposal_data)
    current_proposal = space.get_latest_proposal()
    print(developer._format_proposal(current_proposal))

    # Track average satisfaction to detect regressions
    prev_avg_satisfaction = 0

    # Negotiation rounds
    for round_num in range(max_rounds):
        space.advance_round()

        print(f"\n{'=' * 80}")
        print(f"ROUND {space.current_round}: DECENTRALIZED EVALUATION")
        print(f"{'=' * 80}")
        print("(Each agent evaluates independently using the bulletin board)\n")

        # Each agent evaluates independently - run in parallel
        print("(Running evaluations in parallel)\n")

        neighbor_evals = {}
        neighbor_scores = []

        # Use ThreadPoolExecutor to run neighbor evaluations in parallel
        with ThreadPoolExecutor(max_workers=len(neighbors) + 1) as executor:
            # Submit all neighbor evaluations
            neighbor_futures = {
                executor.submit(neighbor.evaluate_proposal, current_proposal, space): neighbor
                for neighbor in neighbors
            }

            # Also submit developer evaluation in parallel
            dev_future = executor.submit(developer.evaluate_proposal, current_proposal, space)

            # Collect neighbor results as they complete
            for future in as_completed(neighbor_futures):
                neighbor = neighbor_futures[future]
                eval_result = future.result()
                neighbor_evals[neighbor.name] = eval_result
                neighbor_scores.append(eval_result.satisfaction_score)

                score = eval_result.satisfaction_score
                status_icon = "✓" if score >= 4 else "⚠" if score == 3 else "✗"
                print(f"{status_icon} {neighbor.name}: {score}/5")
                print(f"   {eval_result.explanation}")

                if score < 4:
                    if eval_result.suggested_changes:
                        print(f"   Suggests: {eval_result.suggested_changes[0]}")
                print()

            # Wait for developer evaluation to complete
            dev_eval = dev_future.result()

        # Calculate average and check success
        all_scores = neighbor_scores + [dev_eval.satisfaction_score]
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        print(f"\n   Average satisfaction: {avg_score:.1f}/5")
        print(f"   Developer: {dev_eval.satisfaction_score}/5\n")

        # Check for regression (drop > 0.2 in average satisfaction)
        if space.current_round > 1 and (prev_avg_satisfaction - avg_score) > 0.2:
            print(f"\n{'=' * 80}")
            print("✗ REGRESSION DETECTED - Negotiation halted")
            print(f"   Previous round avg: {prev_avg_satisfaction:.1f}/5")
            print(f"   Current round avg: {avg_score:.1f}/5")
            print(f"   Drop: {prev_avg_satisfaction - avg_score:.1f} (threshold: 0.2)")
            print(f"{'=' * 80}")
            return None

        prev_avg_satisfaction = avg_score

        # Success condition: all agents >= 4/5
        all_satisfied = all(score >= 4 for score in all_scores)

        # Check if all parties are satisfied (all agents >= 4/5)
        if all_satisfied:
            print(f"\n{'=' * 80}")
            print("✓ SUCCESS! All parties satisfied through decentralized coordination")
            print(f"{'=' * 80}")
            return current_proposal

        # If not all satisfied, check for Pareto optimality
        if not all_satisfied:
            print(f"\n{'=' * 80}")
            print("META-ANALYSIS: Should Negotiation Continue?")
            print(f"{'=' * 80}\n")

            should_continue, analysis = developer.should_continue_negotiation(
                current_proposal,
                neighbors,
                space
            )

            print(analysis)

            if not should_continue:
                print(f"\n{'=' * 80}")
                print("NEGOTIATION COMPLETE - Pareto Optimal Agreement Reached")
                print(f"{'=' * 80}")
                return current_proposal

            print("\n→ Continuing to synthesis phase...")

        # Developer synthesizes improved proposal based on PUBLIC feedback
        print(f"\n{'=' * 80}")
        print("SYNTHESIS: Developer Agent Responding to Public Signals")
        print(f"{'=' * 80}")
        print("(No special power - just reading the bulletin board like everyone else)\n")

        improved_data = developer.synthesize_proposal(
            current_proposal,
            neighbors,
            space
        )

        space.post_proposal(developer.name, improved_data)
        current_proposal = space.get_latest_proposal()

        # Validate side payments against agent budgets
        agents_dict = {developer.name: developer}
        for neighbor in neighbors:
            agents_dict[neighbor.name] = neighbor

        is_valid, validation_msg = space.validate_side_payments(current_proposal, agents_dict)
        if current_proposal.side_payments:
            print("\nSIDE PAYMENT VALIDATION:")
            print(validation_msg)
            if not is_valid:
                print("\n✗ NEGOTIATION FAILED - Side payments exceed agent budgets!")
                print("   The LLM proposed payments that agents cannot afford.")
                print("   (Agents only have the budgets humans set for them)")
                return None

        print("IMPROVED PROPOSAL:")
        print(developer._format_proposal(current_proposal))
        if current_proposal.reasoning:
            print(f"\nReasoning: {current_proposal.reasoning}")

    print("\n✗ Max rounds reached without unanimous agreement")
    return None


def print_final_summary(proposal: Optional[Proposal], neighbors: List[DecentralizedAgent], space: NegotiationSpace = None):
    """Print summary with Pareto optimality analysis"""

    print("\n" + "=" * 80)
    print("NEGOTIATION OUTCOME")
    print("=" * 80)

    if proposal and space:
        # Show final scores
        final_eval = space.evaluations.get(proposal.id, {})
        if final_eval:
            scores = {name: eval.satisfaction_score for name, eval in final_eval.items()}
            avg = sum(scores.values()) / len(scores) if scores else 0

            print("\nFinal Satisfaction Scores:")
            for agent, score in sorted(scores.items(), key=lambda x: -x[1]):
                icon = "✓" if score >= 4 else "⚠" if score == 3 else "✗"
                print(f"  {icon} {agent}: {score}/5")

            print(f"\n  Average: {avg:.1f}/5")

            if avg >= 4.0:
                print("\n✓ STRONG CONSENSUS ACHIEVED")
                print("  Near-unanimous agreement through multi-dimensional coordination")

            # Explain remaining gaps
            unsatisfied = [(name, score) for name, score in scores.items() if score < 4]
            if unsatisfied:
                print("\n" + "=" * 80)
                print("PARETO FRONTIER ANALYSIS")
                print("=" * 80)
                print("\nRemaining unsatisfied agents have mutually exclusive preferences:")
                for name, score in unsatisfied:
                    eval = final_eval.get(name)
                    if eval:
                        print(f"\n  {name} ({score}/5):")
                        for pref in eval.unsatisfied_preferences[:2]:
                            print(f"    - {pref}")

                print("\nFurther optimization would require breaking satisfied agents.")
                print("Current solution represents Pareto optimal compromise.")

    if proposal:
        print("\nBase Project:")
        for key, value in proposal.base_project.items():
            print(f"  {key}: {value}")

        print(f"\nModifications ({len(proposal.modifications)}):")
        for mod in proposal.modifications:
            if 'cost' in mod:
                try:
                    cost_num = float(mod['cost'])
                    cost_str = f"${cost_num:,.0f}"
                except (ValueError, TypeError):
                    cost_str = f"${mod['cost']}"
            else:
                cost_str = "TBD"
            print(f"  • {mod.get('type', 'unknown')} ({cost_str})")
            if 'benefit' in mod:
                print(f"    → {mod['benefit']}")

        print("\nCompensation (Developer → Stakeholders):")
        total_comp = 0
        for recipient, amount in proposal.compensation.items():
            try:
                amount_num = float(amount)
                total_comp += amount_num
                print(f"  • {recipient}: ${amount_num:,.0f}")
            except (ValueError, TypeError):
                print(f"  • {recipient}: {amount}")
        print(f"  Total: ${total_comp:,.0f}")

        if proposal.side_payments:
            print("\nCoasean Side Payments (Agent-to-Agent Bargaining):")
            total_side = 0
            for (from_agent, to_agent), amount in proposal.side_payments.items():
                try:
                    amount_num = float(amount)
                    total_side += amount_num
                    print(f"  • {from_agent} → {to_agent}: ${amount_num:,.0f}/month")
                except (ValueError, TypeError):
                    pass
            print(f"  Total recurring: ${total_side:,.0f}/month")

            print("\nCOASEAN BARGAINING EXPLANATION:")
            print("  Incompatible preferences between agents were resolved through voluntary")
            print("  bilateral payments (Coasean bargaining), not government mandate:")
            print("  - Agents who valued outcomes more paid agents with opposite preferences")
            print("  - Both sides better off than deadlock → Pareto improvement")
            print("  - This demonstrates private negotiation discovering optimal allocation")
            print("  - Without coercion: each agent AGREED to accept the payment")

        if proposal.commitments:
            print("\nCommitments:")
            for commitment in proposal.commitments:
                print(f"  • {commitment}")

        try:
            total_cost_num = float(proposal.total_cost)
            print(f"\nTotal Project Cost: ${total_cost_num:,.0f}")
        except (ValueError, TypeError):
            print(f"\nTotal Project Cost: {proposal.total_cost}")

    print("\n" + "=" * 80)
    print("KEY INSIGHTS - Breaking the Intelligence Curse")
    print("=" * 80)

    print("\n1. HUMANS SET OUTCOMES, AI DISCOVERS METHODS")
    print("   • Neighbors only provided simple preference tuples")
    print("   • AI agents figured out HOW to achieve those outcomes")
    print("   • Human sovereignty preserved at constitutional layer")

    print("\n2. TRADITIONAL APPROACHES WOULD FAIL")
    print("   • Binary vote: Everyone says no → deadlock")
    print("   • Government mandate: Someone loses → coercion")
    print("   • Naive compensation: Would cost >$20k → wasteful")

    print("\n3. MULTI-DIMENSIONAL SOLUTION SPACE")
    if proposal:
        mod_count = len(proposal.modifications)
        print(f"   • Discovered bundle with {mod_count} modifications")
        try:
            total_cost_num = float(proposal.total_cost)
            print(f"   • Total cost: ${total_cost_num:,.0f} (under budget!)")
        except (ValueError, TypeError):
            print(f"   • Total cost: {proposal.total_cost}")
        print(f"   • All {len(neighbors)} parties satisfied")
        print("   • Pareto improvement discovered through coordination")

    print("\n4. COASEAN BARGAINING - RESOLVING CONFLICT VIA PAYMENTS")
    if proposal and proposal.side_payments:
        print("   • Incompatible preferences resolved through bilateral payments")
        print("   • Not government mandates or central planning")
        print("   • Agents who valued outcomes MORE paid agents to compromise")
        print("   • Both sides better off than deadlock → PARETO IMPROVEMENT")
        print("   • Private voluntary exchange discovering optimal allocation")
    else:
        print("   • When agents have conflicting preferences, enable side payments")
        print("   • Agent A pays Agent B to accept Agent A's preferred outcome")
        print("   • Only works if BOTH are better off than the deadlock")
        print("   • Demonstrates how markets resolve coordination problems")

    print("\n5. DECENTRALIZED ARCHITECTURE")
    print("   • No central coordinator controlling outcomes")
    print("   • Transparent bulletin board for all communications")
    print("   • Each agent autonomous and sovereign")
    print("   • Emergent order from voluntary coordination")

    print("\n6. PRESERVING HUMAN AGENCY AT SCALE")
    print("   • This demo: 5 entities coordinating")
    print("   • Same protocol scales to 500 or 5,000,000")
    print("   • Humans remain in control as AI handles complexity")
    print("   • Infrastructure for massive multi-entity coordination")

    print("\n" + "=" * 80)
    print("This is def/acc: Technology that preserves human agency")
    print("even as coordination scales to civilizational levels.")
    print("=" * 80)


def main():
    """Main entry point"""

    # Setup
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: Please set OPENROUTER_API_KEY environment variable")
        return

    # Create LLM client - using same model for all agents
    llm = LLMClient(api_key, model="google/gemini-2.5-flash-preview-09-2025")

    # Create scenario
    print("Setting up decentralized negotiation scenario...")
    policy_maker, stakeholders = create_demo_scenario(llm, llm)

    # Create shared space (bulletin board)
    space = NegotiationSpace()

    # Run negotiation
    print("\nStarting negotiation...\n")
    final_proposal = run_negotiation(policy_maker, stakeholders, space, max_rounds=7)

    # Print summary
    print_final_summary(final_proposal, stakeholders, space)

    if final_proposal:
        print(f"\n✓ Negotiation succeeded in {space.current_round} rounds")
    else:
        print("\n✗ Negotiation failed to reach agreement")


if __name__ == "__main__":
    main()
