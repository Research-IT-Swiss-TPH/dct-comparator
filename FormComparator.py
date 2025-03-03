import pandas as pd
import os

class FormComparator:

    def __init__(self, f1, f2, output_dir = ".", output_xlsx="comparison_results.xlsx"):
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

        self._f1 = f1
        self._f2 = f2

        self._settings_df = f1.compareSettings(f2)
        self._added_questions_df = f1.detectAddedQuestions(f2)
        self._deleted_questions_df = f1.detectDeletedQuestions(f2)
        self._major_mod_questions_df, self._minor_mod_questions_df = f1.detectModifiedLabels(f2)

        # Generate summary DataFrame
        self._generic_df = pd.DataFrame({
            "Comparison Type": [
                "Settings",
                "Groups",
                "Repeats",
                "Questions",
                "Choice lists",
                "Choice answers"],
             "Identical" : [
                len(self._settings_df[self._settings_df["Finding"] == "identical"]),
                "",
                "",
                "",
                "",
                ""],
            "Added" : [
                "",
                "",
                "",
                len(self._added_questions_df),
                "",
                ""],
            "Deleted": [
                "",
                "",
                "",
                len(self._deleted_questions_df),
                "",
                ""],
            "Modified": [
                len(self._settings_df[self._settings_df["Finding"] == "different"]), 
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

            self._generic_df.to_excel(writer, sheet_name="overview", index=False)
            self._settings_df.to_excel(writer, sheet_name="settings", index=False)
            self._added_questions_df.to_excel(writer, sheet_name="added_questions", index=False)
            self._deleted_questions_df.to_excel(writer, sheet_name="deleted_questions", index=False)
            self._major_mod_questions_df.to_excel(writer, sheet_name="modified_questions", index=False)

            # Access the current worksheet
            worksheet = writer.sheets["settings"]

            # Apply formatting based on "Finding" column
            for row in range(1, len(self._settings_df) + 1):  # Skip header row
                finding = self._settings_df.iloc[row - 1, 1]  # "Finding" column
                
                # Apply green for "identical", red for "different"
                cell_format = green_format if finding == "identical" else red_format
                
                # Apply color formatting to the entire row (Finding, f1, f2 columns)
                worksheet.set_row(row, None, cell_format)

    def update_excel_with_settings(self, df):
        """
        Updates the Excel file by adding a 'settings' sheet with formatted results.
        Ensures that the existing content is preserved.
        """
        self._settings_df = self._f1.compareSettings(self._f2)

        # Load existing Excel file and append new sheet
        

    def getOutputRelativePath(self):

        return self._output_path