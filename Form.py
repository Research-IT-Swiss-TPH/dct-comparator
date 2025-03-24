import pandas as pd
import numpy as np
import os
import string
import Levenshtein
import re
import nltk
from collections import OrderedDict
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
            self._survey_df = pd.read_excel(in_xlsx, sheet_name="survey").reset_index()
            self._survey_df = self._survey_df[self._survey_df["type"].notnull()]
            dims = self._survey_df.shape
            self._survey_lang_columns = [
                "label",
                "hint", "guidance_hint", 
                "constraint_message", "required_message",
                "image", "audio", "video"]
            print("\t - ℹ️ survey sheet with " + str(dims[1]) + " columns and " + str(dims[0]) + " rows")
        except ValueError:
            self._survey_df = None
            print("\t - ⚠️ Sheet 'survey' not found in the file")
        try:
            choices_df  = pd.read_excel(in_xlsx, sheet_name="choices")
            if "list name" in choices_df.columns and "list_name" not in choices_df.columns:
                choices_df = choices_df.rename(columns={"list name": "list_name"})
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

        # Parse groups in an ordered dictionary
        self._group_od = OrderedDict()
        stack = []
        current = self._group_od
        # Initialize a list to hold questions with their group info
        questions_with_group_info = []
        # Iterate through the survey DataFrame to build the group structure and assign group to questions
        for _, row in self._survey_df.iterrows():

            if row["type"] in ["begin group", "begin_group", "begin repeat", "begin_repeat"]:
                prefix = "repeat____" if "repeat" in row["type"] else "group____"
                group_name = f"{prefix}{row['name']}"
                # Create a new group and add it to the stack
                new_group = OrderedDict()
                current[group_name] = new_group
                stack.append(current)
                current = new_group
            elif row["type"] in ["end group", "end_group", "end repeat", "end_repeat"]:
                # Pop the group from the stack
                current = stack.pop()
            else:
                # For all questions, assign the current group_id
                row1 = row.copy()
                row1["group_id"] = next(iter(stack[-1].keys())).split("____", 1)[1] if stack else None  # Current group in stack
                # Append the question with the group info
                questions_with_group_info.append(row1.to_dict())

        # Convert the group info into a DataFrame
        res, _ = Form.extract_groups(self._group_od)
        self._group_df = pd.DataFrame(res)

        # Load questions
        questions = pd.DataFrame(questions_with_group_info)

        self._notes = questions[questions["type"] == "note"]
        # Define mandatory and optional columns
        mandatory_columns = ["index", "group_id", "type", "name", self._label]
        self._optional_columns = ["relevant", "calculation","required", "choice_filter", "constraint"]

        # Combine for desired columns list
        desired_columns = mandatory_columns + self._optional_columns

        # Check for missing mandatory columns
        missing = [col for col in mandatory_columns if col not in questions.columns]
        if missing:
            raise ValueError(f"Missing mandatory column(s): {missing}")

        # Keep only existing columns (still keeping optional ones only if they exist)
        existing_columns = [col for col in desired_columns if col in questions.columns]
        questions = questions[existing_columns]
        #questions[self._label] = questions.apply(lambda row: process_label(row[self._label]), axis = 1)

        self._questions = questions.reset_index(drop=True)

        # Load choices columns
        self._choices_columns = self._choices_df.columns.tolist()

        # Common words
        self._common_words = find_common_words(self._questions, self._label)

    @property
    def survey(self):
        return self._survey_df

    @property
    def survey_columns(self):
        return self._survey_columns

    @property
    def survey_lang_columns(self):
        return self._survey_lang_columns

    @property
    def group_od(self):
        return self._group_od

    @property
    def groups(self):
        return self._group_df

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

    @property
    def choices_columns(self):
        return self._choices_columns
    
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
                status = "unchanged" if current == ref else "modified"

            comparisons.append((attr, status, current, ref))

        return pd.DataFrame(comparisons, columns=["variable", "status", "current", "ref"])

    @staticmethod
    def extract_groups(d, parent = None, depth = 0, results = None, order = 0, group_id = 0):
        
        if results is None:
            results = []
            
        for i, (key, value) in enumerate(d.items()):

            current_id = group_id  # Assign the current node ID
            # Determine the type based on whether the value is a dictionary
            gtype = 'repeat' if "repeat____" in key else 'group'
            key = key.split("____", 1)[1]

            # Append the current group with depth, parent, and order within parent
            results.append({
                'group_id': current_id,
                'name': key,
                'parent': parent,
                'depth': depth,
                'order': i,
                'type': gtype
            })
            
            # Recur for nested dictionaries
            if isinstance(value, dict):
                _, group_id = Form.extract_groups(value, parent = key, depth = depth + 1, results = results, group_id = group_id + 1)
            else:
                group_id += 1
        
        return results, group_id

    @staticmethod
    def detectChanges(current, reference):

        """Static method to detect unchanged, added, and removed items in lists."""
        current_set, reference_set = set(current), set(reference)
        unchanged = list(current_set & reference_set)
        added = list(current_set - reference_set)
        removed = list(reference_set - current_set)
        
        return unchanged, added, removed

    @staticmethod
    def summariseChanges(current, reference, modified = []):

        """Static method to compare names and return a DataFrame."""
        unchanged, added, removed = Form.detectChanges(current, reference)
        return pd.DataFrame({
            "name": unchanged + added + removed + modified,
            "status": (
                ['unchanged'] * len(unchanged) +
                ['added'] * len(added) +
                ['removed'] * len(removed) +
                ['modified'] * len(modified)
            )
        })#.sort_values(by="name", ascending=True)

    @staticmethod
    def get_normalized_edit_distance(s1, s2):

        """Compute normalized edit distance (Levenshtein distance)."""
        try:
            edit_distance = Levenshtein.distance(s1, s2)
            edit_distance /= max(len(s1), len(s2))
        except:
            edit_distance = 1.0
        return edit_distance

    # Survey columns

    def compareSurveyColumns(self, f):

        """Compare survey columns with custom logic for modified items."""
        unchanged, added, removed = Form.detectChanges(self._survey_columns, f.survey_columns)

         # Detect modified items (based on shared prefix)
        modified = []
        thres = 0.5
        for removed_item in removed[:]:
            if any(word in removed_item for word in self.survey_lang_columns): 
                rsplit = removed_item.split("::")
                for added_item in added[:]:
                        asplit = added_item.split("::")
                        if (rsplit[0] == asplit[0]):
                            if len(rsplit) > 1 and len(asplit) > 1:
                                d = Form.get_normalized_edit_distance(rsplit[1],asplit[1])
                                if d < thres:
                                    modified.append((removed_item, added_item))
                                    removed.remove(removed_item)
                                    added.remove(added_item)
                            break

        if modified == []:
            return pd.DataFrame({
                "name": unchanged + added + removed,
                "status": (
                    ['unchanged'] * len(unchanged) +
                    ['added'] * len(added) +
                    ['removed'] * len(removed)
                )
            }).sort_values(by="name", ascending=True)
        else:
            modified0 = [item[0] for item in modified]
            modified1 = [item[1] for item in modified]
            return pd.DataFrame({
                "name": unchanged + added + removed + modified0,
                "status": (
                    ['unchanged'] * len(unchanged) +
                    ['added'] * len(added) +
                    ['removed'] * len(removed) +
                    ['likely_modified'] * len(modified0)
                ),
                "modified_name": (
                    [''] * (len(unchanged) + len(added) + len(removed)) +
                    modified1
                )
            }).sort_values(by="name", ascending=True)

    # Survey group names

    def compareGroupRepeatNames(self, f):

        unchanged_df = self.detectGroups(f, 'unchanged')
        added_df = self.detectGroups(f, 'added')
        removed_df = self.detectGroups(f, 'removed')

        out = pd.concat([unchanged_df, added_df, removed_df], join = "inner")
        out["group_id"] = out["current_group_id"].fillna(out["reference_group_id"])
        out = out.sort_values(by=["group_id"], ascending=[True])

        return out[["name", "status", "current_type", "current_group_id", "reference_group_id", "current_parent", "reference_parent", "current_depth", "reference_depth", "current_order", "reference_order"]]

    def detectGroups(self, f, status):

        out = pd.merge(left = self._group_df,
                       right = f.groups,
                       on = "name",
                       how = 'outer')

        if status == 'unchanged':
            condition = out["group_id_x"].notnull() & out["group_id_y"].notnull()
        elif status == 'added':
            condition = out["group_id_x"].notnull() & out["group_id_y"].isnull()
        elif status == 'removed':
            condition = out["group_id_x"].isnull() & out["group_id_y"].notnull()
        else:
            raise ValueError("Invalid status provided")

        out = out[condition]

        if out.empty:
            return None

        out = out.reset_index(drop=True)
        out = out[["name", "type_x", "group_id_x", "parent_x", "depth_x", "order_x", "group_id_y", "parent_y", "depth_y", "order_y"]] \
            .rename(columns={
                "type_x": "current_type",
                "group_id_x": "current_group_id",
                "parent_x": "current_parent",
                'depth_x': 'current_depth',
                'order_x': 'current_order',
                "group_id_y": "reference_group_id",
                "parent_y": "reference_parent",
                'depth_y': 'reference_depth',
                'order_y': 'reference_order'
            })

        out["status"] = status
        if status == 'unchanged':
            out.loc[((~pd.isna(out["current_parent"])) & (out["current_parent"] != out["reference_parent"])) | (out["current_depth"] != out["reference_depth"]), "status"] = "modified"

        return out

    # Choice list names

    def compareListNames(self, f):

        return self.summariseChanges(self._list_names, f.list_names)

    def compareChoicesColumns(self, f):

        return self.summariseChanges(self._choices_columns, f.choices_columns)

    def compareChoices(self, f):

        unchanged_df = self.detectUnchangedChoices(f)
        added_df = self.detectAddedChoices(f)
        removed_df = self.detectDeletedChoices(f)

        out = pd.concat([unchanged_df, added_df, removed_df], join = "inner") \
            .sort_values(by=["list_name", "name"], ascending=[True, True], key = lambda x: x.str.lower())

        return out[["list_name", "name", "status", "current_label", "reference_label"]]

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

            out["status"] = out.apply(lambda row: "unchanged" if Form.get_normalized_edit_distance(s1 = row["label_x"], s2 = row["label_y"]) == 0 else "modified_label", axis = 1)
            
            out = out[["list_name", "name", "label_x", "label_y", "status"]] \
                .rename(columns={
                    'label_x': 'current_label',
                    'label_y': 'reference_label'
                    })
        
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
            out = out[["list_name", "name", "label_x", "label_y"]] \
                .merge(list_name_df[['list_name', 'status']], on='list_name', how='left') \
                .rename(columns={
                    'label_x': 'current_label',
                    'label_y': 'reference_label'
                    })
        
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
            out = out[["list_name", "name", "label_x", "label_y"]] \
                .merge(list_name_df[['list_name', 'status']], on='list_name', how='left') \
                .rename(columns={
                    'label_x': 'current_label',
                    'label_y': 'reference_label'
                    })

        return out

    # Questions

    def compareQuestions(self, f):

        unchanged_df = self.detectUnchangedQuestions(f)
        added_df = self.detectAddedQuestions(f)
        removed_df = self.detectDeletedQuestions(f)

        out = pd.concat([unchanged_df, added_df, removed_df], join = "outer") \
            .sort_values(by=["order"], ascending=[True])
        
        # Always-required base columns
        base_columns = ["group_name", "name", "status", "type", "order"]

        # Dynamically gather optional columns from unchanged_df (if it exists)
        optional_prefixes = ["label_mod", "logic_mod", "calc_mod", "required_mod", "filter_mod", "group_mod",
                            "current_label", "reference_label",
                            "current_relevant", "reference_relevant",
                            "current_calculation", "reference_calculation",
                            "current_required", "reference_required",
                            "current_filter", "reference_filter",
                            "reference_group_name"]

        # Extract columns that exist in the DataFrame
        detected_columns = [col for col in optional_prefixes if col in out.columns]

        final_columns = base_columns + detected_columns

        # Filter out any missing columns to avoid KeyErrors
        final_columns = [col for col in final_columns if col in out.columns]

        return out[final_columns]

    def detectUnchangedQuestions(self, f):

        out = pd.merge(left = self._questions.rename(columns = {self._label: "label"}),
                       right = f.questions.rename(columns = {f.main_label: "label"}),
                       on = "name",
                       how = 'outer')
        out = out[out["label_x"].notnull() & out["label_y"].notnull()]

        if (out.shape[0] == 0):
            return None

        # Handle relevant and calculation modifications (consider empty values as equivalent to None)
        def check_modification(val_x, val_y):
            if pd.isna(val_x) and pd.isna(val_y):
                return 0  # Both are empty, no modification
            if pd.isna(val_x) or pd.isna(val_y):
                return 1  # One is empty, the other is not, hence modification
            return int(val_x != val_y)  # Both exist, check for differences

        out = out.reset_index(drop = True)
        out["order"] = out.apply(lambda row: round(np.nanmean([row["index_x"], row["index_y"]]), 1), axis = 1)
        out["label_mod"] = out.apply(lambda row: round(Form.get_normalized_edit_distance(s1 = row["label_x"], s2 = row["label_y"]), 2), axis = 1)
        mod_columns = {
            "logic_mod": ("relevant_x", "relevant_y"),
            "calc_mod": ("calculation_x", "calculation_y"),
            "required_mod": ("required_x", "required_y"),
            "filter_mod": ("choice_filter_x", "choice_filter_y")
        }
        mod_columns = {
            new_col: (col_x, col_y)
            for new_col, (col_x, col_y) in mod_columns.items()
            if col_x in out.columns and col_y in out.columns
        }
        # Apply the check_modification function to each pair
        for new_col, (col_x, col_y) in mod_columns.items():
            out[new_col] = out.apply(lambda row: check_modification(row[col_x], row[col_y]), axis=1)

        # Identify all columns that end with '_mod'
        mod_check_cols = [col for col in out.columns if col.endswith('_mod')]
        # Set status based on whether all mod columns are zero
        out["status"] = out[mod_check_cols].apply(
            lambda row: "unchanged" if all(val == 0 for val in row) else "modified",
            axis=1
        )
        for new_col, (col_x, col_y) in {"group_mod": ("group_id_x", "group_id_y")}.items():
            out[new_col] = out.apply(lambda row: check_modification(row[col_x], row[col_y]), axis=1)
        # Select and rename final output columns
        final_columns = [
            "order", "name", "type_y", "label_x", "label_y", "group_id_x", "group_id_y",
            "relevant_x", "relevant_y", "calculation_x", "calculation_y",
            "required_x", "required_y", "choice_filter_x", "choice_filter_y",
            "status", "label_mod", "logic_mod", "calc_mod", "required_mod", "filter_mod", "group_mod"
        ]
        # Filter to only columns that actually exist
        final_columns = [col for col in final_columns if col in out.columns]
        # Column selection and renaming map
        column_renames = {
            "type_y": "type",
            "label_x": "current_label",
            "label_y": "reference_label",
            "relevant_x": "current_relevant",
            "relevant_y": "reference_relevant",
            "calculation_x": "current_calculation",
            "calculation_y": "reference_calculation",
            "required_x": "current_required",
            "required_y": "reference_required",
            "choice_filter_x": "current_filter",
            "choice_filter_y": "reference_filter",
            "group_id_x": "group_name",
            "group_id_y": "reference_group_name"
        }
        # Filter to only columns that actually exist
        column_renames = {old: new for old, new in column_renames.items() if old in out.columns}
        
        return out[final_columns].rename(columns = column_renames)

    def detectAddedQuestions(self, f):

        out = pd.merge(left = self._questions.rename(columns = {self._label: "label"}),
                       right = f.questions.rename(columns = {f.main_label: "label"}),
                       on = "name",
                       how = 'outer')
        out = out[out["type_x"].notnull() & out["type_y"].isnull()]
        
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

        else:
            out = out.reset_index(drop = True)
            out["order"] = out.apply(lambda row: round(np.nanmean([row["index_x"], row["index_y"]]), 1), axis = 1)
            out = out[[
                "order", "name", "type_y", "label_x", "label_y", "group_id_x",
                "relevant_x", "relevant_y", "calculation_x", "calculation_y"
            ]].rename(columns={
                "type_y": "type",
                'label_x': 'current_label',
                'label_y': 'reference_label',
                "relevant_x": "current_relevant",
                "relevant_y": "reference_relevant",
                "calculation_x": "current_calculation",
                "calculation_y": "reference_calculation",
                'group_id_x': 'group_name'})
            out["status"] = "added"
            out["label_mod"] = 0
            out["logic_mod"] = 0
            out["calc_mod"] = 0
            
        return out
    
    def detectDeletedQuestions(self, f):

        out = pd.merge(left = self._questions.rename(columns = {self._label: "label"}),
                       right = f.questions.rename(columns = {f.main_label: "label"}),
                       on = "name",
                       how = 'outer')
        out = out[out["type_x"].isnull() & out["type_y"].notnull()]

        if (out.shape[0] == 0):
            out = None
        else:
            # tmp = self._questions.copy(deep=True)
            # tmp = tmp[tmp[self._label].notnull()]
            # out = skrub.fuzzy_join(out[["row", "name", "label"]],
            #                        tmp[["index", "name", self._label]],
            #                        left_on='label',
            #                        right_on=self._label,
            #                        drop_unmatched = False,
            #                        add_match_info = True)
            out = out.reset_index(drop = True)
            out["order"] = out.apply(lambda row: round(np.nanmean([row["index_x"], row["index_y"]]), 1), axis = 1)
            out = out[[
                "order", "name", "type_y", "label_x", "label_y", "group_id_x",
                "relevant_x", "relevant_y", "calculation_x", "calculation_y"
            ]].rename(columns={
                "type_y": "type",
                'label_x': 'current_label',
                'label_y': 'reference_label',
                "relevant_x": "current_relevant",
                "relevant_y": "reference_relevant",
                "calculation_x": "current_calculation",
                "calculation_y": "reference_calculation",
                'group_id_x': 'group_name'})
            out["status"] = "removed"
            out["label_mod"] = 0
            out["label_mod"] = 0
            out["logic_mod"] = 0
            out["calc_mod"] = 0

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
    
    def detectModifiedLabels(self, f):

        out = pd.merge(left = self._questions.rename(columns = {self._label: "label"}),
                       right = f.questions.rename(columns = {f.main_label: "label"}),
                       on = "name",
                       how = 'inner')
        out["edit_distance"] = out.apply(lambda row: Form.get_normalized_edit_distance(s1 = row["label_x"], s2 = row["label_y"]), axis = 1)

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
        out["edit_distance"] = out.apply(lambda row: Form.get_normalized_edit_distance(s1 = row["type_x"], s2 = row["type_y"]), axis = 1)

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