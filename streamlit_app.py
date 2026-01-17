import streamlit as st
import pandas as pd
from verifier import verify_document


def get_verdict_color(verdict: str) -> str:
    color_map = {
        "Verified": "#28a745",
        "Inaccurate": "#dc3545",
        "False": "#dc3545",
        "Outdated": "#ffc107",
        "Unverifiable": "#6c757d",
        "Error": "#dc3545"
    }
    return color_map.get(verdict, "#6c757d")


def style_dataframe(df: pd.DataFrame) -> str:
    styles = []
    for idx, row in df.iterrows():
        color = get_verdict_color(row['Verdict'])
        styles.append({
            'selector': f'tbody tr:nth-child({idx+1})',
            'props': [('background-color', f'{color}22')]
        })
    return styles


def main():
    st.set_page_config(
        page_title="Fact-Checking Web App",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("Fact-Checking Web App")
    st.markdown("Upload a PDF document to extract and verify claims against live web data.")
    
    if 'OPENAI_API_KEY' not in st.secrets or 'TAVILY_API_KEY' not in st.secrets:
        st.error("API keys not configured. Please set OPENAI_API_KEY and TAVILY_API_KEY in Streamlit secrets.")
        st.stop()
    
    openai_key = st.secrets['OPENAI_API_KEY']
    tavily_key = st.secrets['TAVILY_API_KEY']
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a PDF document containing claims to verify"
    )
    
    if uploaded_file is not None:
        st.success(f"File uploaded: {uploaded_file.name}")
        
        if st.button("Start Verification", type="primary"):
            try:
                with st.spinner("Processing document and verifying claims..."):
                    results = verify_document(uploaded_file, openai_key, tavily_key)
                
                if not results:
                    st.warning("No verifiable claims were extracted from the document.")
                    return
                
                st.success(f"Verification complete! Found {len(results)} claims.")
                
                st.markdown("---")
                st.subheader("Verification Results")
                
                df_data = []
                for result in results:
                    df_data.append({
                        "Original Claim": result.original_claim,
                        "Verdict": result.verdict,
                        "Correction/Evidence": result.evidence,
                        "Source URL": result.source_url
                    })
                
                df = pd.DataFrame(df_data)
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                verified_count = len([r for r in results if r.verdict == "Verified"])
                inaccurate_count = len([r for r in results if r.verdict in ["Inaccurate", "False"]])
                outdated_count = len([r for r in results if r.verdict == "Outdated"])
                unverifiable_count = len([r for r in results if r.verdict == "Unverifiable"])
                error_count = len([r for r in results if r.verdict == "Error"])
                
                col1.metric("Verified", verified_count)
                col2.metric("Inaccurate/False", inaccurate_count)
                col3.metric("Outdated", outdated_count)
                col4.metric("Unverifiable", unverifiable_count)
                col5.metric("Errors", error_count)
                
                st.markdown("---")
                
                for idx, result in enumerate(results):
                    color = get_verdict_color(result.verdict)
                    
                    with st.container():
                        st.markdown(f"""
                        <div style='padding: 15px; border-left: 5px solid {color}; background-color: {color}15; margin-bottom: 15px; border-radius: 5px;'>
                            <strong style='color: {color}; font-size: 1.1em;'>{result.verdict}</strong>
                            <p style='margin: 10px 0;'><strong>Claim:</strong> {result.original_claim}</p>
                            <p style='margin: 10px 0;'><strong>Evidence:</strong> {result.evidence}</p>
                            <p style='margin: 10px 0;'><strong>Source:</strong> <a href='{result.source_url}' target='_blank'>{result.source_url}</a></p>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.subheader("Download Results")
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name="fact_check_results.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"An error occurred during verification: {str(e)}")
                st.exception(e)
    
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This application uses advanced language models and web search to verify factual claims in documents.
        
        **How it works:**
        1. Upload a PDF document
        2. Claims are extracted automatically
        3. Each claim is verified against live web data
        4. Results show verdict with supporting evidence
        
        **Verdict Types:**
        - **Verified**: Claim matches current evidence
        - **Inaccurate**: Numbers or facts don't match
        - **Outdated**: Information is no longer current
        - **False**: Claim contradicts evidence
        - **Unverifiable**: Insufficient data to verify
        """)
        
        st.markdown("---")
        st.markdown("**Tech Stack:**")
        st.markdown("- OpenAI GPT-4o")
        st.markdown("- Tavily Search API")
        st.markdown("- LangChain")
        st.markdown("- Streamlit")


if __name__ == "__main__":
    main()
