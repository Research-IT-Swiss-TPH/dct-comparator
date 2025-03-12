import Form as form
import pandas as pd
import os

class FormComparator:

    def __init__(self, cur_xlsx, ref_xlsx, output_dir = ".", output_xlsx="comparison_results.xlsx"):

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

        cur_form = form.Form(cur_xlsx)
        ref_form = form.Form(ref_xlsx)

        print ("📝 Compare forms and store results in " + self._output_path)

        self._settings_df                                          = cur_form.compareSettings(ref_form)
        self._survey_columns_df                                    = cur_form.compareSurveyColumns(ref_form)
        self._group_names_df                                       = cur_form.compareGroupNames(ref_form)
        self._repeat_names_df                                      = cur_form.compareRepeatNames(ref_form)
        self._list_name_df                                         = cur_form.compareListNames(ref_form)
        self._added_choices_df                                     = cur_form.detectAddedChoices(ref_form)
        self._deleted_choices_df                                   = cur_form.detectDeletedChoices(ref_form)
        self._added_questions_df                                   = cur_form.detectAddedQuestions(ref_form)
        self._deleted_questions_df                                 = cur_form.detectDeletedQuestions(ref_form)
        self._major_mod_questions_df, self._minor_mod_questions_df = cur_form.detectModifiedLabels(ref_form)

        # Generate summary DataFrame
        self._generic_df = pd.DataFrame({
            "Comparison Type": [
                '=HYPERLINK("#settings!A1", "Settings")',
                '=HYPERLINK("#survey_columns!A1", "Survey columns")',
                '=HYPERLINK("#survey_group_names!A1", "Survey group names")',
                "Survey repeat names",
                "Survey questions",
                "Choice list names",
                "Choice answers"],
             "Identical" : [
                len(self._settings_df[self._settings_df["status"] == "identical"]),
                len(self._survey_columns_df[self._survey_columns_df["status"] == "unchanged"]),
                len(self._group_names_df[self._group_names_df["status"] == "unchanged"]),
                len(self._repeat_names_df[self._repeat_names_df["status"] == "unchanged"]),
                "",
                len(self._list_name_df[self._list_name_df["status"] == "unchanged"]),
                ""],
            "Added" : [
                len(self._settings_df[self._settings_df["status"] == "added"]),
                len(self._survey_columns_df[self._survey_columns_df["status"] == "added"]),
                len(self._group_names_df[self._group_names_df["status"] == "added"]),
                len(self._repeat_names_df[self._repeat_names_df["status"] == "added"]),
                len(self._added_questions_df),
                len(self._list_name_df[self._list_name_df["status"] == "added"]),
                len(self._added_choices_df)],
            "Deleted": [
                len(self._settings_df[self._settings_df["status"] == "removed"]),
                len(self._survey_columns_df[self._survey_columns_df["status"] == "removed"]),
                len(self._group_names_df[self._group_names_df["status"] == "removed"]),
                len(self._repeat_names_df[self._repeat_names_df["status"] == "removed"]),
                len(self._deleted_questions_df),
                len(self._list_name_df[self._list_name_df["status"] == "removed"]),
                len(self._deleted_choices_df)],
            "Modified": [
                len(self._settings_df[self._settings_df["status"] == "modified"]), 
                "",
                "",
                "",
                len(self._major_mod_questions_df),
                "",
                ""]
        })
        self._generic_df["Total"] = self._generic_df[["Identical", "Added", "Deleted", "Modified"]] \
            .apply(lambda col: pd.to_numeric(col, errors='coerce').fillna(0).astype(int)).sum(axis=1)

        # List of sheets and corresponding DataFrame
        sds = [
            ("overview", self._generic_df),
            ("settings", self._settings_df),
            ("survey_columns", self._survey_columns_df),
            ("survey_group_names", self._group_names_df),
            ("survey_repeat_names", self._repeat_names_df),
            ("choice_list_names", self._list_name_df),
            ("added_choices", self._added_choices_df),
            ("deleted_choices", self._deleted_choices_df),
            ("added_questions", self._added_questions_df),
            ("deleted_questions", self._deleted_questions_df),
            ("modified_questions", self._major_mod_questions_df)
        ]

        sds_color = [
            ("settings", self._settings_df),
            ("survey_columns", self._survey_columns_df),
            ("survey_group_names", self._group_names_df),
            ("choice_list_names", self._list_name_df)
        ]

        choices_color = "#C6EFCE"
        survey_color = "#1F4E79"
        slbls_color = [
            ("overview", "#FFEB9C"),
            ("settings", "#FFEB9C"),
            ("survey_columns", survey_color),
            ("survey_group_names", survey_color),
            ("survey_repeat_names", survey_color),
            ("choice_list_names", choices_color),
            ("added_choices", choices_color),
            ("deleted_choices", choices_color),
            ("added_questions", survey_color),
            ("deleted_questions", survey_color),
            ("modified_questions", survey_color)
        ]

        # Write output file

        with pd.ExcelWriter(self._output_path, engine="xlsxwriter") as writer:

            # Define formatting styles
            workbook = writer.book
            green_format = workbook.add_format({
                "bg_color": "#C6EFCE",
                "font_color": "#006100"})  # Green
            red_format = workbook.add_format({
                "bg_color": "#FFC7CE",
                "font_color": "#9C0006"})  # Red
            orange_format = workbook.add_format({
                "bg_color": "#FFEB9C",
                "font_color": "#9C5700"})  # Orange
            hyperlink_format = workbook.add_format({
                "font_color": "blue",
                "underline": 1
            })

            for csn, df in sds:
                df.to_excel(writer, sheet_name = csn, index=False)
                worksheet = writer.sheets[csn]
                for idx, col in enumerate(df.columns):
                    # Find the maximum length of the column's content (including the header)
                    max_length = max(df[col].astype(str).map(len).max(), len(col))
                    # Set the column width to the max length, adding a little padding
                    worksheet.set_column(idx, idx, max_length + 2)

            # Apply color formatting
            for sheet_name, df in sds_color:
                worksheet = writer.sheets[sheet_name]
                worksheet = apply_color_format(worksheet, df, green_format, red_format, orange_format)

            # Apply sheet label background color formatting
            for sheet_name, ccolor in slbls_color:
                worksheet = writer.sheets[sheet_name]
                worksheet.set_tab_color(ccolor)

            for row in range(1, len(self._generic_df) + 1):
                cell_value = str(self._generic_df.iloc[row - 1, 0])  
                if cell_value.startswith('=HYPERLINK('):
                    writer.sheets["overview"].write_formula(row, 0, cell_value, hyperlink_format)

    def getOutputRelativePath(self):

        return self._output_path

def apply_color_format(worksheet, df, green_format, red_format, orange_format):

    for row in range(1, len(df) + 1):  # Skip header row
        status = df.iloc[row - 1, 1]
        if status == "added":
            worksheet.set_row(row, None, green_format)
        elif status == "removed":
            worksheet.set_row(row, None, red_format)
        elif status == "modified":
            worksheet.set_row(row, None, orange_format)
    return worksheet