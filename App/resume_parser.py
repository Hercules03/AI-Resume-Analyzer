import os
import multiprocessing as mp
import io
import spacy
import pprint
import re
from spacy.matcher import Matcher
from pyresparser import utils
from pdf_processing import pdf_processor


# Custom extract_name function to handle spaCy compatibility issues
def extract_name_custom(nlp_text, matcher):
    """
    Custom function to extract names from resume text, compatible with newer spaCy versions
    """
    pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]  # Simple pattern for proper nouns
    
    # Use the new spaCy Matcher.add API (without on_match as positional argument)
    matcher.add("NAME", [pattern])
    
    doc = nlp_text if hasattr(nlp_text, 'ents') else nlp_text
    matches = matcher(doc)
    
    for match_id, start, end in matches:
        span = doc[start:end]
        return span.text
    
    # Fallback: Extract from entities
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    
    # Fallback: Simple regex pattern for names at the beginning
    text = str(doc)
    lines = text.split('\n')
    for line in lines[:3]:  # Check first 3 lines
        line = line.strip()
        if line and len(line.split()) <= 4:  # Likely a name if 1-4 words
            # Check if it looks like a name (starts with capital letters)
            words = line.split()
            if all(word[0].isupper() for word in words if word):
                return line
    
    return None


class ResumeParser(object):

    def __init__(
        self,
        resume,
        skills_file=None,
        custom_regex=None
    ):
        nlp = spacy.load('en_core_web_sm')
        try:
            custom_nlp = spacy.load(os.path.dirname(os.path.abspath(__file__)))
        except (OSError, IOError) as e:
            # Fallback to standard model if custom model fails to load
            print(f"Warning: Custom spaCy model not found ({e}), using standard model")
            custom_nlp = nlp
        self.__skills_file = skills_file
        self.__custom_regex = custom_regex
        self.__matcher = Matcher(nlp.vocab)
        self.__details = {
            'name': None,
            'email': None,
            'mobile_number': None,
            'skills': None,
            'degree': None,
            'no_of_pages': None,
        }
        self.__resume = resume
        if not isinstance(self.__resume, io.BytesIO):
            ext = os.path.splitext(self.__resume)[1].split('.')[1]
        else:
            ext = self.__resume.name.split('.')[1]
        
        # Use centralized PDF processor for text extraction
        try:
            if ext.lower() == 'pdf':
                self.__text_raw = pdf_processor.extract_text_hybrid(self.__resume, development_mode=False)
            else:
                self.__text_raw = utils.extract_text(self.__resume, '.' + ext)
        except Exception as e:
            print(f"Text extraction failed, using fallback: {e}")
            self.__text_raw = utils.extract_text(self.__resume, '.' + ext)
        
        self.__text = ' '.join(self.__text_raw.split())
        self.__nlp = nlp(self.__text)
        self.__custom_nlp = custom_nlp(self.__text_raw)
        self.__noun_chunks = list(self.__nlp.noun_chunks)
        self.__get_basic_details()

    def get_extracted_data(self):
        return self.__details

    def __get_basic_details(self):
        cust_ent = utils.extract_entities_wih_custom_model(
                            self.__custom_nlp
                        )
        # Use our custom extract_name function instead of the problematic one
        name = extract_name_custom(self.__nlp, self.__matcher)
        email = utils.extract_email(self.__text)
        mobile = utils.extract_mobile_number(self.__text, self.__custom_regex)
        skills = utils.extract_skills(
                    self.__nlp,
                    self.__noun_chunks,
                    self.__skills_file
                )

        entities = utils.extract_entity_sections_grad(self.__text_raw)

        # extract name
        try:
            self.__details['name'] = cust_ent['Name'][0]
        except (IndexError, KeyError):
            self.__details['name'] = name

        # extract email
        self.__details['email'] = email

        # extract mobile number
        self.__details['mobile_number'] = mobile

        # extract skills
        self.__details['skills'] = skills

        # no of pages
        self.__details['no_of_pages'] = utils.get_number_of_pages(self.__resume)

        # extract education Degree
        try:
            self.__details['degree'] = cust_ent['Degree']
        except KeyError:
            pass

        return


def resume_result_wrapper(resume):
    parser = ResumeParser(resume)
    return parser.get_extracted_data()


if __name__ == '__main__':
    pool = mp.Pool(mp.cpu_count())

    resumes = []
    data = []
    for root, directories, filenames in os.walk('resumes'):
        for filename in filenames:
            file = os.path.join(root, filename)
            resumes.append(file)

    results = [
        pool.apply_async(
            resume_result_wrapper,
            args=(x,)
        ) for x in resumes
    ]

    results = [p.get() for p in results]

    pprint.pprint(results)
