"""The Form class is a Python class designed to represent and manipulate information related to XLSForm surveys. XLSForm is a standard format for authoring surveys in a spreadsheet format, often used in conjunction with data collection tools like ODK (Open Data Kit)."""

class Form:
    _defaults = {
        "survey": None
    }
    
    """Constructor"""
    def __init__(self,
                 in_xlsx,
                 survey):
        
        survey_df, choices_df, settings_df = read_xlsform(in_xlsx)
        
        self._id               = settings_df.loc[0]["form_id"]
        self._title            = settings_df.loc[0]["form_title"]
        self._version          = settings_df.loc[0]["version"],
        self._default_language = settings_df.loc[0]["default_language"],
        self._survey           = survey

    # Instance Methods

    """This method returns the unique identifier of the form."""
    def getID(self):
        return self._id

    """This method returns the title of the form."""
    def getTitle(self):
        return self._title
    
    """This method returns the version information of the form."""
    def getVersion(self):
        return self._version
    
    def getDefaultLanguage(self):
        return self._default_language
    
    def getSurvey(self):
        return self._survey
    
    # Parent of the form
    def getParent(self):
        return self._parent
    
    # Compare
    def compare(self, form):
        out1 = self.compareVersion(form)
        out2 = self.compareID(form)
        out = "{}\n{}".format(out1, out2)
        return out
    
    # Compare version
    def compareVersion(self, form):
        clbl = form.getLabel()
        out = ""
        if self._label != clbl:
            out = "Versions are different: {} and {}".format(self._version, clbl)
        else:
            out = "Version is identical: {}".format(self._version)
        return out
    
    # Compare ID
    def compareID(self, form):
        cid = form.getID()
        out = ""
        if self._id != cid:
            out = "Form IDs are different: {} and {}".format(self._id, cid)
        else:
            out = "Form ID is identical: {}".format(self._id)
        return out
    
Class Attributes

    _defaults (Class-level attribute): This dictionary defines default values for certain attributes of the Form class. Currently, it includes the key "survey" with a default value of None.


__init__(self, in_xlsx, survey)

The constructor initializes a new Form object with the provided parameters.

    in_xlsx (string): The path to the XLSForm spreadsheet file from which the survey information is read.
    survey (object): An object representing the survey, which is passed as an argument to the constructor.

Inside the constructor, the provided XLSForm file is read, and relevant survey information is extracted and stored as instance variables:

    _id (string): The unique identifier of the form extracted from the XLSForm.
    _label (string): The title or label of the form extracted from the XLSForm.
    _version (tuple): The version information extracted from the XLSForm.
    _default_language (tuple): The default language information extracted from the XLSForm.
    _survey (object): The survey object passed as a parameter to the constructor.




getDefaultLanguage(self)

This method returns the default language information of the form.
getSurvey(self)

This method returns the survey object associated with the form.
getParent(self)

This method is intended to return the parent of the form. However, the parent attribute (_parent) is not set within the class, so this method may not provide the expected functionality without additional implementation.
compare(self, form)

This method takes another Form object (form) as an argument and compares various attributes of the current form with the attributes of the provided form. It returns a formatted string containing comparison results.
compareVersion(self, form)

This method compares the version attribute of the current form with the version attribute of the provided form. It returns a string indicating whether the versions are identical or different.
compareID(self, form)

This method compares the unique identifier attribute of the current form with the identifier attribute of the provided form. It returns a string indicating whether the form IDs are identical or different.

Please note that the compare, compareVersion, and compareID methods are designed to provide comparison functionality but should be used with care, as they rely on the assumption that certain attributes of the form are set correctly during initialization.

It's important to ensure that the Form objects are properly initialized with the required survey information before using these comparison methods.

Note: This documentation assumes that the class is used as provided and that any missing implementations or additional functionality required for specific use cases are handled outside of the class definition.