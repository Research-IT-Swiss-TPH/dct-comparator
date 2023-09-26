import pandas as pd

import string
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
        s = "".join([char.lower() for char in s if char not in string.punctuation]).strip()
        # Remove stop words
        word_tokens = nltk.tokenize.word_tokenize(s)
        out = " ".join([w for w in word_tokens if not w in stop_words])
    except:
        out = s

    return out

"""The Form class is a Python class designed to represent and manipulate information related to XLSForm surveys. XLSForm is a standard format for authoring surveys in a spreadsheet format, often used in conjunction with data collection tools like ODK (Open Data Kit)."""

class Form:

    # Class Attributes
    """_defaults (Class-level attribute): This dictionary defines default values for certain attributes of the Form class.
    Currently, it includes the key "survey" with a default value of None."""
    _defaults = {
        "survey": None
    }
    
    # Constructor
    """The constructor initializes a new Form object with the provided parameters.

    in_xlsx (string): The path to the XLSForm spreadsheet file from which the survey information is read.
    survey (string): A string representing the survey type, which is passed as an argument to the constructor.
    
    Inside the constructor, the provided XLSForm file is read, and relevant survey information is extracted and stored as instance variables:
    
    _id (string): The unique identifier of the form extracted from the XLSForm.
    _label (string): The title or label of the form extracted from the XLSForm.
    _version (tuple): The version information extracted from the XLSForm.
    _default_language (tuple): The default language information extracted from the XLSForm.
    _survey (object): The survey object passed as a parameter to the constructor.
    
    It is important to ensure that the Form objects are properly initialized with the required survey information before using these comparison methods."""
    def __init__(self,
                 in_xlsx,
                 survey):
        
        # Raw data from XLSForm
        self._survey_df   = pd.read_excel(in_xlsx, sheet_name="survey").reset_index()
        self._choices_df  = pd.read_excel(in_xlsx, sheet_name="choices")
        self._settings_df = pd.read_excel(in_xlsx, sheet_name="settings")
        
        # General form attributes
        self._id               = self._settings_df.at[0, "form_id"]
        self._title            = self._settings_df.at[0, "form_title"]
        self._version          = self._settings_df.at[0, "version"]
        self._default_language = self._settings_df.at[0, "default_language"]
        self._survey           = survey

        # Load questions
        questions = self._survey_df[self._survey_df["name"].notnull()]
        questions = questions[questions["type"] != "note"]
        questions = questions[["index",
                               "type",
                               "name",
                               "label::English (en)"]]
        questions["label::English (en)"] = questions.apply(lambda row: process_label(row["label::English (en)"]), axis = 1)
        questions = questions.assign(group_id = "",
                                     group_lbl = "")
        group_ids = [0]
        for index, row in questions.iterrows():
            if row["type"] == "begin_group":
                group_ids.append(row["name"]) # Append the name to the list 'g'
            elif row["type"] == "end_group":
                if len(group_ids) > 1:
                    group_ids = group_ids[:-1]
            else:
                questions.loc[index, "group_id"] = group_ids[-1]
        questions = questions[(questions["type"] != "begin_group") & (questions["type"] != "end_group")]
        self._questions = questions.reset_index(drop=True)

        # Common words
        self._common_words = find_common_words(self._questions, "label::English (en)")

    # Instance Methods

    def getSurvey(self):

        return self._survey_df
    
    def getChoices(self):

        return self._choices_df
    
    def getSettings(self):

        return self._settings_df

    """This method returns the unique identifier of the form."""

    def getID(self):

        return self._id

    """This method returns the title of the form."""

    def getTitle(self):

        return self._title
    
    """This method returns the version information of the form."""

    def getVersion(self):

        return self._version
    
    """This method returns the default language information of the form."""

    def getDefaultLanguage(self):

        return self._default_language
    
    """This method returns the survey type associated with the form."""

    def getSurvey(self):

        return self._survey
    
    def getQuestions(self):

        return self._questions
    
    def getCommonWords(self):

        return self._common_words
    
    """This method is intended to return the parent of the form. However, the parent attribute (_parent) is not set within the class, so this method may not provide the expected functionality without additional implementation."""
    
    def getParent(self):

        return self._parent
    
    """This method takes another Form object (form) as an argument and compares various attributes of the current form with the attributes of the provided form.
    It returns a formatted string containing comparison results."""
    def compare(self, f):

        out1 = self.compareID(f)
        out2 = self.compareVersion(f)
        out3 = self.compareDefaultLanguage(f)
        out = "{}\n{}\n{}".format(out1, out2, out3)
        return out
    
    """This method compares the version attribute of the current form with the version attribute of the provided form. It returns a string indicating whether the versions are identical or different."""
    def compareVersion(self, f):

        cver = f.getVersion()
        out = ""
        if self._version != cver:
            out = "Versions are different: {} and {}".format(self._version, cver)
        else:
            out = "Version is identical: {}".format(self._version)
        return out
    
    """This method compares the unique identifier attribute of the current form with the identifier attribute of the provided form. It returns a string indicating whether the form IDs are identical or different."""
    def compareID(self, f):

        cid = f.getID()
        out = ""
        if self._id != cid:
            out = "Form IDs are different: {} and {}".format(self._id, cid)
        else:
            out = "Form ID is identical: {}".format(self._id)
        return out
    
    def compareDefaultLanguage(self, f):

        cdl = f.getDefaultLanguage()
        out = ""
        if self._default_language != cdl:
            out = "Default languages are different: {} and {}".format(self._default_language, cdl)
        else:
            out = "Default language is identical: {}".format(self._default_language)
        return out
    
    def detectAddedQuestions(self, f):

        out = pd.merge(left = self._questions,
                       right = f.getQuestions(),
                       on = "name",
                       how = 'outer')
        out = out[out["type_x"].isnull() & out["type_y"].notnull()]
        out = out.reset_index(drop = True)
        out = out[["index_y",
                   "name",
                   "type_y",
                   "label::English (en)_y"]] \
                    .rename(columns = {"index_y": "row",
                                       "type_y": "type",
                                       "label::English (en)_y": "label"}) \
                    .astype({'row':'int'})

        if (out.shape[0] == 0):
            out = None

        if out is not None:
            tmp = self._questions.copy(deep=True)
            tmp = tmp[tmp["label::English (en)"].notnull()]
            out = skrub.fuzzy_join(out[["row", "name", "label"]],
                                   tmp[["index", "name", "label::English (en)"]],
                                   left_on='label',
                                   right_on='label::English (en)',
                                   how='left',
                                   match_score=0,
                                   return_score=True)
            out = out[["row",
                       "name_x",
                      "label",
                      "name_y",
                      "label::English (en)",
                      "matching_score"]] \
                      .rename(columns = {"name_x": "name",
                                         "name_y": "name_of_closest_lbl",
                                         "label::English (en)": "closest_lbl"}) \
                      .fillna("") \
                      .reset_index(drop=True)

        return out
    
    def detectDeletedQuestions(self, f):

        out = pd.merge(left = self._questions,
                       right = f.getQuestions(),
                       on = "name",
                       how = 'outer')
        out = out[out["type_x"].notnull() & out["type_y"].isnull()]
        out = out.reset_index(drop = True)
        out = out[["index_x",
                   "name",
                   "type_x",
                   "label::English (en)_x",
                   "group_id_x",
                   "group_lbl_x"]] \
                   .rename(columns = {"index_x": "row",
                                       "type_x": "type",
                                       "label::English (en)_x": "label"}) \
                   .astype({'row':'int'})
        if (out.shape[0] == 0):
            out = None

        if out is not None:
            tmp = f.getQuestions().copy(deep=True)
            tmp = tmp[tmp["label::English (en)"].notnull()]
            out = skrub.fuzzy_join(out[["row", "name", "label"]],
                                   tmp[["index", "name", "label::English (en)"]],
                                   left_on='label',
                                   right_on='label::English (en)',
                                   how='left',
                                   match_score=0,
                                   return_score=True)
            out = out[["row",
                       "name_x",
                       "label",
                       "name_y",
                       "label::English (en)",
                       "matching_score"]] \
                        .rename(columns = {"name_x": "name",
                                           "name_y": "name_of_closest_lbl",
                                           "label::English (en)": "closest_lbl"}) \
                        .fillna("") \
                        .reset_index(drop=True)

        return out
    
    def detectModifiedLabels(self, f):

        out = pd.merge(left = self._questions,
                       right = f.getQuestions(),
                       on = "name",
                       how = 'inner')
        out["edit_distance"] = out.apply(lambda row: get_normalized_edit_distance(s1 = row["label::English (en)_x"], s2 = row["label::English (en)_y"]), axis = 1)

        # Major modifications
        major = out[(out["label::English (en)_x"].notnull()) & (out["edit_distance"] > 0.2)]
        major = major.reset_index(drop = True)
        major = major[["name",
                       "index_x",
                       "label::English (en)_x",
                       "index_y",
                       "label::English (en)_y"]] \
                        .rename(columns = {"index_x": "row1",
                                           "index_y": "row2",
                                           "label::English (en)_x": "label1",
                                           "label::English (en)_y": "label2"}) \
                        .astype({'row1':'int', 'row2':'int'})
        if (major.shape[0] == 0):
            major = None
        
        # Minor modifications
        minor = out[(out["label::English (en)_x"].notnull()) & (out["edit_distance"] > 0) & (out["edit_distance"] <= 0.2)]
        minor = minor.reset_index(drop = True)
        minor = minor[["name",
                       "index_x",
                       "label::English (en)_x",
                       "index_y",
                       "label::English (en)_y"]] \
                        .rename(columns = {"index_x": "row1",
                                           "index_y": "row2",
                                           "label::English (en)_x": "label1",
                                           "label::English (en)_y": "label2"}) \
                        .astype({'row1':'int', 'row2':'int'})
        if (minor.shape[0] == 0):
            minor = None

        return major, minor
    
    def detectModifiedTypes(self, f):

        out = pd.merge(left = self._questions,
                       right = f.getQuestions(),
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
            
        tmp1 = self._questions.copy(deep=True)
        tmp1 = tmp1[tmp1["label::English (en)"].notnull()]

        tmp2 = f.getQuestions()
        tmp2 = tmp2[tmp2["label::English (en)"].notnull()]

        out = skrub.fuzzy_join(tmp1[["index", "name", "label::English (en)", "type"]],
                               tmp2[["index", "name", "label::English (en)", "type"]],
                               on='label::English (en)',
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
                                  "label::English (en)_x": "label1",
                                  "label::English (en)_y": "label2"}) \
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