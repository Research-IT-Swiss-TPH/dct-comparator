# Data collection tool comparator

## Overview

**DCT comparator** is a Python project designed to facilitate the analysis and comparison of XLSForm and REDCap data collection tools. This project provides a set of Python classes to extract, process, and compare information from XLSForms and REDCap data dictionaries.

## Form class features

The Form class represents an XLSForm survey and provides various methods to interact with and compare survey forms. 

Key features of the Form class include:

* Initialization: initialize a Form object by providing the path to the XLSForm spreadsheet file and a survey type.
* Retrieve Survey Information: access survey-related information such as the form's unique identifier, title, version, default language, and survey type.
* Retrieve Questions: obtain a DataFrame containing the survey questions, including attributes like question type, label, and group information.
* Comparison: compare two Form objects to detect differences in form ID, version, and default language. Additionally, identify added, deleted, modified questions, and similar labels between two forms.

# DataDic class features

The DataDic class represents an REDCap data dictionary and provides various methods to interact with and compare REDcap data dictionaries.

Key features of the Form class include:

* Initialization: initialize a DataDic object by providing the path to the CSV data dictionary and a dictionary type.
* Comparison: compare two DataDic objects to identify added, deleted, modified questions, and similar labels between two forms.

## Dependencies

The project requires Python 3.10 to work and relies on the following Python libraries:

* pandas
* Levenshtein
* re
* nltk
* skrub

Make sure to install these dependencies before using this code.
