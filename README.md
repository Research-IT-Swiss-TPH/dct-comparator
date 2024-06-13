# Data collection tool comparator

## Overview

**DCT comparator** is a Python project designed to facilitate the analysis and comparison of XLSForm and REDCap data collection tools. This project provides a set of Python classes to extract, process, and compare information from XLSForms and REDCap data dictionaries.

## Features

### Form Class

The Form class represents an XLSForm survey and provides various methods to interact with and analyze survey data. 

Key features of the Form class include:

* Initialization: Initialize a Form object by providing the path to the XLSForm spreadsheet file and a survey type.
* Retrieve Survey Information: Access survey-related information such as the form's unique identifier, title, version, default language, and survey type.
* Retrieve Questions: Obtain a DataFrame containing the survey questions, including attributes like question type, label, and group information.
* Comparison: Compare two Form objects to detect differences in form ID, version, and default language. Additionally, identify added, deleted, modified questions, and similar labels between two forms.

* Dependencies

The project requires Python 3.10 to work and relies on the following Python libraries:

* pandas
* Levenshtein
* re
* nltk
* skrub

Make sure to install these dependencies before using the code.
