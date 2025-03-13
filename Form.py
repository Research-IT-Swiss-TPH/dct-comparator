import pandas as pd
import os
import string
import Levenshtein
import re
import nltk
nltk.download('punkt_tab')
#nltk.download('punkt')
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

"""The Form class is a Python class designed to represent and manipulate information related to XLSForm surveys.
XLSForm is a standard format for authoring surveys in a spreadsheet format, often used in conjunction with data collection tools like ODK."""

class Form:
    
    # Constructor
    """The constructor initializes a new Form object with the provided parameters.

    in_xlsx (string): The path to the XLSForm spreadsheet file from which the survey information is read.
    survey_type (string): A string representing the survey type, which is passed as an argument to the constructor.
    
    Inside the constructor, the provided XLSForm file is read, and relevant survey information is extracted and stored as instance variables:
    
    _id (string): The unique identifier of the form extracted from the XLSForm.
    _label (string): The title or label of the form extracted from the XLSForm.
    _version (tuple): The version information extracted from the XLSForm.
    _default_language (tuple): The default language information extracted from the XLSForm.
    
    It is important to ensure that the Form objects are properly initialized with the required survey information before using these comparison methods."""
    def __init__(self,
                 in_xlsx):

        if not os.path.exists(in_xlsx) or not in_xlsx.endswith('.xlsx'):
            raise FileNotFoundError(f"File {in_xlsx} not found. Cannot create Form object.")

        print(f"📝 Create Form object from {os.path.basename(in_xlsx)}")

        try:
            self._survey_df   = pd.read_excel(in_xlsx, sheet_name="survey").reset_index()
            dims = self._survey_df.shape 
            print("\t - ℹ️ survey sheet with " + str(dims[1]) + " columns and " + str(dims[0]) + " rows")
        except ValueError:
            self._survey_df = None
            print("\t - ⚠️ Sheet 'survey' not found in the file")
        try:
            choices_df  = pd.read_excel(in_xlsx, sheet_name="choices")
            self._choices_df = choices_df[choices_df["list_name"].notnull()]
            dims = self._choices_df.shape 
            print("\t - ℹ️ choices sheet with " + str(dims[1]) + " columns and " + str(dims[0]) + " rows")
        except:
            self._choices_df = None
            print("\t - ℹ️ no choices sheet found")
        try:
            self._settings_df = pd.read_excel(in_xlsx, sheet_name="settings")
            dims = self._settings_df.shape 
            print("\t - ℹ️ settings sheet with " + str(dims[1]) + " columns")
        except:
            self._settings_df = None
            print("\t - ⚠️ no settings sheet found")
        try:
            self._entities_df = pd.read_excel(in_xlsx, sheet_name="entities")
            dims = self._entities_df.shape 
            print("\t - ℹ️ entities sheet with " + str(dims[1]) + " columns")
        except:
            self._entities_df = None
            print("\t - ℹ️ no entities sheet found")
        
        # Extract general form attributes

        # Core form settings
        self._id                      = self._settings_df.get("form_id", [None])[0]
        self._title                   = self._settings_df.get("form_title", [None])[0]
        self._version                 = self._settings_df.get("version", [None])[0]
        self._instance_name           = self._settings_df.get("instance_name", [None])[0]
        self._default_language        = self._settings_df.get("default_language", [None])[0]
        self._style                   = self._settings_df.get("style", [None])[0]
        self._label                   = "::".join(x for x in ["label", self._default_language] if x)

        # Security & submission settings
        self._public_key              = self._settings_df.get("public_key", [None])[0]
        self._auto_send               = self._settings_df.get("auto_send", [None])[0]
        self._auto_delete             = self._settings_df.get("auto_delete", [None])[0]

        # Behavior settings
        self._allow_choice_duplicates = self._settings_df.get("allow_choice_duplicates", [None])[0]

        # Load choice list names
        self._list_names = self._choices_df["list_name"].dropna().unique().tolist() 

        # Load survey columns
        self._survey_columns = self._survey_df.columns.tolist()

        # Load survey group names
        self._group_names = self._survey_df[self._survey_df["type"].isin(["begin group", "begin_group"])]["name"].tolist()

        # Load survey repeat names
        self._repeat_names = self._survey_df[self._survey_df["type"].isin(["begin repeat", "begin_repeat"])]["name"].tolist()

        # Load questions
        questions = self._survey_df[self._survey_df["name"].notnull()]
        questions = questions[questions["type"] != "note"]
        questions = questions[["index",
                               "type",
                               "name",
                               self._label]]
        questions[self._label] = questions.apply(lambda row: process_label(row[self._label]), axis = 1)
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
        self._common_words = find_common_words(self._questions, self._label)

    @property
    def survey(self):
        return self._survey_df

    @property
    def survey_columns(self):
        return self._survey_columns

    @property
    def group_names(self):
        return self._group_names

    @property
    def repeat_names(self):
        return self._repeat_names
    
    @property
    def choices(self):
        return self._choices_df

    @property
    def list_names(self):
        return self._list_names
    
    @property
    def settings(self):
        return self._settings_df

    @property
    def id(self):
        return self._id

    @property
    def title(self):
        return self._title
    
    @property
    def version(self):
        return self._version

    @property
    def default_language(self):
        return self._default_language

    @property
    def style(self):
        return self._style

    @property
    def instance_name(self):
        return self._instance_name
    
    @property
    def public_key(self):
        return self._public_key

    @property
    def auto_send(self):
        return self._auto_send

    @property
    def auto_delete(self):
        return self._auto_delete

    @property
    def allow_choice_duplicates(self):
        return self._allow_choice_duplicates

    @property
    def main_label(self):
        return self._label
    
    @property
    def questions(self):
        return self._questions
    
    """This method is intended to return the parent of the form. However, the parent attribute (_parent) is not set within the class, so this method may not provide the expected functionality without additional implementation."""
    
    def getParent(self):
        return self._parent

    def compareSettings(self, f):

        settings_attributes = [
            ("form_title", self._title, f.title),
            ("form_id", self._id, f.id),
            ("version", self._version, f.version),
            ("instance_name", self._instance_name, f.instance_name),
            ("default_language", self._default_language, f.default_language),
            ("style", self._style, f.style),
            ("public_key", self._public_key, f.public_key),
            ("auto_send", self._auto_send, f.auto_send),
            ("auto_delete", self._auto_delete, f.auto_delete),
            ("allow_choice_duplicates", self._allow_choice_duplicates, f.allow_choice_duplicates)
        ]

        comparisons = []

        for attr, current, ref in settings_attributes:

            if current is None and ref is None:
                continue  # Ignore attributes not used in either form

            if current is None:
                status = "added"
            elif ref is None:
                status = "removed"
            else:
                status = "identical" if current == ref else "modified"

            comparisons.append((attr, status, current, ref))

        return pd.DataFrame(comparisons, columns=["variable", "status", "current", "ref"])

    @staticmethod
    def detectChanges(current, reference):

        """Static method to detect unchanged, added, and removed items in lists."""
        current_set, reference_set = set(current), set(reference)
        unchanged = list(current_set & reference_set)
        added = list(current_set - reference_set)
        removed = list(reference_set - current_set)
        return unchanged, added, removed

    @staticmethod
    def summariseChanges(current, reference):

        """Static method to compare names and return a DataFrame."""
        unchanged, added, removed = Form.detectChanges(current, reference)
        return pd.DataFrame({
            "name": unchanged + added + removed,
            "status": (
                ['unchanged'] * len(unchanged) +
                ['added'] * len(added) +
                ['removed'] * len(removed)
            )
        }).sort_values(by="name", ascending=True)

    # Survey columns

    def compareSurveyColumns(self, f):

        return self.summariseChanges(self._survey_columns, f.survey_columns)

    # Survey group names

    def compareGroupNames(self, f):

        return self.summariseChanges(self._group_names, f.group_names)

    # Survey repeat names

    def compareRepeatNames(self, f):

        return self.summariseChanges(self._repeat_names, f.repeat_names)

    # Choice list names

    def compareListNames(self, f):

        return self.summariseChanges(self._list_names, f.list_names)

    def compareChoices(self, f):

        unchanged_df = self.detectUnchangedChoices(f)
        added_df = self.detectAddedChoices(f)
        removed_df = self.detectDeletedChoices(f)

        out = pd.concat([unchanged_df, added_df, removed_df], join = "inner") \
            .sort_values(by=["list_name", "name"], ascending=[True, True], key = lambda x: x.str.lower())
        
        return out

    def detectUnchangedChoices(self, f):

        out = pd.merge(left = self._choices_df.rename(columns = {self._label: "label"}),
                       right = f.choices.rename(columns = {f.main_label: "label"}),
                       on = ["list_name", "name"],
                       how = 'outer')
        out = out[out["label_x"].notnull() & out["label_y"].notnull()]

        if (out.shape[0] == 0):
            out = None
        else:
            out = out.reset_index(drop = True)
            out["status"] = "unchanged"
            out = out[["list_name", "name", "label_x", "status", "label_y"]] \
                .rename(columns={'label_x': 'label'})
        
        return out

    def detectAddedChoices(self, f):

        list_name_df = self.compareListNames(f).rename(columns={'name': 'list_name'})
        list_name_df.loc[list_name_df['status'] == 'added', 'status'] = 'list_name_added'
        list_name_df.loc[list_name_df['status'] == 'unchanged', 'status'] = 'added'

        out = pd.merge(left = self._choices_df.rename(columns = {self._label: "label"}),
                       right = f.choices.rename(columns = {f.main_label: "label"}),
                       on = ["list_name", "name"],
                       how = 'outer')
        out = out[out["label_x"].notnull() & out["label_y"].isnull()]

        if (out.shape[0] == 0):
            out = None
        else:
            out = out.reset_index(drop = True)

            # Different flag if the list_name has actually been added
            out = out[["list_name", "name", "label_x"]] \
                .merge(list_name_df[['list_name', 'status']], on='list_name', how='left') \
                .rename(columns={'label_x': 'label'})
        
        return out

    def detectDeletedChoices(self, f):

        list_name_df = self.compareListNames(f).rename(columns={'name': 'list_name'})
        list_name_df.loc[list_name_df['status'] == 'removed', 'status'] = 'list_name_removed'
        list_name_df.loc[list_name_df['status'] == 'unchanged', 'status'] = 'removed'

        out = pd.merge(left = self._choices_df.rename(columns = {self._label: "label"}),
                       right = f.choices.rename(columns = {f.main_label: "label"}),
                       on = ["list_name", "name"],
                       how = 'outer')
        out = out[out["label_x"].isnull() & out["label_y"].notnull()]
        
        if (out.shape[0] == 0):
            out = None
        else:
            out = out.reset_index(drop = True)

            # Different flag if the list_name has actually been removed
            out = out[["list_name", "name", "label_y"]] \
                .merge(list_name_df[['list_name', 'status']], on='list_name', how='left') \
                .rename(columns={'label_y': 'label'})

        return out

    # Questions
    
    def detectAddedQuestions(self, f):

        out = pd.merge(left = self._questions.rename(columns = {self._label: "label"}),
                       right = f.questions.rename(columns = {f.main_label: "label"}),
                       on = "name",
                       how = 'outer')
        out = out[out["type_x"].isnull() & out["type_y"].notnull()]
        out = out.reset_index(drop = True)
        out = out[["index_y",
                   "name",
                   "type_y",
                   "label_y"]] \
                    .rename(columns = {"index_y": "row",
                                       "type_y": "type",
                                       "label_y": "label"}) \
                    .astype({'row':'int'})

        if (out.shape[0] == 0):
            out = None

        if out is not None:
            tmp = self._questions.copy(deep=True)
            tmp = tmp[tmp[self._label].notnull()]
            out = skrub.fuzzy_join(out[["row", "name", "label"]],
                                   tmp[["index", "name", self._label]],
                                   left_on='label',
                                   right_on=self._label,
                                   drop_unmatched = False,
                                   add_match_info = True)
            """ 
            print (out)
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
    
    def detectDeletedQuestions(self, f):

        out = pd.merge(left = self._questions.rename(columns = {self._label: "label"}),
                       right = f.questions.rename(columns = {f.main_label: "label"}),
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

        # if out is not None:
        #     tmp = f.questions.copy(deep=True)
        #     tmp = tmp[tmp[f.main_label].notnull()]
        #     out = skrub.fuzzy_join(out[["row", "name", "label"]],
        #                            tmp[["index", "name", f.main_label]],
        #                            left_on='label',
        #                            right_on=f.main_label,
        #                            how='left',
        #                            match_score=0,
        #                            return_score=True)
        #     out = out[["row",
        #                "name_x",
        #                "label",
        #                "name_y",
        #                f.main_label,
        #                "matching_score"]] \
        #                 .rename(columns = {"name_x": "name",
        #                                    "name_y": "name_of_closest_lbl",
        #                                    f.main_label: "closest_lbl"}) \
        #                 .fillna("") \
        #                 .reset_index(drop=True)

        if out is None:
            out = pd.DataFrame()
            
        return out
    
    def detectModifiedLabels(self, f):

        out = pd.merge(left = self._questions.rename(columns = {self._label: "label"}),
                       right = f.questions.rename(columns = {f.main_label: "label"}),
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

        out = pd.merge(left = self._questions.rename(columns = {self._label: "label"}),
                       right = f.questions.rename(columns = {f.main_label: "label"}),
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
            
        tmp1 = self._questions.copy(deep=True).rename(columns = {self._label: "label"})
        tmp1 = tmp1[tmp1["label"].notnull()]

        tmp2 = f.questions.rename(columns = {f.main_label: "label"})
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