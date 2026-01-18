import re
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from tavily import TavilyClient
import PyPDF2


class ExtractedClaim(BaseModel):
    claim_text: str = Field(description="The atomic, verifiable claim extracted from text")
    claim_type: str = Field(description="Type of claim: statistic, date, financial, technical, or factual")


class ClaimsList(BaseModel):
    claims: List[ExtractedClaim] = Field(description="List of extracted claims")


class VerificationResult(BaseModel):
    original_claim: str
    verdict: str
    evidence: str
    source_url: str


def extract_text_from_pdf(pdf_file) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_content = ""
        
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n"
        
        if not text_content.strip():
            raise ValueError("No text could be extracted from the PDF")
        
        return text_content.strip()
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def extract_claims(text: str, llm: ChatGoogleGenerativeAI) -> List[ExtractedClaim]:
    parser = PydanticOutputParser(pydantic_object=ClaimsList)
    
    system_message = """You are a critical fact-checking analyst with expertise in identifying verifiable claims.
Your task is to extract ONLY atomic, verifiable claims from the provided text.

FOCUS ON:
- Statistical claims with specific numbers
- Dates and temporal assertions
- Financial figures and monetary values
- Technical specifications and measurements
- Concrete factual statements about events or entities

IGNORE:
- Subjective opinions and value judgments
- Predictions or speculations
- General statements without specific data
- Contextual information without verifiable facts

Be skeptical and precise. Extract each claim as a standalone statement that can be independently verified against external sources.
Look for claims that could be intentionally misleading, outdated, or factually incorrect."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("user", "Extract all verifiable claims from this text:\n\n{text}\n\n{format_instructions}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        result = chain.invoke({
            "text": text,
            "format_instructions": parser.get_format_instructions()
        })
        return result.claims
    except Exception as e:
        fallback_claims = extract_claims_fallback(text, llm)
        return fallback_claims


def extract_claims_fallback(text: str, llm: ChatGoogleGenerativeAI) -> List[ExtractedClaim]:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract verifiable claims with numbers, dates, or specific facts. Return each claim on a new line starting with 'CLAIM:'."),
        ("user", "{text}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"text": text})
    
    claims = []
    for line in response.content.split("\n"):
        if line.strip().startswith("CLAIM:"):
            claim_text = line.replace("CLAIM:", "").strip()
            if claim_text:
                claims.append(ExtractedClaim(
                    claim_text=claim_text,
                    claim_type="factual"
                ))
    
    return claims if claims else [ExtractedClaim(claim_text=text[:200], claim_type="general")]


def search_claim(claim: str, tavily_client: TavilyClient) -> Dict[str, Any]:
    try:
        search_query = formulate_search_query(claim)
        results = tavily_client.search(
            query=search_query,
            search_depth="advanced",
            max_results=5
        )
        return results
    except Exception as e:
        return {"results": [], "error": str(e)}


def formulate_search_query(claim: str) -> str:
    numbers = re.findall(r'\d+(?:\.\d+)?(?:\s*(?:million|billion|trillion|percent|%|thousand))?', claim)
    dates = re.findall(r'\b(?:19|20)\d{2}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', claim)
    
    query_parts = []
    
    if numbers:
        query_parts.append(claim)
    elif dates:
        query_parts.append(claim)
    else:
        words = claim.split()
        key_terms = [w for w in words if len(w) > 4 and w[0].isupper()]
        if key_terms:
            query_parts.extend(key_terms[:3])
        else:
            query_parts.append(claim[:100])
    
    return " ".join(query_parts)


def verify_claim_against_results(claim: str, search_results: Dict[str, Any], llm: ChatGoogleGenerativeAI) -> Dict[str, str]:
    if "error" in search_results or not search_results.get("results"):
        return {
            "verdict": "Unverifiable",
            "evidence": "Unable to find relevant sources to verify this claim",
            "source_url": "N/A"
        }
    
    results_text = ""
    source_urls = []
    
    for idx, result in enumerate(search_results["results"][:3], 1):
        results_text += f"\nSource {idx}: {result.get('content', '')}\n"
        source_urls.append(result.get('url', ''))
    
    verification_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a skeptical fact-checker analyzing claims against evidence.

STRICT VERIFICATION RULES:
1. If numbers in the claim do NOT match the sources, mark as "Inaccurate"
2. If dates are outdated (claim says 2023 but sources show 2024/2025 data), mark as "Outdated"
3. If the claim contradicts the evidence, mark as "False"
4. Only mark as "Verified" if evidence directly supports the claim with matching data
5. Look for intentional deception, cherry-picked statistics, or misleading context

Return ONLY one of: Verified, Inaccurate, Outdated, False, or Unverifiable
Then provide a brief evidence statement explaining your verdict."""),
        ("user", "Claim: {claim}\n\nEvidence from search results:\n{evidence}\n\nProvide verdict and explanation:")
    ])
    
    chain = verification_prompt | llm
    
    try:
        response = chain.invoke({
            "claim": claim,
            "evidence": results_text
        })
        
        verdict_text = response.content.strip()
        
        verdict = "Unverifiable"
        for v in ["Verified", "Inaccurate", "Outdated", "False", "Unverifiable"]:
            if v.lower() in verdict_text.lower():
                verdict = v
                break
        
        evidence = verdict_text.replace(verdict, "").strip()
        if not evidence:
            evidence = verdict_text
        
        return {
            "verdict": verdict,
            "evidence": evidence[:300],
            "source_url": source_urls[0] if source_urls else "N/A"
        }
    except Exception as e:
        return {
            "verdict": "Error",
            "evidence": f"Verification failed: {str(e)}",
            "source_url": "N/A"
        }


def verify_document(pdf_file, google_key: str, tavily_key: str) -> List[VerificationResult]:
    text = extract_text_from_pdf(pdf_file)
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        google_api_key=google_key
    )
    
    tavily_client = TavilyClient(api_key=tavily_key)
    
    claims = extract_claims(text, llm)
    
    results = []
    
    for claim in claims:
        search_results = search_claim(claim.claim_text, tavily_client)
        verification = verify_claim_against_results(claim.claim_text, search_results, llm)
        
        results.append(VerificationResult(
            original_claim=claim.claim_text,
            verdict=verification["verdict"],
            evidence=verification["evidence"],
            source_url=verification["source_url"]
        ))
    
    return results
