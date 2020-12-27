from whoosh.index import create_in
# from whoosh.fields import *

from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
from whoosh.analysis import StemmingAnalyzer

import json
import ndjson

import os.path
from whoosh.index import create_in

from whoosh.index import open_dir

from whoosh.query import *
from whoosh.qparser import QueryParser

import spacy
from whoosh import highlight


class Reader:
    def get_result(self, input):
        schema = Schema(abstract=TEXT(stored=True), sentences = TEXT(stored=True))

        if not os.path.exists("index"):
            os.mkdir("index")

        # create an index
        ix = create_in("index", schema)
        # open an index
        # ix = open_dir("index")
        
        # create writer
        writer = ix.writer()

        # load spacy model
        nlp = spacy.load('en_core_web_sm')

        ## add all the corpus with their submitters and abstract
        with open('condensed_data.ndjson') as f:
            data = ndjson.load(f)
            ## add all the abstract to find the keyword
            for p in data:
                writer.add_document(abstract = u(p["abstract"]))
        writer.commit()
        ## create searcher
        searcher = ix.searcher()

        qp = QueryParser("abstract", schema=ix.schema)
        q = qp.parse(input)

        results = searcher.search(q)

        ## separate index and writer for sentences. 
        sentence_ix = create_in("index", schema)
        sentence_writer = sentence_ix.writer()

        for hit in results:
            doc = nlp(hit["abstract"])
            sentences = list(doc.sents)
            ## add document of every sentence which abstracts contain the keyword 
            for s in sentences:
                sentence_writer.add_document(sentences = u(s.orth_))

        sentence_writer.commit()

        ## second searcher to find the keyword amongs the sentences that were filtered once with the abstract 
        sentence_searcher = sentence_ix.searcher()

        s_qp = QueryParser("sentences", schema = sentence_ix.schema)
        sq = s_qp.parse(input)
        sentence_results = sentence_searcher.search(sq)
        
        ## unlimit the number of characters 
        sf = highlight.SentenceFragmenter(charlimit = None)
        sentence_results.fragmenter = sf

        final_result_str =''
        ## add all highlighted sentences to return value
        for hit in sentence_results:
            for t in nlp(hit['sentences']):
                if t.dep_ == "nsubj" and t.orth_ == input:
                    final_result_str += hit.highlights("sentences") + '.'
                    final_result_str += '\n\n'
        return final_result_str
