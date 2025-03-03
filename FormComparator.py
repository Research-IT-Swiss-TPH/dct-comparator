import pandas as pd
import os

class FormComparator:

    def __init__(self, cur_form, ref_form, output_dir = ".", output_xlsx="comparison_results.xlsx"):

        """
        Initializes the XLSComparator with a name and an optional XLSX filename.

        This method sets up the necessary variables for performing the comparison
        between the current form and the reference form, and specifies the output 
        directory and output XLSX filename for storing the results.

        :param cur_form: The current form to be compared (can be a DataFrame, file, etc.).
        :param ref_form: The reference form to compare against (can be a DataFrame, file, etc.).
        :param output_dir: Directory where the comparison results will be saved. Defaults to the current directory ("./").
        :param output_xlsx: Filename for the output XLSX file containing comparison results. Defaults to "comparison_results.xlsx".
        """

        if output_dir != ".":
            os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists
            self._output_path = os.path.join(output_dir, output_xlsx)
        else:
            self._output_path = output_xlsx
        self._comparisons = {}  # Dictionary to store comparison results

        self._cur_form = cur_form
        self._ref_form = ref_form

        self._settings_df = cur_form.compareSettings(ref_form)
        self._survey_columns_df = cur_form.compareSurveyColumns(ref_form)
        self._group_names_df = cur_form.compareGroupNames(ref_form)
        self._list_name_df = cur_form.compareListNames(ref_form)
        self._added_questions_df = cur_form.detectAddedQuestions(ref_form)
        self._deleted_questions_df = cur_form.detectDeletedQuestions(ref_form)
        self._major_mod_questions_df, self._minor_mod_questions_df = cur_form.detectModifiedLabels(ref_form)

        # Generate summary DataFrame
        self._generic_df = pd.DataFrame({
            "Comparison Type": [
                "Settings",
                "Survey columns",
                "Survey group names",
                "Survey repeats",
                "Survey questions",
                "Choice list names",
                "Choice answers"],
             "Identical" : [
                len(self._settings_df[self._settings_df["status"] == "identical"]),
                len(self._survey_columns_df[self._survey_columns_df["status"] == "unchanged"]),
                len(self._group_names_df[self._group_names_df["status"] == "unchanged"]),
                "",
                "",
                len(self._list_name_df[self._list_name_df["status"] == "unchanged"]),
                ""],
            "Added" : [
                "",
                len(self._survey_columns_df[self._survey_columns_df["status"] == "added"]),
                len(self._group_names_df[self._group_names_df["status"] == "added"]),
                "",
                len(self._added_questions_df),
                len(self._list_name_df[self._list_name_df["status"] == "added"]),
                ""],
            "Deleted": [
                "",
                len(self._survey_columns_df[self._survey_columns_df["status"] == "removed"]),
                len(self._group_names_df[self._group_names_df["status"] == "removed"]),
                "",
                len(self._deleted_questions_df),
                len(self._list_name_df[self._list_name_df["status"] == "removed"]),
                ""],
            "Modified": [
                len(self._settings_df[self._settings_df["status"] == "different"]), 
                "",
                "",
                "",
                len(self._major_mod_questions_df),
                "",
                ""]
        })

        sds = [
            ("overview", self._generic_df),
            ("settings", self._settings_df),
            ("survey_columns", self._survey_columns_df),
            ("survey_group_names", self._group_names_df),
            ("choice_list_names", self._list_name_df),
            ("added_questions", self._added_questions_df),
            ("deleted_questions", self._deleted_questions_df),
            ("modified_questions", self._major_mod_questions_df)
        ]

        sds_color = [
            ("survey_columns", self._survey_columns_df),
            ("survey_group_names", self._group_names_df),
            ("choice_list_names", self._list_name_df)
        ]

        with pd.ExcelWriter(self._output_path, engine="xlsxwriter") as writer:

            # Define formatting styles
            workbook = writer.book
            green_format = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})  # Green
            red_format = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})  # Red
            orange_format = workbook.add_format({"bg_color": "#FFEB9C", "font_color": "#9C5700"})  # Orange

            for csn, df in sds:
                df.to_excel(writer, sheet_name = csn, index=False)

            worksheet = writer.sheets["settings"]
            for row in range(1, len(self._settings_df) + 1):  # Skip header row
                status = self._settings_df.iloc[row - 1, 1] 
                cell_format = green_format if status == "identical" else orange_format
                worksheet.set_row(row, None, cell_format)

            # Apply color formatting
            for sheet_name, df in sds_color:
                worksheet = writer.sheets[sheet_name]
                worksheet = apply_color_format(worksheet, df, green_format, red_format)

    def getOutputRelativePath(self):

        return self._output_path

def apply_color_format(worksheet, df, green_format, red_format):

    for row in range(1, len(df) + 1):  # Skip header row
        status = df.iloc[row - 1, 1]
        if status == "added":
            worksheet.set_row(row, None, green_format)
        elif status == "removed":
            worksheet.set_row(row, None, red_format)
    return worksheet