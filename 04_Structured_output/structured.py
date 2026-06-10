from pydantic import BaseModel
import asyncio
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ResultMessage, query


# Define the expected output schema for the structured output:

schema = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "founded_year": {"type": "number"},
        "headquarters": {"type": "string"},
    },
    "required": ["company_name"],
}



async def main():
    async for message in query(
        prompt="When Anthropic made and where is it headquarter",
        options=ClaudeAgentOptions(
            output_format={"type": "json_schema", "schema": schema}
        )
    ):
        if isinstance(message, ResultMessage) and message.structured_output:
            print(f"\nCompany Name: {message.structured_output["company_name"]}")
            print(f"\nFounded Year: {message.structured_output["founded_year"]}")
            print(f"\nHeadQuarter is in: {message.structured_output["headquarters"]}")



# asyncio.run(main())



# Using Pydantic for structured output validation without manually defining the schema:

class MomThreatReport(BaseModel):
    situation: str
    threat_level: str            # "chill" | "warning" | "danger" | "run_to_nana_house"
    estimated_grounding_days: int
    weapon_of_choice: str        # "chappal" | "jhadu" | "silent_treatment" | "emotional_guilt_trip"
    survival_tip: str            # agent ka advice — kaise bachna hai
    predicted_mom_roasted_funny_quote: str



async def main():
    async for messsage in query(
        prompt="Analyze this situation: I told my mom I want to become a YouTuber instead of a doctor. I accidentally broke mom's favorite chai cup. Mom found out I've been gaming till 4am every night.",
        options=ClaudeAgentOptions(output_format={"type": "json_schema", "schema": MomThreatReport.model_json_schema()})
    ):
        if isinstance(messsage, ResultMessage) and messsage.structured_output:
            report = MomThreatReport.model_validate(messsage.structured_output)
            print(f"\n\n Situation       : {report.situation}")
            print(f"Threat Level    : {report.threat_level}")
            print(f"Grounding Days  : {report.estimated_grounding_days} days")
            print(f"Weapon          : {report.weapon_of_choice}")
            print(f"Survival Tip    : {report.survival_tip}")
            print(f"Mom Will Say    : '{report.predicted_mom_roasted_funny_quote}'\n\n")
        elif isinstance(messsage, ResultMessage) and messsage.subtype == "error_max_structured_output_retries":
            print("Could not produce valid output — Please simplify the schema and clearly define the prompt.")



asyncio.run(main())
