import pandas as pd

import Levenshtein
import re
import nltk
nltk.download('punkt')
nltk.download('stopwords')

import skrub

stop_words = set(nltk.corpus.stopwords.words('english'))
stop_words.add("please")
stop_words.add("specify")
stop_words.discard("where")
stop_words.discard("how")
stop_words.discard("when")
stop_words.discard("why")

def get_normalized_edit_distance(s1, s2):
    try:
        edit_distance = Levenshtein.distance(s1, s2)
        edit_distance /= max(len(s1), len(s2))
    except:
        edit_distance = 1.0
    return edit_distance

def find_common_words(df, lbl_col):
    full_text = ""
    df = df[df[lbl_col].notnull()]
    for index, row in df.iterrows():
        full_text = full_text + " " + row[lbl_col]
    allWords = nltk.tokenize.word_tokenize(full_text)
    allWordDist = nltk.FreqDist(w.lower() for w in allWords)
    mostCommon= allWordDist.most_common(10)
    common_words = []
    for item in mostCommon:
        common_words.append(item[0])
    return common_words

def remove_common_words(df,
                        lbl_col,
                        common_words):

    for index, row in df.iterrows():
        sentence = row[lbl_col]
        word_tokens = nltk.tokenize.word_tokenize(sentence)
        filtered_sentence = " "
        for w in word_tokens:
            if w not in common_words:
                filtered_sentence = filtered_sentence + " " + w
        row[lbl_col] = filtered_sentence

def process_label(s):

    try:
        # remove call to ODK variable
        s = re.sub(r'[$]+{.*?}', '', s)
        # remove HTML tags
        s = re.sub(r'<.*?>', '', s)
        # Remove question number
        s = re.sub(r'\w*[0-9]*.*[0-9]*\) ', '', s)
        # Remove punctuations and convert characters to lower case
        #s = "".join([char.lower() for char in s if char not in string.punctuation]).strip()
        s = s.lower().replace(".", "").replace("?", "").replace("'", "").strip()
        # Remove stop words
        word_tokens = nltk.tokenize.word_tokenize(s)
        out = " ".join([w for w in word_tokens if not w in stop_words])
    except:
        out = s

    return out

def print_n_diff_in_forms(row):

    n = row["N"] - row["N0"]

    if n == 0:
        s = "Same number of variables"
    elif n > 0:
        s = "{} Variables added".format(n)
    else:
        s = "{} Variables deleted".format(abs(n))

    return s

"""The Datadic class is a Python class designed to represent and manipulate information related to REDCap data dictionaries."""

class DataDic:

    # Class Attributes
    """_defaults (Class-level attribute): This dictionary defines default values for certain attributes of the Form class.
    Currently, it includes the key "survey" with a default value of None."""
    _defaults = {
        "survey_type": None
    }
    
    # Constructor
    """The constructor initializes a new Form object with the provided parameters.

    in_csv (string): The path to the REDCap data dictionary file from which the survey information is read.
    survey_type (string): A string representing the survey type, which is passed as an argument to the constructor.
    
    Inside the constructor, the provided REDcap data dictionary file is read, and relevant survey information is extracted and stored as instance variables:
    
    _id (string): The unique identifier of the form extracted from the XLSForm.
    _label (string): The title or label of the form extracted from the XLSForm.
    _version (tuple): The version information extracted from the XLSForm.
    _default_language (tuple): The default language information extracted from the XLSForm.
    _dtype (object): The data dictionary type object passed as a parameter to the constructor.
    
    It is important to ensure that the Form objects are properly initialized with the required survey information before using these comparison methods."""
    def __init__(self,
                 in_csv,
                 dtype):
        
        # Read and import raw data from XLSForm
        try:
            self._df   = pd.read_csv(in_csv).reset_index().dropna(axis=1, how="all")
        except:
            self._df = None
            print ("No CSV found")

        self._dtype       = dtype

        # Load forms and Variables
        self._forms      = self._df.groupby(["Form Name"])["Form Name"].count().to_frame(name = "N").reset_index().rename(columns = {"Form Name": "Forms"})
        self._vars       = self._df[self._df["Variable / Field Name"].notnull()].rename(columns = {"Variable / Field Name": "Variables",
                                                                                                   "Form Name": "Forms"})
        self._pii        = self._vars[self._vars["Identifier?"] == "y"]
        
        # Extract statistics
        self._nforms     = len(self._forms)
        self._nvariables = len(self._vars.index)

    # Instance Methods

    def getType(self):

        return self._dtype

    def getDictionary(self):

        return self._df
    
    def getNumVariables(self):

        return self._nvariables
    
    def getForms(self):

        return self._forms
    
    def getNumForms(self):

        return self._nforms

    def printNumForms(self):

        s = "The REDCap data dictionary contains {} forms.".format(self._nforms)
        return s
    
    def getVariables(self):

        return self._vars
    
    def getIdentifiers(self):

        return self._pii[["Variables", "Forms", "Field Type", "Field Label"]]
    
    def getCommonWords(self):

        return self._common_words
    
    """This method is intended to return the parent of the form.
    However, the parent attribute (_parent) is not set within the class, so this method may not provide the expected functionality without additional implementation."""
    
    def getParent(self):

        return self._parent
    
    """This method takes another DataDic object (d) as an argument and compares various attributes of the current data dictionary with the attributes of the provided data dictionary.
    It returns a formatted string containing comparison results."""
    def compareForms(self, f):

        out1 = self.compareNumForms(f)
        out2 = self.detectAddedForms(f)
        out = "{}\n{}".format(out1,
                              out2)
        return out
    
    """This method compares the number of forms of the current data dictionary with the number of forms attribute of the provided data dictionary.
    It returns a string indicating whether the numbers are identical or different."""
    def compareNumForms(self, f):

        n = f.getNumForms()
        out = ""
        if self._nforms > n:
            out = "Increased number of forms: {} vs. {}".format(self._nforms, n)
        elif self._nforms < n:
            out = "Decreased number of forms: {} vs. {}".format(self._nforms, n)
        else:
            out = "Same number of forms: {}".format(self._nforms)
        return out
    
    # Identical question
    def detectIdenticalVarNames(self, f):
        
        df1 = self._vars
        df2 = f.getVariables()
        colnames = ["Variables"]
        out = pd.merge(left = df1,
                       right = df2,
                       on = colnames,
                       suffixes = (None, "0"),
                       how = "inner")
        if (out.shape[0] == 0):
            out = None
        else:
            out = out[["index", "Forms"]].groupby("Forms").count().rename(columns = {"index": "Same variable"})

        return out
    
    # Identical question
    def detectIdenticalVariables(self, f):

        out          = None
        sum          = None
        identical    = None
        nonidentical = None
        
        # Identical variables
        df1 = self._vars
        df2 = f.getVariables()
        colnames = [i for i in df1.columns.tolist() if i != "index"]
        out = pd.merge(left = df1,
                       right = df2,
                       on = colnames,
                       suffixes = (None, "0"),
                       how = "outer",
                       indicator = True)
        if (out.shape[0] > 0):
            identical = out[out["_merge"] == "both"]
            sum = identical[["index", "Forms"]].groupby("Forms").count().rename(columns = {"index": "No changes"})
            nonidentical = out[out["_merge"] == "left_only"][colnames]

            # Renamed variable
            out1 = skrub.fuzzy_join(left = nonidentical,
                                    right = df2,
                                    on = "Variables",
                                    suffix = "0",
                                    add_match_info = True,
                                    drop_unmatched = False)
            if (out1.shape[0] > 0):
                same_name = out1[out1["skrub_Joiner_distance"] == 0]
                renamed = out1[(out1["skrub_Joiner_distance"] > 0) & (out1["skrub_Joiner_distance"] < 1)]
                added = out1[out1["skrub_Joiner_distance"] >= 1]

        return sum, identical, same_name, renamed, added
    
    # Same form names
    def detectModificationsInSameForms(self, f):

        out = None

        out1 = pd.merge(left = self._forms,
                        right = f.getForms(),
                        on = "Forms",
                        suffixes = (None, "0"),
                        how = "inner")
        if (out1.shape[0] > 0):
            out = out1
            out2, _, _, _, _ = self.detectIdenticalVariables(f)
            if (out2.shape[0] > 0):
                out = pd.merge(left = out,
                               right = out2,
                               on = "Forms",
                               how = "left")
            else:
                out["No changes"] = 0
            out["Changes"] = out.apply(lambda row: print_n_diff_in_forms(row), axis = 1)

        return out
    
    # Renamed forms
    def detectModificationsInRenamedForms(self, f):

        out1 = skrub.fuzzy_join(left = self._forms,
                                right = f.getForms(),
                                on = "Forms",
                                suffix = "0",
                                add_match_info = True,
                                drop_unmatched = False)
        
        if (out1.shape[0] > 0):
            out1 = out1[(out1["skrub_Joiner_distance"] > 0) & (out1["skrub_Joiner_distance"] < 1)]

        if (out1.shape[0] == 0):
            out1 = None
        else:
            out = out1[["Forms", "N", "Forms0", "N0"]]
            out2, _, _, _, _ = self.detectIdenticalVariables(f)
            if (out2.shape[0] > 0):
                out = pd.merge(left = out,
                               right = out2,
                               on = "Forms",
                               how = "left")
                out["No changes"] = out["No changes"].fillna(0).astype("int")
            else:
                out["No changes"] = 0
            out["Changes"] = out.apply(lambda row: print_n_diff_in_forms(row), axis = 1)

        """
        if out is not None:
            tmp = self._vars.copy(deep=True)
            tmp = tmp[tmp["Form Name"].notnull()]
            out = skrub.fuzzy_join(out[["row", "name", "label"]],
                                   tmp[["index", "name", self._label]],
                                   left_on='label',
                                   right_on=self._label,
                                   how='left',
                                   match_score=0,
                                   return_score=True)
            out = out[["row",
                       "name_x",
                      "label",
                      "name_y",
                      self._label,
                      "matching_score"]] \
                      .rename(columns = {"name_x": "name",
                                         "name_y": "name_of_closest_lbl",
                                         self._label: "closest_lbl"}) \
                      .fillna("") \
                      .reset_index(drop=True)
        """

        return out
    
    def detectDeletedVariables(self, f):

        out = pd.merge(left = self._vars.rename(columns = {self._label: "label"}),
                       right = f.getVariables().rename(columns = {f.getMainLabel(): "label"}),
                       on = "name",
                       how = 'outer')
        out = out[out["type_x"].notnull() & out["type_y"].isnull()]
        out = out.reset_index(drop = True)
        out = out[["index_x",
                   "name",
                   "type_x",
                   "label_x",
                   "group_id_x",
                   "group_lbl_x"]] \
                   .rename(columns = {"index_x": "row",
                                       "type_x": "type",
                                       "label_x": "label"}) \
                   .astype({'row':'int'})
        if (out.shape[0] == 0):
            out = None

        if out is not None:
            tmp = f.getVariables().copy(deep=True)
            tmp = tmp[tmp[f.getMainLabel()].notnull()]
            out = skrub.fuzzy_join(out[["row", "name", "label"]],
                                   tmp[["index", "name", f.getMainLabel()]],
                                   left_on='label',
                                   right_on=f.getMainLabel(),
                                   how='left',
                                   match_score=0,
                                   return_score=True)
            out = out[["row",
                       "name_x",
                       "label",
                       "name_y",
                       f.getMainLabel(),
                       "matching_score"]] \
                        .rename(columns = {"name_x": "name",
                                           "name_y": "name_of_closest_lbl",
                                           f.getMainLabel(): "closest_lbl"}) \
                        .fillna("") \
                        .reset_index(drop=True)

        return out
    
    def detectModifiedLabels(self, f):

        out = pd.merge(left = self._vars.rename(columns = {self._label: "label"}),
                       right = f.getVariables().rename(columns = {f.getMainLabel(): "label"}),
                       on = "name",
                       how = 'inner')
        out["edit_distance"] = out.apply(lambda row: get_normalized_edit_distance(s1 = row["label_x"], s2 = row["label_y"]), axis = 1)

        # Major modifications
        major = out[(out["label_x"].notnull()) & (out["edit_distance"] > 0.2)]
        major = major.reset_index(drop = True)
        major = major[["name",
                       "index_x",
                       "label_x",
                       "index_y",
                       "label_y"]] \
                        .rename(columns = {"index_x": "row1",
                                           "index_y": "row2",
                                           "label_x": "label1",
                                           "label_y": "label2"}) \
                        .astype({'row1':'int', 'row2':'int'})
        if (major.shape[0] == 0):
            major = None
        
        # Minor modifications
        minor = out[(out["label_x"].notnull()) & (out["edit_distance"] > 0) & (out["edit_distance"] <= 0.2)]
        minor = minor.reset_index(drop = True)
        minor = minor[["name",
                       "index_x",
                       "label_x",
                       "index_y",
                       "label_y"]] \
                        .rename(columns = {"index_x": "row1",
                                           "index_y": "row2",
                                           "label_x": "label1",
                                           "label_y": "label2"}) \
                        .astype({'row1':'int', 'row2':'int'})
        if (minor.shape[0] == 0):
            minor = None

        return major, minor
    
    def detectModifiedTypes(self, f):

        out = pd.merge(left = self._vars.rename(columns = {self._label: "label"}),
                       right = f.getVariables().rename(columns = {f.getMainLabel(): "label"}),
                       on = "name",
                       how = 'inner')
        out["edit_distance"] = out.apply(lambda row: get_normalized_edit_distance(s1 = row["type_x"], s2 = row["type_y"]), axis = 1)

        out = out[(out["type_x"].notnull()) & (out["edit_distance"] > 0)]
        out = out.reset_index(drop = True)
        out = out[["name",
                   "index_x",
                   "type_x",
                   "index_y",
                   "type_y"]] \
                   .rename(columns = {"index_x": "row1",
                                      "index_y": "row2",
                                      "type_x": "type1",
                                      "type_y": "type2"}) \
                   .astype({'row1':'int', 'row2':'int'})
        if (out.shape[0] == 0):
            out = None

        return out
    
    def detectSimilarLabels(self, f):
            
        tmp1 = self._vars.copy(deep=True).rename(columns = {self._label: "label"})
        tmp1 = tmp1[tmp1["label"].notnull()]

        tmp2 = f.getVariables().rename(columns = {f.getMainLabel(): "label"})
        tmp2 = tmp2[tmp2["label"].notnull()]

        out = skrub.fuzzy_join(tmp1[["index", "name", "label", "type"]],
                               tmp2[["index", "name", "label", "type"]],
                               on='label',
                               how='left',
                               match_score=0,
                               return_score=True)
        out = out[out["matching_score"] >= 0.6] \
               .rename(columns = {"index_x": "row1",
                                  "index_y": "row2",
                                  "name_x": "name1",
                                  "name_y": "name2",
                                  "type_x": "type1",
                                  "type_y": "type2",
                                  "label_x": "label1",
                                  "label_y": "label2"}) \
              .reset_index(drop=True) \
              .sort_values(by=["matching_score", "row1"],
                           ascending=[False, True])
            
        if (out.shape[0] == 0):
            out = None

        return out
    
    """Please note that the compare, compareVersion, and compareID methods are designed to provide comparison functionality but should be used with care, as they rely on the assumption that certain attributes of the form are set correctly during initialization."""

"""Note: This documentation assumes that the class is used as provided and that any missing implementations or additional functionality required for specific use cases are handled outside of the class definition."""

class ListAnswers:

    def __init__(self,
                 name):
        self._name = name
        
    # Instance Methods
    """This method returns the list name."""
    def getName(self):
        return self._name    

class Answer:

    def __init__(self,
                 list_name):
        self._list_name = list_name
        
    # Instance Methods
    """This method returns the list name."""
    def getListName(self):
        return self._list_name    