# Data Collection Tool (DCT) comparator

## Overview

Data collection tools often require regular updates to a master version as well as sometimes additionally localized adaptations to meet specific regional or local needs. However, tracking changes across different master (and child) versions is a complex and time-consuming process. To simplify this, **DCT comparator** is a Python project designed to facilitate the analysis and comparison of XLSForm data collection tools, such as the WHO verbal autopsy, which is implemented in many countries.

The solution includes the development of a Python class designed to represents an XLSForm and provides class methods for 1-to-1 comparisons of ODK forms from a functional perspective. A step-by-step Jupyter Notebook is also available to demonstrate how to use the class for comparing two forms. The workflow generates an Excel file with multiple tabs, providing a detailed comparison of XLSForms with functional differences across various components using color scales. 

## Form class features

The Form class represents an XLSForm object and provides various methods to interact with and compare 1-to-1 forms. 

Key features of the Form class include:

* **Initialization**: initialize a Form object by providing the path to the XLSForm spreadsheet file.
* **Retrieve form general information**: access form-related information such as the form's unique identifier, title, version, default language, and survey type.
* **Retrieve questions**: obtain a dataframe containing the survey questions, including attributes like question type, label, and group information.

FormComparator
* **Comparison**: compare 2 Form objects to detect differences in form ID, version, and default language. Additionally, identify added, deleted, modified questions, and similar labels between two forms. Return an excel summary of the detected differences.

A Juypter notebook **extract_info_from_xlsforms.ipynb** is available to demonstrate how the class can be used.

## Dependencies

The project requires **Python 3.13.2** to work and relies in particular on the following Python libraries:

* pandas 2.2.3
* Levenshtein 0.26.1
* nltk 3.9.1
* skrub 0.5.1

Make sure to install these dependencies before using this code.

A file `requirements.txt` is also available.

## Installation

To set up the environment and install all required dependencies, follow these steps:

1. Clone the repository in a local copy on your computer:

```bash
git clone https://github.com/Research-IT-Swiss-TPH/odk_xlsform_management
cd <repository_folder>
```

[How to clone using the webbrowser](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)

2. Create a virtual environment (recommended), for instance with conda in Anaconda prompt:

```bash
conda create -n formcompareenv python=3.13.2
conda activate formcompareenv
```

3. Install dependencies using the requirements.txt file:

```bash
pip install -r requirements.txt
```

If you get an error prompring you to modify pip, run the following modified command instead:

```bash
python -m pip install -r requirements.txt
```

After installation, you should be ready to run the code.

## Usage

After installing the dependencies, you can use the form comparison tool via a Jupyter Notebook or a Python script. 

### Extract and manipulate XLSForm information

Below is an example of how to use the tool to extract information from XLSForms

```python
import os
import Form as form

# Set the root path where your XLSForm files are stored
root = "data"  # or any path to your XLSForms

# Define file paths
f2016_xlsx = os.path.join(root, "WHOVA2016_v1_5_3_XLS_form_for_ODK.xlsx")

f = form.Form(f2016_xlsx)
f.groups
```

### Compare XLSForms

Below is an example of how to use the tool to compare two XLSForm files:

Prepare your XLSForm files and place them in a known directory (e.g., a data/ folder).

* A reference form (e.g., WHOVA2016_v1_5_3_XLS_form_for_ODK.xlsx)
* A current form (e.g., WHOVA2022_XLS_form_for_ODK.xlsx)

Example code snippet

```python
import os
import FormComparator as comp

# Set the root path where your XLSForm files are stored
root = "data"  # or any path to your XLSForms

# Define file paths
f2016_xlsx = os.path.join(root, "WHOVA2016_v1_5_3_XLS_form_for_ODK.xlsx")
f2022_xlsx = os.path.join(root, "WHOVA2022_XLS_form_for_ODK.xlsx")

# Run the comparison
comparison = comp.FormComparator(
    cur_xlsx=f2022_xlsx,
    ref_xlsx=f2016_xlsx,
    output_dir="outputs"  # directory where results will be saved
)
```
The tool will generate output files (e.g., reports or comparison results) in the specified output_dir.

⚠️ Changes from lowercase to uppercase in labels are not considered as changes.

## Screenshots

![image](https://github.com/user-attachments/assets/6d76c627-229d-470a-a7d2-360a6c2f3365)

![image](https://github.com/user-attachments/assets/321798c5-53e6-461d-96e4-0cfea05d4a4f)

![image](https://github.com/user-attachments/assets/b87cb3e5-9544-4228-b1e0-f2ee5a8a2626)

## Development

If you want to contribute, follow these steps:

* Fork the repository;
* Create a feature branch based on the develop branch;
* Write clean and well-documented code;
* Commit and push your changes;
* Open a pull request

## Licensing

The project is open-sourced, with all code shared on GitHub under an MIT license to promote accessibility and collaboration.

## Changelog

Version | Description
------- | --------------------
v1.0.0  | First release
