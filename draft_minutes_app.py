from dotenv import load_dotenv 
import os
import streamlit as st
from langchain.text_splitter import TokenTextSplitter
from langchain_openai.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain, LLMChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain


def getOutputSummary(docs):
    load_dotenv()
    llm = ChatOpenAI(model="gpt-3.5-turbo-1106",temperature=0.1,
                 api_key= os.environ.get('OPENAI_API_KEY'),organization=os.environ.get('OPENAI_ORG_ID'))
    
    map_template = """Please generate an elaborate minutes of a business meeting based on the following meeting transcript content. 
                    Ensure that the minutes are written in formal business language with legal references and includes all essential details.
                    Also ensure that each summary must contain atleast 700 words
                    {content}
                    Summary:
                    """
    map_prompt = PromptTemplate.from_template(map_template)
    map_chain = LLMChain(llm=llm, prompt=map_prompt)
    
    reduce_template = """The following are the summaries extracted from the transcript of a single meeting containing all the essential details:
                        {doc_summaries}
                        Summarize the content of {doc_summaries} to generate an elaborated Minutes of meetings.
                        Split the generated minutes by agenda points in different blocks.
                        Specify date,time,location and title of the meeting at the beginning.
                        The length of the final summarized Minutes of meeting must be at least 5000 words.
                        Summary:"""
    reduce_prompt = PromptTemplate.from_template(reduce_template)
    reduce_chain = LLMChain(llm=llm, prompt=reduce_prompt)
    
    combine_documents_chain = StuffDocumentsChain(llm_chain=reduce_chain, document_variable_name="doc_summaries")
    
    reduce_documents_chain = ReduceDocumentsChain(
    # This is final chain that is called.
    combine_documents_chain=combine_documents_chain,
    # If documents exceed context for `StuffDocumentsChain`
    collapse_documents_chain=combine_documents_chain,
    # The maximum number of tokens to group documents into.
    token_max=8000)
   
    map_reduce_chain = MapReduceDocumentsChain(
    # Map chain
    llm_chain=map_chain,
    # Reduce chain
    reduce_documents_chain=reduce_documents_chain,
    # The variable name in the llm_chain to put the documents in
    document_variable_name="content",
    # Return the results of the map steps in the output
    return_intermediate_steps=False)
    splitter = TokenTextSplitter(chunk_size=2500,chunk_overlap=50)
    split_docs = splitter.create_documents([docs])
    return map_reduce_chain.run(split_docs)

def main():
    st.set_page_config(page_title='Transcript Summary Generator')
    st.header('Generated Transcript Summary')
    side = st.sidebar
    side.subheader('Your Transcript')
    text_file = side.file_uploader('Upload your transcript file of .txt format here',type=['txt'],
                                   help='Ensure that the transcript file is of right format i.e. .txt')
    #agenda_doc = side.file_uploader('Upload your agenda file of .txt or .docx format here',type=['txt','docx'])
    if side.button('Generate Summary'):
        with st.spinner('Processing'):
            raw_text = text_file.read()  
            #raw_agenda = agenda_doc.read()
            output_summary = getOutputSummary(raw_text.decode('utf-8','replace'))
            watermark = '''\n:grey[Generated by proCS BMS.ai \nThis is an AI generated MoM from the transcript file provided :flag-ai::copyright:]'''
            st.write(output_summary)  
            st.write(watermark) 
            if output_summary:
                st.download_button(label="Download Summary",data = output_summary, file_name='Generaeted_Summary.txt')
                   
            
if __name__ == '__main__':
    main()
