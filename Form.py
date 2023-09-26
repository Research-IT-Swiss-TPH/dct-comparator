import pandas as pd
import Levenshtein
import skrub

def get_normalized_edit_distance(s1, s2):
    try:
        edit_distance = Levenshtein.distance(s1, s2)
        edit_distance /= max(len(s1), len(s2))
    except:
        edit_distance = 1.0
    return edit_distance

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
    
    def addedQuestions(self, f):

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
            out = out[["name_x",
                    "label",
                    "name_y",
                    "label::English (en)",
                    "matching_score"]] \
                    .rename(columns = {"name_x": "name",
                                        "name_y": "name_of_closest_lbl",
                                        "label::English (en)": "closest_lbl"}) \
                    .fillna("")

        return out
    
    def modifiedLabel(self, f):

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
    
    def removedQuestions(self, f):

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
            out = out[["name_x",
                    "label",
                    "name_y",
                    "label::English (en)",
                    "matching_score"]] \
                    .rename(columns = {"name_x": "name",
                                        "name_y": "name_of_closest_lbl",
                                        "label::English (en)": "closest_lbl"}) \
                    .fillna("")

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