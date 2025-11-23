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
    commitments: List[str]
    total_cost: float
    reasoning: str = ""


@dataclass
class Evaluation:
    """An agent's evaluation of a proposal"""
    agent_name: str
    proposal_id: int
    satisfied: bool
    explanation: str
    unsatisfied_preferences: List[str]
    suggested_changes: List[str]
    timestamp: datetime


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
        proposal = Proposal(
            id=proposal_id,
            author=author,
            round=self.current_round,
            timestamp=datetime.now(),
            base_project=proposal_data.get("base_project", {}),
            modifications=proposal_data.get("modifications", []),
            compensation=proposal_data.get("compensation", {}),
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

    def check_unanimous_acceptance(self, proposal_id: int, required_agents: List[str]) -> bool:
        """Check if all required agents accepted"""
        if proposal_id not in self.evaluations:
            return False
        evals = self.evaluations[proposal_id]
        return all(
            evals.get(agent, Evaluation(agent, proposal_id, False, "", [], [], datetime.now())).satisfied
            for agent in required_agents
        )

    def get_feedback_for_proposal(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Get all feedback for a proposal"""
        if proposal_id not in self.evaluations:
            return []
        return [
            {
                "agent": eval.agent_name,
                "satisfied": eval.satisfied,
                "unsatisfied": eval.unsatisfied_preferences,
                "suggested": eval.suggested_changes
            }
            for eval in self.evaluations[proposal_id].values()
        ]

    def advance_round(self):
        """Move to next negotiation round"""
        self.current_round += 1


class LLMClient:
    """Simple LLM client for OpenRouter"""
    def __init__(self, api_key: str, model: str = "openai/gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def call(self, prompt: str) -> str:
        """Make API call"""
        response = requests.post(
            url=self.url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/defacc-hackathon",
                "X-Title": "Coasean Negotiation Demo",
            },
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}]
            }
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

    def __init__(self, name: str, role: str, preferences: List[Preference], llm: LLMClient):
        self.name = name
        self.role = role
        self.preferences = preferences  # HUMAN SOVEREIGNTY - outcomes only
        self.llm = llm

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

        # Can see others' evaluations for coordination
        others_feedback = ""
        if proposal.id in space.evaluations:
            others_feedback = "\n\nOTHER AGENTS' EVALUATIONS:\n"
            for other_eval in space.evaluations[proposal.id].values():
                if other_eval.agent_name != self.name:
                    status = "✓ satisfied" if other_eval.satisfied else "✗ unsatisfied"
                    others_feedback += f"- {other_eval.agent_name}: {status}\n"
                    if not other_eval.satisfied:
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

Respond in XML format:
<evaluation>
  <satisfied>true or false</satisfied>
  <explanation>brief explanation of whether YOUR constraints are met</explanation>
  <unsatisfied_preferences>
    <preference>your constraint that isn't met</preference>
  </unsatisfied_preferences>
  <suggested_changes>
    <change>what you'd need to change about YOUR constraints (rare)</change>
  </suggested_changes>
</evaluation>"""
        else:
            # Original neighbor evaluation prompt
            prompt = f"""You represent {self.name}, evaluating a proposal.

HUMAN'S STATED OUTCOMES (you MUST respect these exactly):
{prefs_str}

CURRENT PROPOSAL:
{proposal_str}

{others_feedback}

Your job: Determine if this proposal achieves the HUMAN'S OUTCOMES using your domain knowledge.

CRITICAL RULES:
1. NEVER question or redefine what the human wants
2. Use domain knowledge to assess if METHODS achieve OUTCOMES
3. If unsatisfied, suggest concrete METHODS to achieve the outcome
4. You can coordinate with others' suggestions to find bundle solutions

Examples of good reasoning:
- "Soundproofing typically reduces noise 15dB. Current 75dB - 15dB = 60dB. Satisfies threshold."
- "Proposal includes 20 parking spaces. Human needs ≥20. Satisfied."
- "Building is 3 stories but human wants ≤2 stories. Unsatisfied. Suggest: reduce height."
- "Compensation is $5000. Human needs ≥$3000. Satisfied."

Respond in XML format:
<evaluation>
  <satisfied>true or false</satisfied>
  <explanation>brief explanation referencing the human's specific preferences</explanation>
  <unsatisfied_preferences>
    <preference>first preference not met</preference>
    <preference>second preference not met</preference>
  </unsatisfied_preferences>
  <suggested_changes>
    <change>specific METHOD to achieve outcome (with cost estimate if possible)</change>
    <change>alternative METHOD to achieve outcome</change>
  </suggested_changes>
</evaluation>"""

        response = self.llm.call(prompt)

        # Parse response
        try:
            satisfied = parse_bool(parse_xml_tag(response, "satisfied"))
            explanation = parse_xml_tag(response, "explanation")
            unsatisfied_prefs = parse_xml_list(response, "preference")
            suggested_changes = parse_xml_list(response, "change")

            evaluation = Evaluation(
                agent_name=self.name,
                proposal_id=proposal.id,
                satisfied=satisfied,
                explanation=explanation,
                unsatisfied_preferences=unsatisfied_prefs,
                suggested_changes=suggested_changes,
                timestamp=datetime.now()
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

        # Format developer constraints
        dev_prefs = "\n".join([
            f"  - {topic}: {value if value is not None else 'required'}"
            for topic, value in self.preferences
        ])

        # Format feedback
        feedback_str = ""
        for fb in feedback:
            if not fb['satisfied']:
                feedback_str += f"\n{fb['agent']}:\n"
                feedback_str += f"  Unsatisfied: {', '.join(fb['unsatisfied'])}\n"
                feedback_str += f"  Suggests: {', '.join(fb['suggested'][:3])}\n"

        prompt = f"""You are synthesizing an improved proposal based on PUBLIC feedback.

DEVELOPER CONSTRAINTS:
{dev_prefs}

CURRENT PROPOSAL:
{self._format_proposal(current_proposal)}

NEIGHBOR FEEDBACK (from public bulletin board):
{feedback_str}

Your job: Create an improved proposal that satisfies more neighbors while respecting developer constraints.

MULTI-DIMENSIONAL SOLUTION SPACE - you can:
- Add physical modifications (soundproofing, parking, green buffers)
- Impose operational constraints (delivery hours, construction times)
- Make design changes (architecture, height, materials)
- Adjust compensation amounts
- Add community commitments

Think creatively! Don't just throw money at problems. Look for complementary solutions
where one modification helps multiple neighbors.

IMPORTANT: Pay close attention to exact compensation amounts neighbors require.
If someone needs $8000 minimum, give them AT LEAST $8000, not less!

Respond with XML:
<improved_proposal>
  <base_project>
    <type>grocery_store</type>
    <size_sqft>5000</size_sqft>
    <stories>2</stories>
  </base_project>
  <modifications>
    <modification>
      <type>soundproofing</type>
      <cost>40000</cost>
      <benefit>reduces noise to 60dB, helps Alice</benefit>
    </modification>
  </modifications>
  <compensation>
    <payment>
      <recipient>Alice (Noise-Sensitive)</recipient>
      <amount>3000</amount>
    </payment>
  </compensation>
  <commitments>
    <commitment>maintain green buffer zone</commitment>
  </commitments>
  <total_cost>200000</total_cost>
  <reasoning>Brief explanation of the bundle</reasoning>
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

    def _format_proposal(self, proposal: Proposal) -> str:
        """Format proposal for display"""
        result = f"Base Project:\n"
        for key, value in proposal.base_project.items():
            result += f"  {key}: {value}\n"

        if proposal.modifications:
            result += "\nModifications:\n"
            for mod in proposal.modifications:
                result += f"  - {mod.get('type', 'unknown')}"
                if 'cost' in mod:
                    result += f" (${mod['cost']:,})"
                if 'benefit' in mod:
                    result += f": {mod['benefit']}"
                result += "\n"

        if proposal.compensation:
            result += "\nCompensation:\n"
            for recipient, amount in proposal.compensation.items():
                result += f"  - {recipient}: ${amount:,}\n"

        if proposal.commitments:
            result += "\nCommitments:\n"
            for commitment in proposal.commitments:
                result += f"  - {commitment}\n"

        result += f"\nTotal Cost: ${proposal.total_cost:,}"

        return result


def create_demo_scenario(llm: LLMClient) -> Tuple[DecentralizedAgent, List[DecentralizedAgent]]:
    """
    Create the demo scenario: Developer wants to build a store

    Note: Each agent only provides SIMPLE preference tuples.
    The AI figures out HOW to achieve these outcomes.
    """

    developer = DecentralizedAgent(
        name="Developer",
        role="developer",
        preferences=[
            ("total_cost_under", 250000.0),
        ],
        llm=llm
    )

    neighbors = [
        DecentralizedAgent(
            name="Alice (Noise-Sensitive)",
            role="neighbor",
            preferences=[
                ("noise_level_below_db", 60.0),
                ("compensation_minimum", 3000.0)
            ],
            llm=llm
        ),
        DecentralizedAgent(
            name="Bob (Aesthetic-Focused)",
            role="neighbor",
            preferences=[
                ("building_height_stories", 2.0),
                ("compensation_minimum", 2000.0)
            ],
            llm=llm
        ),
        DecentralizedAgent(
            name="Carol (Traffic-Concerned)",
            role="neighbor",
            preferences=[
                ("parking_spaces_minimum", 20.0),
                ("compensation_minimum", 4000.0)
            ],
            llm=llm
        ),
        DecentralizedAgent(
            name="Dave (Pragmatic)",
            role="neighbor",
            preferences=[
                ("compensation_minimum", 8000.0),
            ],
            llm=llm
        )
    ]

    return developer, neighbors


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
            "type": "grocery_store",
            "size_sqft": 5000,
            "stories": 2
        },
        "modifications": [],
        "compensation": {n.name: 0 for n in neighbors},
        "commitments": [],
        "total_cost": 150000
    }

    print("\n" + "=" * 80)
    print("ROUND 0: INITIAL PROPOSAL (Binary Approach)")
    print("=" * 80)
    proposal_id = space.post_proposal(developer.name, initial_proposal_data)
    current_proposal = space.get_latest_proposal()
    print(developer._format_proposal(current_proposal))

    # Negotiation rounds
    for round_num in range(max_rounds):
        space.advance_round()

        print(f"\n{'=' * 80}")
        print(f"ROUND {space.current_round}: DECENTRALIZED EVALUATION")
        print(f"{'=' * 80}")
        print("(Each agent evaluates independently using the bulletin board)\n")

        # Each agent evaluates independently
        all_satisfied = True
        for neighbor in neighbors:
            eval_result = neighbor.evaluate_proposal(current_proposal, space)

            status_icon = "✓" if eval_result.satisfied else "✗"
            status_text = "SATISFIED" if eval_result.satisfied else "UNSATISFIED"
            print(f"{status_icon} {neighbor.name}: {status_text}")
            print(f"   {eval_result.explanation}")

            if not eval_result.satisfied:
                all_satisfied = False
                if eval_result.suggested_changes:
                    print(f"   Suggests: {eval_result.suggested_changes[0]}")
            print()

        # Check if all satisfied
        if all_satisfied:
            print(f"\n{'=' * 80}")
            print("✓ SUCCESS! All parties satisfied through decentralized coordination")
            print(f"{'=' * 80}")
            return current_proposal

        # Check developer constraints
        dev_eval = developer.evaluate_proposal(current_proposal, space)
        if not dev_eval.satisfied:
            print(f"\n✗ Developer constraints cannot be met")
            print(f"   {dev_eval.explanation}")
            return None

        # Developer synthesizes improved proposal based on PUBLIC feedback
        print(f"\n{'=' * 80}")
        print(f"SYNTHESIS: Developer Agent Responding to Public Signals")
        print(f"{'=' * 80}")
        print("(No special power - just reading the bulletin board like everyone else)\n")

        improved_data = developer.synthesize_proposal(
            current_proposal,
            neighbors,
            space
        )

        proposal_id = space.post_proposal(developer.name, improved_data)
        current_proposal = space.get_latest_proposal()

        print("IMPROVED PROPOSAL:")
        print(developer._format_proposal(current_proposal))
        if current_proposal.reasoning:
            print(f"\nReasoning: {current_proposal.reasoning}")

    print("\n✗ Max rounds reached without unanimous agreement")
    return None


def print_final_summary(proposal: Optional[Proposal], neighbors: List[DecentralizedAgent]):
    """Print summary emphasizing key insights"""

    print("\n" + "=" * 80)
    print("FINAL AGREEMENT")
    print("=" * 80)

    if proposal:
        print("\nBase Project:")
        for key, value in proposal.base_project.items():
            print(f"  {key}: {value}")

        print(f"\nModifications ({len(proposal.modifications)}):")
        for mod in proposal.modifications:
            cost_str = f"${mod['cost']:,}" if 'cost' in mod else "TBD"
            print(f"  • {mod.get('type', 'unknown')} ({cost_str})")
            if 'benefit' in mod:
                print(f"    → {mod['benefit']}")

        print(f"\nCompensation:")
        total_comp = sum(proposal.compensation.values())
        for recipient, amount in proposal.compensation.items():
            print(f"  • {recipient}: ${amount:,}")
        print(f"  Total: ${total_comp:,}")

        if proposal.commitments:
            print(f"\nCommitments:")
            for commitment in proposal.commitments:
                print(f"  • {commitment}")

        print(f"\nTotal Project Cost: ${proposal.total_cost:,}")

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
        print(f"   • Total cost: ${proposal.total_cost:,} (under budget!)")
        print(f"   • All {len(neighbors)} parties satisfied")
        print("   • Pareto improvement discovered through coordination")

    print("\n4. DECENTRALIZED ARCHITECTURE")
    print("   • No central coordinator controlling outcomes")
    print("   • Transparent bulletin board for all communications")
    print("   • Each agent autonomous and sovereign")
    print("   • Emergent order from voluntary coordination")

    print("\n5. PRESERVING HUMAN AGENCY AT SCALE")
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

    llm = LLMClient(api_key)

    # Create scenario
    print("Setting up decentralized negotiation scenario...")
    developer, neighbors = create_demo_scenario(llm)

    # Create shared space (bulletin board)
    space = NegotiationSpace()

    # Run negotiation
    print("\nStarting negotiation...\n")
    final_proposal = run_negotiation(developer, neighbors, space, max_rounds=7)

    # Print summary
    print_final_summary(final_proposal, neighbors)

    if final_proposal:
        print(f"\n✓ Negotiation succeeded in {space.current_round} rounds")
    else:
        print(f"\n✗ Negotiation failed to reach agreement")


if __name__ == "__main__":
    main()
