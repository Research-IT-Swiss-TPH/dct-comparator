import pandas as pd
import os

class FormComparator:

    def __init__(self, cur_form, ref_form, output_dir = ".", output_xlsx="comparison_results.xlsx"):
        """
        Initializes the XLSComparator with a name and an optional XLSX filename.
        
        :param output_xlsx: Filename for exporting comparison results.
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

        with pd.ExcelWriter(self._output_path, engine="xlsxwriter") as writer:

            # Define formatting styles
            workbook = writer.book
            green_format = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})  # Green
            red_format = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})  # Red
            orange_format = workbook.add_format({"bg_color": "#FFEB9C", "font_color": "#9C5700"})  # Orange

            self._generic_df.to_excel(writer, sheet_name="overview", index=False)
            self._settings_df.to_excel(writer, sheet_name="settings", index=False)
            self._survey_columns_df.to_excel(writer, sheet_name="survey_columns", index=False)
            self._group_names_df.to_excel(writer, sheet_name="group_names", index=False)
            self._list_name_df.to_excel(writer, sheet_name="list_names", index=False)
            self._added_questions_df.to_excel(writer, sheet_name="added_questions", index=False)
            self._deleted_questions_df.to_excel(writer, sheet_name="deleted_questions", index=False)
            self._major_mod_questions_df.to_excel(writer, sheet_name="modified_questions", index=False)

            worksheet = writer.sheets["settings"]
            for row in range(1, len(self._settings_df) + 1):  # Skip header row
                status = self._settings_df.iloc[row - 1, 1] 
                cell_format = green_format if status == "identical" else orange_format
                worksheet.set_row(row, None, cell_format)

            worksheet = writer.sheets["survey_columns"]
            worksheet = apply_color_format(worksheet, self._survey_columns_df, green_format, red_format)

            worksheet = writer.sheets["group_names"]
            worksheet = apply_color_format(worksheet, self._group_names_df, green_format, red_format)

            worksheet = writer.sheets["list_names"]
            worksheet = apply_color_format(worksheet, self._list_name_df, green_format, red_format)

    def update_excel_with_settings(self, df):
        """
        Updates the Excel file by adding a 'settings' sheet with formatted results.
        Ensures that the existing content is preserved.
        """
        self._settings_df = self._cur_form.compareSettings(self._ref_form)

        # Load existing Excel file and append new sheet
        

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