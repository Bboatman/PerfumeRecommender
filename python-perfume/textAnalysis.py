import json, pickle, re, time, os
import numpy as np
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.utils import simple_preprocess
from sklearn.manifold import TSNE, SpectralEmbedding, MDS
from sklearn.decomposition import PCA
from sklearn import preprocessing
from matplotlib import pyplot
import os
script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
rel_path = "fragrances.p"
pickleFile = os.path.join(script_dir, rel_path)

class Vectorizor:
    def __init__(self, model_dimensionality = 5):
        print("Initializing")
        dirname = os.path.dirname(__file__)
        self.model_dimensionality = model_dimensionality
        self.fragrance_json_path = os.path.join(dirname, '../models/data.json')
        self.word2vec_model_path = os.path.join(dirname,'../models/fragrance_vector_model.model')
        self.model_dimensionality_path = os.path.join(dirname, '../models/fragrance_' + str(self.model_dimensionality) + 'd_model.model')
        self.twod_model_path = os.path.join(dirname,'../models/fragrance_2d_model.model')
        self.keyed_vector_path = os.path.join(dirname,'../models/fragrance_vector.kv')
        self.training_model_path = os.path.join(dirname,"../models/training_seq.p")
        self.fragrance_data_path = os.path.join(dirname,"../models/fragrance_data.p")
        self.train_seq = []
        
    def load_training_sequence(self, clean=False):
        try:
            obj = pickle.load( open( self.training_model_path, "rb" ) )
        except:
            obj = self.get_fragrances_from_json()

        if clean: 
            print("Cleaning Training Model")
            self.twodmodel = Doc2Vec(vector_size=2, min_count=1, epochs=40, ns_exponent=.75)
            self.multimodel = Doc2Vec(vector_size=self.model_dimensionality, min_count=1, epochs=40, ns_exponent=.75)
            self.model = Doc2Vec(vector_size=52, min_count=1, epochs=40, ns_exponent=.75)
        else:
            try:
                self.twodmodel = Doc2Vec.load(self.twod_model_path) 
                self.multimodel = Doc2Vec.load(self.model_dimensionality_path) 
                self.model = Doc2Vec.load(self.word2vec_model_path)
            except:
                print("Failed to load")
                self.twodmodel = Doc2Vec(vector_size=2, min_count=1, epochs=40, ns_exponent=.75)
                self.multimodel = Doc2Vec(vector_size=self.model_dimensionality, min_count=1, epochs=40, ns_exponent=.75)
                self.model = Doc2Vec(vector_size=52, min_count=1, epochs=40, ns_exponent=.75)
                clean = True
                
        count = len(self.model.dv)
        for i, f in enumerate(obj):
            phrase = f.body
            doc = TaggedDocument(simple_preprocess(phrase), [i + count])
            self.train_seq.append(doc)
        
        if clean:
            self.train_model(True)

    def train_model(self, build = False):
        if build: 
            print("Building Vocab")
            self.model.build_vocab(self.train_seq)
            self.twodmodel.build_vocab(self.train_seq)
            self.multimodel.build_vocab(self.train_seq)
        
        print("Training Model")
        self.model.train(self.train_seq, total_examples=self.model.corpus_count, \
            epochs=self.model.epochs)
        self.multimodel.train(self.train_seq, total_examples=self.model.corpus_count, \
            epochs=self.model.epochs)
        self.twodmodel.train(self.train_seq, total_examples=self.model.corpus_count, \
            epochs=self.model.epochs)
        if build:
            f = open(self.word2vec_model_path, "w+")
            f.close()
            f = open(self.model_dimensionality_path, "w+")
            f.close()
            f = open(self.twod_model_path, "w+")
            f.close()
        self.model.save(self.word2vec_model_path)
        self.twodmodel.save(self.twod_model_path)
        self.multimodel.save(self.model_dimensionality_path)

    def get_fragrances_from_json(self, update_training_model= False, progress_print = False):
        print("Getting fragrances from JSON")
        t = time.time()
        json_file = open(self.fragrance_json_path)
        data = json.load(json_file)
        json_file.close()

        if (update_training_model):
            obj = []
        else:
            try:
                obj = pickle.load(open( self.training_model_path, "rb" ))
            except: 
                obj = []
                update_training_model = True

        count = 0
        fragrance_array = []

        for entry in data:
            c = Fragrance(entry)
            fragrance_array.append(c)
            count += 1
            obj += c.tokenize_text()
        
        t = time.time() - t
        print(f"Got {len(fragrance_array)} fragrances in {t} time")
        return fragrance_array

    def build_clean_array(self):
        fragrance_array = self.get_fragrances_from_json()
        for t in fragrance_array: 
            tokens = t.tokenize_text()
            t.simple_vec = self.multimodel.infer_vector(tokens)
            t.long_vec = self.model.infer_vector(tokens) # There's something wrong with this??
        return fragrance_array
    
    def pickleFragranceList(self, fragranceList):
        pickle.dump(fragranceList, open(pickleFile, "wb" ))
    
    def dumpJSONData(self, fragranceList):
        print(len(fragranceList))
        dumpObj = []
        for x in fragranceList:
            obj = {
                "name": x.name,
                "body": x.body,
                "tags": x.tags,
                "notes": x.notes,
                "simple_vec": [ (y+1)/ 2 for y in x.simple_vec.tolist() ]
            }
            dumpObj.append(obj)

        with open(self.fragrance_json_path, 'w') as outfile:
            json.dump(dumpObj, outfile)
            print("dumping data")

class Fragrance:
    delimiters = "\n", ".", ",", ":"
    regexPattern = '|'.join(map(re.escape, delimiters))
    name = ""
    body = ""
    tags = []
    notes = []
    simple_vec = []
    long_vec = []

    def __init__(self, json_info=None):
        if (json_info != None):
            if 'tags' in json_info and len(json_info['tags']) > 0:
                self.tags = json_info['tags']
            if 'notes' in json_info and len(json_info['notes']) > 0:
                self.notes = json_info['notes']
            self.name = json_info['name'].lower()
            if 'body' in json_info:
                self.body = json_info['body']

    def tokenize_text(self):
        body = self.body.lower()
        name = self.name.lower()
        txt = body.replace(name, "~self~")
        arr = re.split(self.regexPattern, txt)
        tokens = [x.strip() for x in arr]
        tokens = filter(None, tokens)
        return tokens

def vectorizeFragrances():
    print("Vectorizing Cards")
    model_dimensionality = 4
    try:
        v = Vectorizor(model_dimensionality)
        v.load_training_sequence(False)
        fragrance_array = v.build_clean_array()
        v.dumpJSONData(fragrance_array)

    except Exception as e: 
        print(e)

vectorizeFragrances()